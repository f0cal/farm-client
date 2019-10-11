# TODO move this into in a sepereate package
from encodings.punycode import selective_find

import requests
import logging
import wrapt

LOG = logging.getLogger(__name__)


@wrapt.decorator
def api_key_required(wrapped, instance, args, kwargs):
    if instance.api_key == None:
        raise Exception(
            'This call requires an apikey. Please provide an APIkey')
    return wrapped(*args, **kwargs)


class DeviceFarmApi:

    def __init__(self, api_url, api_key=None):
        self.url = api_url
        self.api_key = api_key

    @staticmethod
    def _handle_error_response(response):
        if response.status_code >= 500:
            print(
                f"There was an Server ERROR in the F0cal Device Farm API at {response.request.path_url}. Please contact Please contact support@f0cal.com")
            LOG.debug(f'Error at url {response.request.path_url}: {response.text}')
            exit(1)

        elif response.status_code == 401:
            print('ERROR: Unauthorized\nPlease ensure you api key is valid')
            exit(1)
        elif response.status_code >= 400:
            if 'errors' in response.json():
                print(f"ERROR Bad request: \n{response.json()['errors'][0]['code']} ")
            else:
                print(f"ERROR Bad request: \n{response.json()} Please contact support@f0cal.com")
            exit(1)

        else:
            print("Unknown Error from F0cal")
            response.raise_for_status()

    def _check_response(self, response):
        if not response.ok:
            self._handle_error_response(response)

    def _prep_data(self, data):
        data = {k: v for k, v in data.items() if v is not None}
        return data

    def _get(self, url, *args, **kwargs):

        headers = kwargs.pop('headers', {})
        headers = self._add_auth(headers)
        kwargs['headers'] = headers
        try:
            response = requests.get(url, *args, **kwargs)
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:
            print(f'ERROR: {e.args[0]}')
            print("There was an error connecting to the F0cal Device Farm API. Please contact support@f0cal.com")
            exit(1)

        self._check_response(response)

        return response.json()['data']

    def _post(self, url, data, *args, **kwargs):
        headers = kwargs.pop('headers', {})
        headers = self._add_auth(headers)
        kwargs['headers'] = headers
        data = self._prep_data(data)
        try:
            response = requests.post(url, json={'data': data}, *args, **kwargs)
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:
            print(f'ERROR: {e.args[0]}')
            print("There was an error connecting to the F0cal Device Farm API. Please contact support@f0cal.com")
            exit(1)

        self._check_response(response)
        return response.json()['data']

    def create(self, noun, data):
        url = f'{self.url}/{noun}/'
        return self._post(url, data)

    def list(self, noun):
        url = f'{self.url}/{noun}/'
        return self._get(url)

    def retrieve(self, noun, _id):
        url = f'{self.url}/{noun}/{_id}'
        return self._get(url)

    def action(self, noun, _id, verb, data):
        url = f'{self.url}/{noun}/{_id}/{verb}/'
        return self._post(url, data)

    def _add_auth(self, headers):
        if self.api_key:
            headers.update({'Authorization': f'APIKEY {self.api_key}'})
        return headers
