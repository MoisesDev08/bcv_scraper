import requests
from tenacity import (
    retry, retry_if_exception_type, 
    stop_after_attempt, wait_exponential_jitter,
    after_log
)

from fake_useragent import FakeUserAgentError, UserAgent
from bcv import config as cf
import logging
import requests.exceptions
from exceptions import HTTPClientError
from typing import Any

logger = logging.getLogger(__name__)

class RetryableError(Exception): ...
class HttpClient():

    def __init__(self):
        self.session = requests.Session()
        try:
            self.ua = UserAgent()
        
        except (ImportError, ValueError, TypeError, FakeUserAgentError) as e:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"self.ua = UserAgent raised {e}\nUsing self.ua = None that it will call the fallback")
            
            self.ua = None

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

            if isinstance(self.ua, UserAgent):
                ua = self.ua.random
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"UA gotten from fake_useragent module:\n{ua}")

                return ua

            ua = self._fallback_user_agent_helper()
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "FakeUserAgent failed, calling to _fallback_user_agent_helper() %s", 
                    f"UA gotten:\n{ua}"
                    )

            return ua
        
        except (ImportError, ValueError, TypeError, FakeUserAgentError) as e:
            
            logger.warning("Error during getting the user agent\nCalling fallback...")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Error Traceback:\n\n", exc_info=True)
            return self._fallback_user_agent_helper()
        
        except Exception as e: raise HTTPClientError(f"Unexpected error: {e}")

    def _get_headers(self) -> dict[str, str]: 

        try:
            headers = {
                "accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,image/avif,"
                    "image/webp,image/apng,*/*;q=0.8,"
                    "application/signed-exchange;v=b3;q=0.7"
                ),
                "accept-language": "en-US,en;q=0.9,es-MX;q=0.8,es;q=0.7",
                "referer": "https://www.bcv.org.ve/",
                "user-agent": self._get_user_agent()  
            }

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Headers gotten:\n{headers}")
            return headers
        except Exception as e:

            raise HTTPClientError(f"Unexpected error getting headers for the request: {e}")


    @retry(
            retry=retry_if_exception_type((
                requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout,
                RetryableError)),
            stop=stop_after_attempt(5),
            wait=wait_exponential_jitter(exp_base=2, max=10),
            after=after_log(logger, logging.DEBUG)
    )
    def fetch(self, page: int = None) -> requests.Response: 
        """Send the get requests and give the Response obj
        
        - Note: *The headers used for this client have "https://www.bcv.org.ve/" as referer*"""

        try:
            response = self._do_request(page)
            return response
        
        except requests.exceptions.HTTPError as e:

            status = e.response.status_code if e.response else None
            if status != None and status in (408, 429, 500, 502, 503, 504): 
                logger.warning("Error during request, retrying...")
                raise RetryableError from e
            
            else:

                raise HTTPClientError(
                    f"HTTP error {status}: {e}",
                    url=cf.URL_WITH_XLS_FILES,
                    status_code=status
                    ) from e
        
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            raise RetryableError from e
        
        except Exception as e:
            raise HTTPClientError(f"Unexpected error: {e}") from e

    def _do_request(self, page: int | None) -> requests.Response:

        headers = self._get_headers()
        params = {"page": page} if page is not None else None
        response = self.session.get(
                url=cf.URL_WITH_XLS_FILES,
                headers=headers,
                verify=cf.CERT_PATH,
                params=params,
                timeout=10
            )

        response.raise_for_status()
        logger.info("Fetching Succesfully!")
        return response