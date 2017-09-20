#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2017 University of Dundee & Open Microscopy Environment.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Aleksandra Tarkowska <A(dot)Tarkowska(at)dundee(dot)ac(dot)uk>, 2017
#
# Version: 1.0
#


import logging
import requests

from urlparse import urlparse

logger = logging.getLogger(__name__)


class OmeroRequests(object):

    session = None
    config = {}
    urls = {}

    def __init__(self, session=None):
        if session is None:
            session = requests.Session()
        self.session = session

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.session.close()
        self.config = {}
        self.urls = {}

    def configure(self, domain, server=1):
        self.config = {'domain': domain.rstrip('/'), 'server': server}
        self.urls['index'] = self.prepare_url("/webclient/")
        self.urls['login'] = self.prepare_url("/webclient/login/")

    def prepare_url(self, url, params={}, no_prefix=False):
        if no_prefix:
            params['domain'] = "{0.scheme}://{0.netloc}".format(
                urlparse(self.config['domain']))
        else:
            params['domain'] = self.config['domain']
        url = "{domain}%s" % url
        return url.format(**params)

    def connect(self, token=None, username=None, password=None):
        if token:
            logger.debug("Authenticate using token: %s" % token)
            self.urls['auth'] = self.prepare_url(
                "/webclient/?server={server}&bsession={bsession}",
                {
                    'server': self.config['server'],
                    'bsession': token
                })
            url = self.urls['auth']
        elif username and password:
            logger.debug("Authenticate using username: %s" % username)
            url = self.urls['login']
        else:
            logger.debug("Anonymous session")
            url = self.urls['index']
        response = self.session.get(url)  # todo: https
        if response.status_code != 200:
            response.raise_for_status()

        if username and password:
            csrftoken = self.session.cookies['csrftoken']
            data = {
                'username': username,
                'password': password,
                'server': self.config['server'],
                'noredirect': 1,
                'csrfmiddlewaretoken': csrftoken}
            response = self.session.post(
                self.urls['login'],
                data=data,
                headers=dict(Referer=self.urls['login']))
            if response.status_code != 200:
                response.raise_for_status()

    def exception(self, request, exception):
        logger.error("Problem: {}: {}".format(request.url, exception))

    def async_requests(self, urls):
        import grequests

        rs = (grequests.get(url, session=self.session, stream=False,
                            cookies=self.session.cookies) for url in urls)
        return grequests.imap(rs, exception_handler=self.exception, size=10)
