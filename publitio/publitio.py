import random
import hashlib
import calendar
import functools
import os.path
from datetime import datetime

import requests


__all__ = ['UnknownStatusCode', 'TransformationFailed', 'PublitioAPI']


class UnknownStatusCode(BaseException):

    def __init__(self, status_code):
        super().__init__('API call returned unknown status code {}.'.format(status_code))


class TransformationFailed(BaseException):

    def __init__(self, reason):
        super().__init__('File transformation failed. Response: ' + reason)


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


def rest_request(method, *args, **kwargs):
    res = method(*args, **kwargs)
    check_status_code(res.status_code)
    return res.json()


def filename_without_extension(filename):
    return os.path.splitext(filename)[0]


def replace_extension(filename, new_extension):
    return '{}.{}'.format(filename_without_extension(filename),
                          new_extension)


rest_get = functools.partial(rest_request, requests.get)
rest_put = functools.partial(rest_request, requests.put)
rest_post = functools.partial(rest_request, requests.post)
rest_delete = functools.partial(rest_request, requests.delete)


class PublitioAPI:
    API_URL = 'https://api.publit.io/v1/'
    MEDIA_URL = 'https://media.publit.io/'

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

    def api_get(self, path, payload=None):
        return rest_get(PublitioAPI.API_URL + path,
                        params=self.full_payload(payload or {}))

    def api_put(self, path, data=None):
        return rest_put(PublitioAPI.API_URL + path,
                        params=self.api_payload(),
                        data=data or {})

    def api_post(self, path, payload=None, data=None):
        payload = payload or {}
        data = data or {}

        return rest_post(PublitioAPI.API_URL + path,
                         params=self.full_payload(payload),
                         files=data)

    def api_delete(self, path):
        return rest_delete(PublitioAPI.API_URL + path,
                           params=self.api_payload())


    def create_file(self, file, **params):
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

    def get_file_player(self, file_id, **params):
        return self.api_get('files/player/' + file_id, params)

    def create_version(self, file_id, **params):
        return self.api_post('files/versions/create/' + file_id,
                             payload=params)

    def list_versions(self, file_id, **params):
        return self.api_get('files/versions/list/' + file_id,
                            payload=params)

    def show_version(self, version_id):
        return self.api_get('files/versions/show/' + version_id)

    def delete_version(self, version_id):
        return self.api_delete('files/versions/delete/' + version_id)

    def create_player(self, **params):
        return self.api_post('players/create', payload=params)

    def list_players(self):
        return self.api_get('players/list')

    def show_player(self, player_id):
        return self.api_get('players/show/' + player_id)

    def update_player(self, player_id, **params):
        return self.api_put('players/update/' + player_id, data=params)

    def delete_player(self, player_id):
        return self.api_delete('players/delete/' + player_id)

    def create_adtag(self, **params):
        return self.api_post('players/adtags/create', payload=params)

    def list_adtags(self):
        return self.api_get('players/adtags/list')

    def show_adtag(self, adtag_id):
        return self.api_get('players/adtags/show/' + adtag_id)

    def update_adtag(self, adtag_id, **params):
        return self.api_put('players/adtags/update/' + adtag_id,
                            data=params)

    def delete_adtag(self, adtag_id):
        return self.api_delete('players/adtags/delete/' + adtag_id)

    def create_watermark(self, file, **params):
        return self.api_post('watermarks/create',
                             payload=params,
                             data={'file': file})

    def list_watermarks(self):
        return self.api_get('watermarks/list')

    def show_watermark(self, watermark_id):
        return self.api_get('watermarks/show/' + watermark_id)

    def update_watermark(self, watermark_id, **params):
        return self.api_put('watermarks/update/' + watermark_id,
                            data=params)

    def delete_watermark(self, watermark_id):
        return self.api_delete('watermarks/delete/' + watermark_id)


    @staticmethod
    def transformation_options(**params):
        return ','.join('{}_{}'.format(k, v) for k, v in params.items())

    @staticmethod
    def transformation_url(filename, *, extension, **params):
        filename = replace_extension(filename, extension)
        options = PublitioAPI.transformation_options(**params)
        options_url = options + '/' if options else ''
        return PublitioAPI.MEDIA_URL + 'file/' + options_url + filename

    def transformed(self, filename, *, extension, **params):
        url = PublitioAPI.transformation_url(filename,
                                             extension=extension,
                                             **params)

        res = requests.get(url)
        if not res.ok:
            raise TransformationFailed(res.reason)
        return res.content
