# TODO move this into in a sepereate package
from encodings.punycode import selective_find

import requests
import wrapt
import logging

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
        elif response.status_code >= 400:
            if 'errors' in response.json():
                print(f"ERROR Bad request: \n {response.json()['errors'][0]['code']} ")
            else:
                print(f"ERROR Bad request: \n {response.json()} Please contact support@f0cal.com")
            exit(1)
        else:
            print("Unknown Error from F0cal")
            response.raise_for_status()

    def _check_response(self, response):
        if not response.ok:
            self._handle_error_response(response)

    def _get(self, url, *args, **kwargs):
        url = f'{self.url}{url}'

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
        url = f'{self.url}{url}'
        headers = kwargs.pop('headers', {})
        headers = self._add_auth(headers)
        kwargs['headers'] = headers
        try:
            response = requests.post(url, json={'data': data}, *args, **kwargs)
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:
            print(f'ERROR: {e.args[0]}')
            print("There was an error connecting to the F0cal Device Farm API. Please contact support@f0cal.com")
            exit(1)

        self._check_response(response)

        return response.json()['data']

    def _add_auth(self, headers):
        if self.api_key:
            headers.update({'Authorization': f'APIKEY {self.api_key}'})
        return headers

    @api_key_required
    def create_ssh_key_pair(self, key_name, public_key=None):
        data = {'key_name': key_name, 'public_key': public_key}
        return self._post('/public-keys/', data=data)

    @api_key_required
    def create_instance(self, hardware_type, key_name=None, start_up_script=None):
        data = {"hardware_type": hardware_type, "key_name": key_name, "startup_script": start_up_script}
        response = self._post(f"/instances/", data=data,
                              headers={'Authorization': f'APIKEY {self.api_key}'})
        return response

    @api_key_required
    def get_instance(self, instance_id):
        response = self._get(f"/instances/{instance_id}")
        return response

    @api_key_required
    def stop_instance(self, instance_id):
        response = self._post(f"/instances/stop/", data={'instance_id': instance_id})
        return response

    @api_key_required
    def get_all_key_pairs(self):
        response = self._get(f'/public-keys/')
        return response

    @api_key_required
    def get_vpn_key(self):
        response = self._post('/vpn-key', data={})
        return response['key_string']
