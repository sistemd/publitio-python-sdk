import contextlib
import random
import hashlib
import calendar
import abc
import io
import functools
from datetime import datetime

import requests


# TODO Use git.


__all__ = ['PublitioAPI', 'AsyncPublitioAPI']


API_URL = 'https://api.publit.io/v1/'


class UnknownStatusCode(BaseException):

    def __init__(self, status_code):
        super().__init__('API call returned unknown status code {}.'.format(status_code))


def generate_nonce():
    return str(random.randrange(10000000, 99999999))


def current_unix_timestamp():
    return str(calendar.timegm(datetime.utcnow().utctimetuple()))


def status_code_is_known(status_code):
    return 200 <= status_code < 300 \
           or 400 <= status_code <= 406 \
           or status_code in [410, 422, 429, 500, 503]


def check_status_code(status_code):
    if not status_code_is_known(status_code):
        raise UnknownStatusCode(status_code)


def parse_response(response):
    if status_code_is_known(response.status_code):
        return response.json()
    raise UnknownStatusCode


def safe_request(method, *args, **kwargs):
    res = method(*args, **kwargs)
    check_response(res)
    return res.json()


safe_get = functools.partial(safe_request, requests.get)
safe_put = functools.partial(safe_request, requests.put)
safe_post = functools.partial(safe_request, requests.post)
safe_delete = functools.partial(safe_request, requests.delete)


class PublitioAPI:

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret

    def generate_signature(self, timestamp, nonce):
        s = timestamp + nonce + self.secret
        sha1_hash = hashlib.sha1(s.encode())
        digest = sha1_hash.hexdigest()
        return str(digest)

    def api_payload(self):
        timestamp = current_unix_timestamp()
        nonce = generate_nonce()
        signature = self.generate_signature(timestamp, nonce)

        return {
            'api_key': self.key,
            'api_timestamp': timestamp,
            'api_nonce': nonce,
            'api_signature': signature
        }

    def full_payload(self, user_payload):
        result = self.api_payload()
        result.update(user_payload)
        return result

    def api_get(self, path, payload):
        return safe_get(API_URL + path,
                        params=self.full_payload(payload))

    def api_put(self, path, data):
        return safe_put(API_URL + path,
                        params=self.api_payload(),
                        data=data)

    def api_post(self, path, payload, data):
        return safe_post(API_URL + path,
                         params=self.full_payload(payload),
                         files=data)

    def api_delete(self, path):
        return safe_delete(API_URL + path,
                           params=self.api_payload())


    def upload_file(self, file, **params):
        return self.api_post('files/create',
                             payload=params,
                             data={'file': file})

    def list_files(self, **params):
        return self.api_get('files/list', params)

    def show_file(self, file_id):
        return self.api_get('files/show/' + file_id)

    def update_file(self, file_id, **params):
        return self.api_put('files/update/' + file_id, params)

    def delete_file(self, file_id):
        return self.api_delete('files/delete/' + file_id)

    def player_file(self, file_id, **params):
        return self.api_get('files/player/' + file_id, params)


EXAMPLE_FILE_ID = '2P65LMzD'


if __name__ == '__main__':
    from pprint import pprint

    publitio_api = PublitioAPI(key='ktuZkDrpfA3M7t3txAp0',
                               secret='RWnZpAdRa8olrNaDjsZp1Q5VbWgznwy8')

    pprint(publitio_api.upload_file(file=io.open('/home/jimihendrix/index.jpeg', 'rb'), title='Whatever'))
