"""SDK for the https://publit.io RESTful API."""

import secrets
import hashlib
import calendar
import functools
import os.path
from datetime import datetime

import requests

__all__ = [
    'UnknownStatusCode',
    'TransformationFailed',
    'BadJSON',
    'PublitioAPI'
]


VERSION = '1.3.0'


class UnknownStatusCode(Exception):
    """Raised when the server responds with an unknown status code."""

    def __init__(self, status_code):
        """Create exception for given status code."""
        super().__init__(
            'API call returned unknown status code {}.'.format(status_code))


class TransformationFailed(Exception):
    """Raised when the server fails to perform a transformation."""

    def __init__(self, reason):
        """Create exception with given transformation failure reason."""
        super().__init__('File transformation failed. Reason: ' + reason)


class BadJSON(Exception):
    """Raised when the server responds with invalid JSON."""

    def __init__(self, response_text):
        """Create exception with given origin response text."""
        super().__init__(
            'Server responded with invalid JSON. Original response: ' +
            response_text)


def generate_nonce():
    x = secrets.randbelow(100000000 - 10000000) + 10000000
    return str(x)


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
    try:
        return res.json()
    except Exception:
        raise BadJSON(res.text)


def filename_without_extension(filename):
    return os.path.splitext(filename)[0]


def replace_extension(filename, new_extension):
    if new_extension is None:
        return filename

    return '{}.{}'.format(filename_without_extension(filename),
                          new_extension)


rest_get = functools.partial(rest_request, requests.get)
rest_put = functools.partial(rest_request, requests.put)
rest_post = functools.partial(rest_request, requests.post)
rest_delete = functools.partial(rest_request, requests.delete)


