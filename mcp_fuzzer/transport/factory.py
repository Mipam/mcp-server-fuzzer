from .base import TransportProtocol
from .http import HTTPTransport
from .sse import SSETransport


def create_transport(protocol: str, url: str) -> TransportProtocol:
    if protocol == "http":
        return HTTPTransport(url)
    elif protocol == "sse":
        return SSETransport(url)
    else:
        raise ValueError(f"Unsupported protocol: {protocol}")
