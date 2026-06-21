class MiBaseException(Exception):
    def __init__(self, mensaje, **context):
        self.mensaje = mensaje
        self.context = context
        super().__init__(mensaje)

    def __str__(self):
        return self.mensaje
    
    def __repr__(self):
        ctx_lines = "\n".join(
                f"  - {k}={v!r}\n   - type of {k}=({type(v).__name__})"
                for k, v in self.context.items()
            )
    
        return (
            f"{self.__class__.__name__}(\n"
            f"  mensaje={self.mensaje!r}\n"
            f"  context={{\n{ctx_lines}\n  }}\n)"
        )

# --- HTMLPARSER EXCEPTIONS ---
class HTMLParserError(MiBaseException): ...
class SelectorNotFound(HTMLParserError):
    """Exception for errors related to CSS selectors. __repr__ method
    print the items from the variable self.context

    ### Params

    * *mensaje* (str): exception message
    * ***context* (dict): dict with kwargs for context
    
    #### Inheritance:
    Exception > MiBaseException > HTMLParserError > SelectorNotFound
    """
    pass

# --- HTTPCLIENT EXCEPTIONS ---
class HTTPClientError(MiBaseException): ...
class RetryableError(MiBaseException):...

# --- DOWNLOADER EXCEPTIONS ---
class DownloadError(MiBaseException): ...
class EmptyFileError(DownloadError):...
class NotAExcelFile(DownloadError):...
class HTMLInvalidWarning(DownloadError):...

# --- XLS PARSER EXCEPTIONS ---
class XLSParserError(MiBaseException):...
class ReadingExcelError(XLSParserError):...

class PipelineModuleError(MiBaseException): ...