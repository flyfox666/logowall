import asyncio

import httpx
import pytest


@pytest.mark.parametrize('url', [
    'http://127.0.0.1/a.png',
    'http://localhost/a.png',
    'http://169.254.169.254/latest/meta-data/',
    'http://10.0.0.5/a.png',
    'http://192.168.1.1/a.png',
    'http://[::1]/a.png',
    'http://[::ffff:127.0.0.1]/a.png',
    'http://0.0.0.0/a.png',
    'file:///etc/passwd',
    'ftp://example.com/a.png',
    'http://user:pw@example.com/a.png',
])
def test_imgproxy_blocks_internal_and_bad_urls(ctx, url):
    admin = ctx.admin()
    r = ctx.client.get('/api/imgproxy', params={'url': url}, headers=admin)
    assert r.status_code in (400, 403), r.text


def test_logo_fetch_blocks_internal(ctx):
    r = ctx.client.post('/api/logo/fetch', headers=ctx.admin(),
                        data={'url': 'http://169.254.169.254/latest/meta-data/'})
    assert r.status_code == 400
    assert 'not allowed' in r.json()['detail']


def _mock_client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)


@pytest.fixture
def nf(ctx, monkeypatch):
    nf = ctx.mod.safe_fetch.__module__
    import importlib
    mod = importlib.import_module(nf)
    # Pretend every hostname resolves to a public address unless it is "internal.test"
    monkeypatch.setattr(mod, '_resolve', lambda host, port: {'10.1.2.3'} if host == 'internal.test'
                        else {'93.184.216.34'})
    return mod


def test_redirect_to_internal_address_is_blocked(nf):
    def handler(request):
        if request.url.host == 'public.test':
            return httpx.Response(302, headers={'location': 'http://169.254.169.254/'})
        return httpx.Response(200, content=b'secret')

    async def run():
        async with _mock_client(handler) as client:
            await nf.fetch('http://public.test/logo.png', max_bytes=1000, client=client)

    with pytest.raises(nf.FetchError) as e:
        asyncio.run(run())
    assert e.value.status == 403


def test_redirect_to_internal_hostname_is_blocked(nf):
    def handler(request):
        return httpx.Response(301, headers={'location': 'http://internal.test/x'})

    async def run():
        async with _mock_client(handler) as client:
            await nf.fetch('http://public.test/', max_bytes=1000, client=client)

    with pytest.raises(nf.FetchError):
        asyncio.run(run())


def test_public_redirect_is_followed(nf):
    def handler(request):
        if request.url.path == '/old':
            return httpx.Response(302, headers={'location': '/new'})
        return httpx.Response(200, content=b'ok-body')

    async def run():
        async with _mock_client(handler) as client:
            return await nf.fetch('http://public.test/old', max_bytes=1000, client=client)

    res = asyncio.run(run())
    assert res.content == b'ok-body' and res.url.endswith('/new')


def test_body_size_is_capped_while_streaming(nf):
    def handler(request):
        return httpx.Response(200, content=b'x' * 5000)

    async def run():
        async with _mock_client(handler) as client:
            await nf.fetch('http://public.test/big', max_bytes=1000, client=client)

    with pytest.raises(nf.FetchError) as e:
        asyncio.run(run())
    assert e.value.status == 413


def test_redirect_loop_is_bounded(nf):
    def handler(request):
        return httpx.Response(302, headers={'location': '/again'})

    async def run():
        async with _mock_client(handler) as client:
            await nf.fetch('http://public.test/', max_bytes=1000, client=client)

    with pytest.raises(nf.FetchError):
        asyncio.run(run())


def test_allow_private_opt_in(make_ctx):
    c = make_ctx(seed_records=[], FETCH_ALLOW_PRIVATE='true')
    import importlib
    nf = importlib.import_module('logowall.netfetch')
    assert asyncio.run(nf.check_url('http://127.0.0.1/a.png')) == 'http://127.0.0.1/a.png'


def test_domain_from_url_strips_only_www_prefix(ctx):
    f = ctx.mod._domain_from_url
    assert f('https://wework.com/path') == 'wework.com'
    assert f('www.example.com') == 'example.com'
    assert f('') == ''
