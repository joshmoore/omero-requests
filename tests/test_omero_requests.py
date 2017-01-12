import os
import sys
import pytest
import logging

from orequests import OmeroRequests
import requests_mock
from requests_mock.exceptions import NoMockAddress

# Logging
LOGDIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'log').replace('\\', '/')
if not os.path.isdir(LOGDIR):
    try:
        os.makedirs(LOGDIR)
    except Exception, x:
        exctype, value = sys.exc_info()[:2]
        raise exctype(value)
logging.basicConfig(
    filename=os.path.join(LOGDIR, 'test_orequests.log').replace('\\', '/'),
    level=logging.DEBUG
)


class TestRequests(object):

    @requests_mock.Mocker()
    def test_basic(self, m):
        with OmeroRequests() as oreq:
            oreq.configure("mock://test.com")
            m.get(oreq.urls['index'], text='index')
            m.get(oreq.urls['login'], text='login')
            oreq.connect()

            thumb_url = oreq.prepare_url(
                "/webgateway/render_thumbnail/12345/")
            m.get(thumb_url, content='12345')
            assert oreq.session.get(thumb_url).content == "12345"
            assert oreq.session.get(thumb_url).status_code == 200

            thumb_url = oreq.prepare_url("/webgateway/render_thumbnail/0000/")
            m.get(thumb_url, status_code=404)
            assert oreq.session.get(thumb_url).status_code == 404

    @pytest.mark.parametrize('params', (
        {'kwargs': {},
            'error': 'GET mock://test.com/webclient/'},
        {'kwargs': {'token': '12345'},
            'error': ('GET mock://test.com/webclient/'
                      '?server=1&bsession=12345')},
        {'kwargs': {'username': 'foo', 'password': 'bar'},
            'error': 'GET mock://test.com/webclient/login/'},
    ))
    def test_urls(self, params):
        with requests_mock.Mocker():
            with pytest.raises(NoMockAddress) as excinfo:
                with OmeroRequests() as oreq:
                    oreq.configure("mock://test.com")
                    oreq.connect(**params['kwargs'])
            assert str(excinfo.value).endswith(params['error'])

    @pytest.mark.parametrize('params', (
        {'domain': "mock://test.com"},
        {'domain': "mock://test.com/"},
        {'domain': "mock://test.com:1234"},
        {'domain': "mock://test.com:1234/"},
        {'domain': "mock://test.com/prefix"},
        {'domain': "mock://test.com/prefix/"},
        {'domain': "mock://test.com:1234/prefix"},
        {'domain': "mock://test.com:1234/prefix/"},
    ))
    def test_domain(self, params):
        with requests_mock.Mocker():
            with pytest.raises(NoMockAddress) as excinfo:
                with OmeroRequests() as oreq:
                    oreq.configure(params['domain'])
                    oreq.connect()
            error = ("%s/webclient/" % params['domain'].rstrip("/"))
            assert str(excinfo.value).endswith(error)

    @requests_mock.Mocker()
    def test_basic_async(self, m):
        with OmeroRequests() as oreq:
            oreq.configure("mock://test.com")
            m.get(oreq.urls['index'], text='index')
            m.get(oreq.urls['login'], text='login')
            oreq.connect()

            plateurls = []
            for i in xrange(0, 10):
                thumb_url = oreq.prepare_url(
                    "/webgateway/render_thumbnail/%i/" % i)
                m.get(thumb_url, content='thumbnail_%i' % i)
                plateurls.append(thumb_url)
            oreq.async_requests(urls=plateurls)

    @pytest.mark.parametrize('token', ("12345",))
    def test_token(self, token):
        with requests_mock.Mocker() as m:
            with OmeroRequests() as oreq:
                oreq.configure("mock://test.com")
                m.get(oreq.urls['index'], text='index')
                m.get(oreq.urls['login'], text='login')

                auth = oreq.prepare_url(
                    "?server={server}&bsession={bsession}",
                    {
                        'server': oreq.config['server'],
                        'bsession': token
                    })

                m.get(auth, text='auth')
                oreq.connect(token=token)
