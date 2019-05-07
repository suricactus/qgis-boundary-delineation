# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Its4landAPI
 Query its4land Land Administration Data
                              -------------------
        begin                : 2019-04-14
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Ivan Ivanov suricactus
        email                : ivan.ivanov@suricactus.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from typing import Any, Optional, Dict
from enum import Enum
from urllib.parse import urljoin, quote

from requests import request, exceptions

class ResponseType(Enum):
    json = 1
    text = 2
    html = 3
    stream = 4


Payload = Dict[str, Any]

class Its4landException(Exception):
    def __init__(
        self,
        msg: str = None,
        error: exceptions.RequestException = None,
        url: str = None,
        code: int = None
    ):
        self.msg = msg
        self.code = code
        self.url = url
        self.error = error
        self.count = 0

        if error:
            if isinstance(error, Its4landException):
                self.msg = msg or error.msg
                self.code = code or error.code
                self.url = url or error.url
                self.count = error.count + 1
            elif isinstance(error, exceptions.RequestException):
                self.msg = msg or str(error)
            else:
                self.msg = msg or str(error)

                if 'response' in error:
                    self.code = error.response.code
                    self.url = error.response.url
                else:
                    self.code = code
                    self.url = url
        else:
            self.msg = msg
            self.code = code
            self.url = url

        super().__init__(self.msg)

class Its4landAPI:
    def __init__(self, url: str, api_key: str, response_type: ResponseType = ResponseType.json):
        self.url = url + '/'
        self.api_key = api_key
        self.response_type = response_type
        self.session_token = ''

    def get(self, *argv, **kwargs):
        return self.request('GET', *argv, **kwargs)

    def post(self, *argv, **kwargs):
        return self.request('POST', *argv, **kwargs)

    def request(self,
                method: str,
                data: Optional[Payload],
                encode_as: str = 'form',
                response_type: ResponseType = None,
                files: Dict[str, Any] = None,
                headers: Dict[str, str] = dict(),
                auth_required: bool = True,
                url: str = None):
        url = url or self.url
        response_type = response_type or self.response_type

        assert not auth_required or self.session_token, 'No session token provided'

        try:
            headers['X-Api-Key'] = self.api_key

            if self.session_token:
                headers['X-Session-Token'] = self.session_token

            send_data: Dict[str, Any] = {
                'stream': (response_type == ResponseType.stream),
                'headers': headers,
            }

            if method == 'GET':
                send_data['params'] = data
            else:
                if encode_as == 'json':
                    send_data['json'] = data
                elif encode_as == 'form':
                    send_data['data'] = data
                else:
                    raise Exception(url, 998, 'Unknown encode type: %s' % encode_as)

            if files is not None and len(files):
                send_data['files'] = {}

                for k, v in files.items():
                    try:
                        send_data['files'][k] = open(v, 'rb')
                    except Exception as e:
                        raise Exception(url, 998, 'Unable to open file: %s' % v, e)

            resp = request(method, url, **send_data)

            if resp is not None:
                if resp.ok and resp.content is not None:
                    if response_type == ResponseType.stream:
                        return resp
                    elif response_type == ResponseType.json:
                        return resp.json()
                    elif response_type == ResponseType.html:
                        return resp.content

                    assert False, 'Unrecognized response type'
                else:
                    raise Its4landException(url=resp.url, code=resp.status_code, msg=resp.reason)
            else:
                raise Its4landException(url=url, msg='There is no response, something bad happened')
        except exceptions.RequestException as e:
            raise Its4landException(error=e)
        except Exception as e:
            raise Its4landException(url=url, error=e)

    def login(self, login: str, password: str) -> str:
        # self.session_token = self.post({
        #     'login': login,
        #     'password': password,
        # },
        # auth_required=False,
        # url=urljoin(self.url, 'login'))
        self.session_token = 'SESSION_TOKEN'
        return self.session_token

    def get_projects(self):
        return self.get(None, url=urljoin(self.url, 'projects'))

    def get_validation_sets(self, project_id: str):
        return self.get({
            'Projects': project_id
        }, url=urljoin(self.url, 'WP5ValidationSets'))

    def post_boundaries(self, project_id: str, geojson: str):
        url = urljoin(self.url, 'BoundaryFaceFeatures/%s' % quote(project_id, safe=''))

        return self.post({'geojson': geojson, }, url=url)

    def get_content_item(self, uid: str):
        return self.get({
            'uid': uid
        }, url=urljoin(self.url, 'contentitems'))

    def download_content_item(self, uid: str, filename: str):
        url = urljoin(self.url, 'contentitems/%s' % quote(uid, safe=''))

        return self.download_file(None, url=url, filename=filename)

    def download_file(self, data: Optional[Payload], filename: str, **rest) -> str:
        resp = self.get(data, response_type=ResponseType.stream, **rest)

        with open(filename, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=4096):
                if not chunk:  # filter out keep-alive new chunks
                    pass

                f.write(chunk)

        return filename