class PublitioAPI:
    """This class is the main interface to the Publitio RESTful API.

    It contains methods matching all API endpoints.
    For a list of endpoints, see https://publit.io/docs.
    Each method returns a dict of parsed server JSON response, except
    transformed which returns raw bytes of retrieved file.
    Each method supports keyword parameters.
    For the transformed method, these correspond to transformation parameters,
    such as w=300 to set image width to 300.
    For the other methods, these correspond to query parameters. For example,
    calling publitio_api.list_files(limit=10) will list 10 files at most.
    Make sure to check https://publit.io/docs to see which parameters
    are supported for each API endpoint.
    """

    _API_URL = 'https://api.publit.io/v1/'
    _MEDIA_URL = 'https://media.publit.io/'

    def __init__(self, key, secret):
        """Create API interface with given API key and API secret.

        You may find your API key and secret at the
        Publitio dashboard: https://publit.io/dashboard.
        """
        self.key = key
        self.secret = secret

    def _generate_signature(self, timestamp, nonce):
        s = timestamp + nonce + self.secret
        sha1_hash = hashlib.sha1(s.encode())
        digest = sha1_hash.hexdigest()
        return str(digest)

    def _api_payload(self):
        timestamp = current_unix_timestamp()
        nonce = generate_nonce()
        signature = self._generate_signature(timestamp, nonce)

        return {
            'api_key': self.key,
            'api_timestamp': timestamp,
            'api_nonce': nonce,
            'api_signature': signature,
            'api_kit': 'python3-' + VERSION
        }

    def _full_payload(self, user_payload):
        result = self._api_payload()
        result.update(user_payload)
        return result

    def _api_get(self, path, payload=None):
        return rest_get(PublitioAPI._API_URL + path,
                        params=self._full_payload(payload or {}))

    def _api_put(self, path, payload=None, data=None):
        payload = payload or {}
        data = data or {}

        return rest_put(PublitioAPI._API_URL + path,
                        params=self._full_payload(payload),
                        data=data)

    def _api_post(self, path, payload=None, data=None):
        payload = payload or {}
        data = data or {}

        return rest_post(PublitioAPI._API_URL + path,
                         params=self._full_payload(payload),
                         files=data)

    def _api_delete(self, path):
        return rest_delete(PublitioAPI._API_URL + path,
                           params=self._api_payload())

    def create_file(self, file=None, **params):
        """Create (upload) a new file.

        file should be a file opened for binary reading,
        as in open('path/to/file', 'rb'). This method will not close the file.
        If you wish to upload the file from a remote URL, supply a file_url
        keyword parameter instead of the optional file parameter.
        """
        data = None if file is None else {'file': file}
        return self._api_post('files/create',
                              payload=params,
                              data=data)

    def list_files(self, **params):
        """Get a list of all files."""
        return self._api_get('files/list', params)

    def show_file(self, file_id):
        """Get info about file with ID file_id."""
        return self._api_get('files/show/' + file_id)

    def update_file(self, file_id, **params):
        """Update properties of file with ID file_id."""
        return self._api_put('files/update/' + file_id, params)

    def delete_file(self, file_id):
        """Permanently delete file with ID file_id."""
        return self._api_delete('files/delete/' + file_id)

    def get_file_player(self, file_id, **params):
        """Get HTML5 media player for file with ID file_id."""
        return self._api_get('files/player/' + file_id, params)

    def create_version(self, file_id, **params):
        """Create a new file version."""
        return self._api_post('files/versions/create/' + file_id,
                              payload=params)

    def list_versions(self, file_id, **params):
        """Get all versions of file with ID file_id."""
        return self._api_get('files/versions/list/' + file_id,
                             payload=params)

    def show_version(self, version_id):
        """Get info about file version with ID version_id."""
        return self._api_get('files/versions/show/' + version_id)

    def update_version(self, version_id):
        """Update properties of file version with ID version_id."""
        return self._api_put('files/versions/update/' + version_id)

    def reconvert_version(self, version_id):
        """Reattempt converting file version with ID version_id.

        This can be useful if a previous conversion failed for some reason.
        """
        return self._api_put('files/versions/reconvert/' + version_id)

    def delete_version(self, version_id):
        """Permanently delete file version with id version_id."""
        return self._api_delete('files/versions/delete/' + version_id)

    def create_folder(self, **params):
        """Create a new folder.

        Usually you will want to also pass a name='<folder name>'
        keyword parameter.
        """
        return self._api_post('folders/create', payload=params)

    def list_folders(self, **params):
        """Get a list of all folders."""
        return self._api_get('folders/list', payload=params)

    def show_folder(self, folder_id):
        """Get info about folder with ID folder_id."""
        return self._api_get('folders/show/' + folder_id)

    def update_folder(self, folder_id, **params):
        """Update properties of folder with ID folder_id."""
        return self._api_put('folders/update/' + folder_id, payload=params)

    def delete_folder(self, folder_id):
        """Permanently delete folder with ID folder_id."""
        return self._api_delete('folders/delete/' + folder_id)

    def folders_tree(self):
        """Get entire folder tree."""
        return self._api_get('folders/tree')

    def create_player(self, **params):
        """Create a new HTML5 media player.

        Usually you will want to also pass a name='<player name>'
        keyword parameter.
        """
        return self._api_post('players/create', payload=params)

    def list_players(self):
        """Get a list of all players."""
        return self._api_get('players/list')

    def show_player(self, player_id):
        """Get info about player with ID player_id."""
        return self._api_get('players/show/' + player_id)

    def update_player(self, player_id, **params):
        """Update properties of player with ID player_id."""
        return self._api_put('players/update/' + player_id, payload=params)

    def delete_player(self, player_id):
        """Delete player with ID player_id."""
        return self._api_delete('players/delete/' + player_id)

    def create_adtag(self, **params):
        """Create a new adtag.

        Usually you will want to also pass name='<adtag name>'
        and tag='<tag URL>' keyword parameters.
        """
        return self._api_post('players/adtags/create', payload=params)

    def list_adtags(self):
        """Get a list of all adtags."""
        return self._api_get('players/adtags/list')

    def show_adtag(self, adtag_id):
        """Get info about adtag with ID adtag_id."""
        return self._api_get('players/adtags/show/' + adtag_id)

    def update_adtag(self, adtag_id, **params):
        """Update properties of adtag with ID adtag_id."""
        return self._api_put('players/adtags/update/' + adtag_id,
                             data=params)

    def delete_adtag(self, adtag_id):
        """Permanently delete adtag with ID adtag_id."""
        return self._api_delete('players/adtags/delete/' + adtag_id)

    def create_watermark(self, file, **params):
        """Create (upload) a new watermark.

        file should be a file opened for binary reading,
        as in open('path/to/file', 'rb'). This method will not close the file.
        """
        return self._api_post('watermarks/create',
                              payload=params,
                              data={'file': file})

    def list_watermarks(self):
        """Get a list of all watermarks."""
        return self._api_get('watermarks/list')

    def show_watermark(self, watermark_id):
        """Get properties of watermark with ID watermark_id."""
        return self._api_get('watermarks/show/' + watermark_id)

    def update_watermark(self, watermark_id, **params):
        """Update properties of watermark with ID watermark_id."""
        return self._api_put('watermarks/update/' + watermark_id,
                             data=params)

    def delete_watermark(self, watermark_id):
        """Permanently delete watermark with ID watermark_id."""
        return self._api_delete('watermarks/delete/' + watermark_id)

    @staticmethod
    def _transformation_options(**params):
        return ','.join('{}_{}'.format(k, v) for k, v in params.items())

    @staticmethod
    def _transformation_url(filename, *, extension=None, **params):
        filename = replace_extension(filename, extension)
        options = PublitioAPI._transformation_options(**params)
        options_url = options + '/' if options else ''
        return PublitioAPI._MEDIA_URL + 'file/' + options_url + filename

    def transformed(self, filename, *, extension=None, **params):
        """Transform a media file from the server and retrieve the new version.

        filename should be the name of the requested file, including its
        extension. Unlike the other methods, which return dicts of parsed
        response JSON, this method returns raw bytes of the retrieved file.
        If transformation fails, this method will throw a TransformationFailed
        exception.
        """
        url = PublitioAPI._transformation_url(filename,
                                              extension=extension,
                                              **params)

        res = requests.get(url)
        if not res.ok:
            raise TransformationFailed(res.reason)
        return res.content
