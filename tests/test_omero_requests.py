import pytest
import logging

from orequests import OmeroRequests
import requests_mock


logging.basicConfig(filename='test_orequests.log', level=logging.DEBUG)


class TestRequests(object):

    @requests_mock.Mocker()
    def test_basic(self, m):
        with OmeroRequests() as oreq:
            oreq.configure("mock://test.com/")
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

    @requests_mock.Mocker()
    def test_bad_basic(self, m):
        with pytest.raises(requests_mock.exceptions.NoMockAddress) as excinfo:
            with OmeroRequests() as oreq:
                oreq.configure("mock://test.com/")
                oreq.connect()
            assert 'No mock address: GET mock://test.comwebclient/' \
                in str(excinfo.value)

    @requests_mock.Mocker()
    def test_basic_async(self, m):
        with OmeroRequests() as oreq:
            oreq.configure("mock://test.com/")
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
                oreq.configure("mock://test.com/")
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
