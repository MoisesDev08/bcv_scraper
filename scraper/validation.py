from pathlib import Path
from requests import Response
import os, logging
from urllib.parse import urlparse
from bcv.scraper.exceptions import DownloadError, EmptyFileError, HTMLInvalidWarning
from typing import Literal, Any

logger = logging.getLogger(__name__)



def validate_downloads_dir(path: str | Path, mkdir: bool = False):
    """
    Validate a given Path object or a string to directory and checks out if It has write permission
    
    - ### **Raise:**

        *   FileNotFoundError: if not path.exists() and mkdir=False
        *   TypeError.
        *   NotADirectoryError.
        *   PermissionError
    
    - ### **Return:**

        - **path** *(Path)*: validated path
    """
    
    if not isinstance(path, (str, Path)):
        raise TypeError(f"str | Path object expected, gotten: {type(path).__name__}")
    
    if isinstance(path, str): 
        path = Path(path)

    if not path.exists():
        if mkdir == True: path.mkdir(exist_ok=True)
        if mkdir == False: raise FileNotFoundError(f"Unexistent rute given:\n{path}")
    
    if not path.is_dir():
        raise NotADirectoryError(f"The given rute is not a directory\n{path}")
    
    if not os.access(path, os.W_OK):
        raise PermissionError(f"Not write permission for directory:\n{path}")
    
    return path

def validate_url(url: str):
    """
    Validate a given url, only with parser, doesn't make a HEAD request
    
    - ### **Raise:**

        *   TypeError.
        *   DownloadError
    
    - ### **Return:**

        - **url** *(str)*: validated url
    """

    if not isinstance(url, str): 
        raise TypeError(f"URL is not a string, gotten: {type(url)}")
    url = url.strip()
    parsed_url = urlparse(url)

    if not parsed_url.scheme in ("http", "https") or parsed_url.netloc == "":
        raise DownloadError(f"Invalid url given: {url}")
            
    return parsed_url.geturl()

def _validate_xls_r_head_helper(headers_response: Response | dict):

    if isinstance(headers_response, Response):
        headers = headers_response.headers

    elif isinstance(headers_response, dict):
        headers = headers_response

    else:
        raise TypeError(f"Response | dict object expected, {type(headers_response).__name__} gotten")
    
    ctype = headers.get("content-type", None)
    if not ctype: 
        logger.warning("No content type detected")
    
    length = headers.get("content-length", 1)
    try: 
        if int(length) <= 1: raise EmptyFileError
    except TypeError:
        if logger.isEnabledFor(logging.DEBUG): 
            logger.debug(
                "TypeError detectando content-length en headers\n%s", 
                f"lenght=({length})"
                )

    ext = None
    if ctype == "application/vnd.ms-excel": ext = ".xls"
    elif ctype == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ext = ".xlsx"

    elif "ms-excel" in ctype:
        return ".xls"

    elif "spreadsheetml" in ctype:
        return ".xlsx"

    return ext

def _validate_xls_r_get_helper(get_response: Response):
    if get_response.status_code >= 400:
        raise DownloadError(f"HTTP Error: {get_response.status_code}")
    
    data = get_response.content
    if len(data) < 10:
        raise EmptyFileError

    if data.startswith(b"\xD0\xCF\x11\xE0"): return ".xls"

    elif data.startswith(b"PK"): return ".xlsx"

    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Binary firm: {data[:40]}")

        raise DownloadError("Unsupported binary firm")

ExcelExt = Literal[".xls", ".xlsx"]
def validate_excel_extension(
        r_get: Response = None, 
        r_head: Response | dict = None
        ) -> tuple[ExcelExt | None, ExcelExt | None]:
    """Return excel extension based on the Response object and, or the headers

    **Nota**: *ExcelExt is an alias for the typing expression **Literal['.xls', '.xlsx']***
    
    - ### *Raise:*
    
    * DownloadError
    * EmptyFileError
    * TypeError
    * AttributeError
    """

    if r_head and r_get:

        headers_ext = _validate_xls_r_head_helper(r_head)
        get_ext = _validate_xls_r_get_helper(r_get)
        return (get_ext, headers_ext)

    elif not r_head and r_get: 

        get_ext = _validate_xls_r_get_helper(r_get)
        headers_ext = _validate_xls_r_head_helper(r_get.headers)
        return (get_ext, headers_ext)

    elif not r_get and r_head:

        logger.warning("No get response gotten for excel validation")
        get_ext = None

        headers_ext = _validate_xls_r_head_helper(r_head)
        return (get_ext, headers_ext)

    else: 
        raise AttributeError(f"At least one argument expected, 0 given")

def validate_html(response: Response) -> bool:
        """
        Validate either if It is or is not a HTML file from its response of the get request

        **Notes:**
            *   Analyze the Content-Type in the Response.headers to check out its MIME type
            *   Also, analyze the Response.content to verify if it has the characteristics tags
            from a HTML file, such as; **<html**, **<body**...
            *   If after this actions the html doesn't look like a valid one it is used lxml to
            parsing the Response.content, if doesn't raise any error, the html must be valid

        ### **Raise:**

            -   *HTMLInvalidWarning:* only if the lxml parser raise any exception
        """

        valid_html = False
        headers = response.headers
        ctype = headers.get("content-type", None)

        if ctype:
            if "html" in ctype:
                valid_html = True
                return valid_html
        
        if any(
            tag in response.content[:1000].lower() for tag in
            (b"<html", b"<body", b"<head", b"<!doctype html")
        ):
            valid_html = True
            return valid_html
        
        if valid_html is False:
            try:
                from lxml import html
                from lxml.etree import ParserError, XMLSyntaxError
                html.fromstring(response.content)
            
            except (ParserError, XMLSyntaxError) as e:
                raise HTMLInvalidWarning from e
        
        return valid_html