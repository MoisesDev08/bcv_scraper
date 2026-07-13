import logging
from pathlib import Path

import requests
import requests.exceptions
from fake_useragent import FakeUserAgentError, UserAgent
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from bcv.config import config as cf
from bcv.scraper.exceptions import HTTPClientError, RetryableError

logger = logging.getLogger(__name__)


class HttpClient:
    """
    Client for safe requests. Use fake_useragent (user rotation) and tenacity (retrys)

    ### Notes

    - Use a fallback with only one user agent if fake_useragent fails
    - Retry attemps number is showed in the class attr as RETRY_ATTEMPS, 5 as default.
    !!Be careful if you change it, It's recommended turn on the default manually after change it

    ### Fallback User Agent:

    ```
    ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0"
        )
    ```

    ### Requests Get Headers:

    ```
    headers = {
            "accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,image/avif,"
                "image/webp,image/apng,*/*;q=0.8,"
                "application/signed-exchange;v=b3;q=0.7"
            ),
            "accept-language": "en-US,en;q=0.9,es-MX;q=0.8,es;q=0.7",
            "referer": "https://www.bcv.org.ve/",
            "user-agent": self._get_user_agent() # fake_useragent.UserAgent().random
                                                # or user agent from fallback
        }
    ```

    """

    try:
        UA = UserAgent()

    except (ImportError, ValueError, TypeError, FakeUserAgentError) as e:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"self.ua = UserAgent raised {e}\nUsing self.ua = None that it will call the fallback"
            )

        UA = None

    def __init__(self):
        self.session = requests.Session()

    @staticmethod
    def _fallback_user_agent_helper() -> str:

        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0"
        )
        return ua

    def _get_user_agent(self) -> str:
        try:
            if isinstance(self.UA, UserAgent):
                ua = self.UA.random
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"UA gotten from fake_useragent module:\n{ua}")

                return ua

            ua = self._fallback_user_agent_helper()
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "FakeUserAgent failed, calling to _fallback_user_agent_helper() %s",
                    f"UA gotten:\n{ua}",
                )

            return ua

        except (ImportError, ValueError, TypeError, FakeUserAgentError):
            logger.warning("Error during getting the user agent\nCalling fallback...")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Error Traceback:\n\n", exc_info=True)
            return self._fallback_user_agent_helper()

        except Exception as e:
            raise HTTPClientError(f"Unexpected error: {e}", self_ua=self.UA)

    def _get_headers(self) -> dict[str, str]:

        headers = {
            "accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,image/avif,"
                "image/webp,image/apng,*/*;q=0.8,"
                "application/signed-exchange;v=b3;q=0.7"
            ),
            "accept-language": "en-US,en;q=0.9,es-MX;q=0.8,es;q=0.7",
            "referer": "https://www.bcv.org.ve/",
            "user-agent": self._get_user_agent(),
        }

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Headers gotten:\n{headers}\n")
        return headers

    RETRY_ATTEMPS: int = 5

    @retry(
        retry=retry_if_exception_type(
            (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                RetryableError,
            )
        ),
        stop=stop_after_attempt(RETRY_ATTEMPS),
        wait=wait_exponential_jitter(exp_base=2, max=10),
        after=after_log(logger, logging.DEBUG),
    )
    def fetch(
        self,
        url: str | None = None,
        page: int | None = None,
        stream: bool | None = None,
        head: bool | None = None,
        verify_bcv_cert: bool | Path | None = None,
        params: dict | None = None,
        timeout: int | None = 10,
    ) -> requests.Response:
        """Send the get requests and give the Response obj

        ### Notes:

        - verify_bcv_cert accepts wether bool or Path objects to the cert if given, don't use
        verify_bcv_cert=False if you don't know the risks of do a get request with verify=False
        - Don't use params and page at the same time, page arg creates params={'page': page}
        - verify_bcv_cert as None will use the bcv.pem certify
        - *The headers used for this client have "https://www.bcv.org.ve/" as referer*
        - *If not url given, it is used "https://www.bcv.org.ve/estadisticas/tipo-cambio-de-referencia-smc"*"""

        try:
            url = url if url else cf.URL_WITH_XLS_FILES
            if params and isinstance(page, int):
                raise AttributeError(
                    "Don't use params and page at the same time.\n"
                    "Page it's used to create a params argument and to have both cause fatal errors"
                )
            if not params and isinstance(page, int):
                params = {"page": page}

            response = self._do_request(
                params=params,
                url=url,
                stream=stream,
                head=head,
                verify=verify_bcv_cert,
                timeout=timeout,
            )
            return response

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status is not None and status in (408, 429, 500, 502, 503, 504):
                logger.warning("Error during request, retrying...")
                raise RetryableError(f"Error HTTP: {status}\nReintentando...") from e

            else:
                raise HTTPClientError(
                    f"HTTP error {status}: {e}", url=url, status_code=status
                ) from e

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            raise RetryableError("Error de conexión\nReintentando...") from e

        except AttributeError:
            raise

        except Exception as e:
            raise HTTPClientError(
                f"Unexpected error: {e}",
                params=params,
                url=url,
                stream=stream,
                head=head,
                verify=verify_bcv_cert,
                timeout=timeout,
            ) from e

    def _do_request(
        self,
        url: str,
        params: dict | None = None,
        stream: bool | None = None,
        head: bool | None = None,
        verify: bool | Path | None = None,
        timeout: int | None = None,
    ) -> requests.Response:

        headers = self._get_headers()
        if verify is None:
            verify = cf.CERT_PATH

        if head is True:
            response = self.session.head(
                url=url,
                headers=headers,
                verify=verify,  # type: ignore
                params=params,
                timeout=timeout,
                stream=stream,
            )
        else:
            response = self.session.get(
                url=url,
                headers=headers,
                verify=verify,  # type: ignore
                params=params,
                timeout=timeout,
                stream=stream,
            )

        response.raise_for_status()
        logger.info(f"Fetching Succesfully to: {url}")
        return response
