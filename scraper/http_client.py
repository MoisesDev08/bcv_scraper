import requests
from tenacity import (
    retry, retry_if_exception_type, 
    stop_after_delay, wait_exponential_jitter,
    after_log
)
import fake_useragent
import config as cf
import logging
import requests.exceptions


logger = logging.getLogger(__name__)
session = requests.session()
user_agent = fake_useragent.UserAgent()

class RetryableError(Exception): pass


def _fallback_user_agent_helper():
    try:
        logger.debug("Calling to _fallback_user_agent_helper()")
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0"
        )
        logger.debug(f"Using fallback's user_agent:\n{ua}")
        
        return ua
    
    except:
        logger.error("Error during call to _fallback_user_agent_helper", exc_info=True)
        raise

def _get_user_agent():
    try:

        logger.debug("Calling to _get_user_agent()")
        ua = user_agent.random

        logger.debug(f"User-Agent gotten:\n{ua}")
        return ua
    
    except:

        logger.debug("Error during call to _get_user_agent()", exc_info=True)
        return _fallback_user_agent_helper()

         
def _get_headers(): 

    try:
        logger.debug("Calling to _get_headers()")
        headers = {
            "accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,image/avif,"
                "image/webp,image/apng,*/*;q=0.8,"
                "application/signed-exchange;v=b3;q=0.7"
            ),
            "accept-language": "en-US,en;q=0.9,es-MX;q=0.8,es;q=0.7",
            "referer": "https://www.bcv.org.ve/",
            "user-agent": _get_user_agent()  
        }

        logger.debug(f"Headers gotten:\n{headers}")
        return headers
    except:
        logger.error("Error during call to _get_headers()", exc_info=True)
        raise


@retry(
        retry=retry_if_exception_type((
            ConnectionError, 
            TimeoutError,
            RetryableError)),
        stop=stop_after_delay(30),
        wait=wait_exponential_jitter(exp_base=2, max=10),
        after=after_log(logger, logging.INFO)
)
def fetch(page: int):
    try:

        logger.debug("Calling to fetch()")
        response = session.get(
                url=cf.URL_WITH_XLS_FILES,
                headers=_get_headers(),
                verify=cf.CERT_PATH,
                params={"page": page}
            )
        
        response.raise_for_status()
        logger.debug("Fetching Succesfully!")
        return response.text
    
    except Exception as e:
        
        logger.info(f"Error during call to fetch():\n{e}")
        status = getattr(response, 'status_code', None)
        if status in (429, 500): raise RetryableError
        else: 
            logger.error("Error during call to fetch()", exc_info=True)
            raise e

cf.setup_logging_config()
print(fetch(3)[:2000])