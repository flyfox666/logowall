"""Outbound HTTP fetching with SSRF protection.

Every server-side fetch of a user-supplied URL (image proxy, remote logo
download, logo discovery) goes through `fetch()`, which:
  * only allows http/https,
  * resolves the host and refuses private, loopback, link-local (incl. cloud
    metadata 169.254.169.254), multicast and otherwise non-global addresses,
  * follows redirects manually so every hop is re-checked,
  * streams the body and aborts once `max_bytes` is exceeded.

FETCH_ALLOW_PRIVATE=true disables the address check for intranet deployments.
Residual risk: a hostile DNS server could answer differently between the
check and httpx's own lookup (DNS rebinding); the window is a few ms.
"""
import socket
import asyncio
import ipaddress
import urllib.parse
from typing import Optional

import httpx

from . import config

MAX_REDIRECTS = 5
DEFAULT_UA = 'Mozilla/5.0 (LogoWall)'


class FetchError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


class FetchResult:
    def __init__(self, url: str, status: int, headers: httpx.Headers, content: bytes):
        self.url = url
        self.status_code = status
        self.headers = headers
        self.content = content

    @property
    def content_type(self) -> str:
        return (self.headers.get('content-type') or '').split(';')[0].strip().lower()


def _ip_allowed(ip: ipaddress._BaseAddress) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


def _resolve(host: str, port: int):
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return {info[4][0] for info in infos}


async def check_url(url: str) -> str:
    """Validate scheme + destination address. Returns the normalised URL."""
    parsed = urllib.parse.urlsplit((url or '').strip())
    if parsed.scheme not in ('http', 'https'):
        raise FetchError('Only http/https URLs are allowed')
    host = parsed.hostname
    if not host:
        raise FetchError('URL has no host')
    if parsed.username or parsed.password:
        raise FetchError('Credentials in URLs are not allowed')
    if config.FETCH_ALLOW_PRIVATE:
        return parsed.geturl()
    try:
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    except ValueError:
        raise FetchError('Invalid port')
    try:
        literal = ipaddress.ip_address(host)
        addrs = {str(literal)}
    except ValueError:
        try:
            addrs = await asyncio.get_running_loop().run_in_executor(None, _resolve, host, port)
        except (socket.gaierror, UnicodeError) as e:
            raise FetchError(f'Cannot resolve host: {host} ({e})', 502)
    if not addrs:
        raise FetchError(f'Cannot resolve host: {host}', 502)
    for a in addrs:
        if not _ip_allowed(ipaddress.ip_address(a.split('%')[0])):
            raise FetchError('Destination address is not allowed (private / internal network)', 403)
    return parsed.geturl()


async def fetch(url: str, *, max_bytes: int, timeout: float = 10.0, method: str = 'GET',
                headers: Optional[dict] = None,
                client: Optional[httpx.AsyncClient] = None) -> FetchResult:
    hdrs = {'User-Agent': DEFAULT_UA}
    if headers:
        hdrs.update(headers)
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=timeout, follow_redirects=False)
    try:
        current = url
        for _ in range(MAX_REDIRECTS + 1):
            current = await check_url(current)
            try:
                async with client.stream(method, current, headers=hdrs) as resp:
                    if resp.is_redirect and resp.headers.get('location'):
                        current = urllib.parse.urljoin(current, resp.headers['location'])
                        continue
                    declared = resp.headers.get('content-length')
                    if declared and declared.isdigit() and int(declared) > max_bytes:
                        raise FetchError('Remote file too large', 413)
                    buf = bytearray()
                    if method != 'HEAD':
                        async for chunk in resp.aiter_bytes():
                            buf.extend(chunk)
                            if len(buf) > max_bytes:
                                raise FetchError('Remote file too large', 413)
                    return FetchResult(current, resp.status_code, resp.headers, bytes(buf))
            except httpx.HTTPError as e:
                raise FetchError(f'Fetch failed: {e}', 502)
        raise FetchError('Too many redirects', 502)
    finally:
        if own_client:
            await client.aclose()
