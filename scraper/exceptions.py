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


class HTMLParserError(MiBaseException): ...
class HTTPClientError(MiBaseException): ...