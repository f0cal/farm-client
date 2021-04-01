import requests
import logging
import wrapt
import json
from f0cal.farm.client.__codegen__.entities import EntityBase

LOG = logging.getLogger(__name__)


class ServerError(Exception):
    pass


class ClientError(Exception):
    pass


class ConnectionError(Exception):
    pass


@wrapt.decorator
def api_key_required(wrapped, instance, args, kwargs):
    if instance.api_key == None:
        raise Exception(
            'This call requires an apikey. Please provide an APIkey')
    return wrapped(*args, **kwargs)


class DeviceFarmApi:
    def __init__(self, api_url, api_key=None):
        self.url = f'{api_url}/api'
        self.api_key = api_key

    @staticmethod
    def _handle_error_response(response):
        if response.status_code >= 500:
            err_str = f"There was an Server ERROR in the F0cal Device Farm API at {response.request.path_url}. Please contact Please contact support@f0cal.com"
            raise ServerError(err_str)

        elif response.status_code == 401:
            err_str = 'ERROR: Unauthorized\nPlease ensure you api key is valid'
            raise ClientError(err_str)

        elif response.status_code >= 400:
            try:
                response_json = response.json()
            except json.decoder.JSONDecodeError:
                raise ClientError(f"ERROR Bad request")
            if 'errors' in response_json:
                err_str = f"ERROR Bad request: \n{response_json['errors'][0]['code']}"
            else:
                err_str = f"ERROR Bad request: \n{response.json()} Please contact support@f0cal.com"
            raise ClientError(err_str)

        else:
            print("Unknown Error from F0cal")
            response.raise_for_status()

    def _check_response(self, response):
        if not response.ok:
            self._handle_error_response(response)

    def _prep_data(self, data):
        for key, val in data.items():
            if isinstance(val, EntityBase):
                data[key] = val.id
        # There is an issue with FlaskResty/marshmallow and None values
        data = {k: v for k, v in data.items() if v is not None}
        return data
    def _get_raw(self, url, *args, **kwargs):
        headers = kwargs.pop('headers', {})
        headers = self._add_auth(headers)
        kwargs['headers'] = headers
        try:
            response = requests.get(url, *args, **kwargs)
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:
            err_str = f"There was an error connecting to the F0cal Device Farm API. Please contact support@f0cal.com" \
                      f"\nMore info:\n{e.args[0]}"
            raise ConnectionError(err_str)

        self._check_response(response)
        return response

    def _get(self, url, *args, **kwargs):
        response = self._get_raw(url, *args, **kwargs)
        return response.json()['data']

    def _post(self, url, data, *args, **kwargs):
        headers = kwargs.pop('headers', {})
        headers = self._add_auth(headers)
        kwargs['headers'] = headers
        data = self._prep_data(data)
        try:
            response = requests.post(url, json={'data': data}, *args, **kwargs)
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:
            err_str = f"There was an error connecting to the F0cal Device Farm API. Please contact support@f0cal.com" \
                      f"\nMore info:\n{e.args[0]}"
            raise ConnectionError(err_str)

        self._check_response(response)
        return response.json()['data']

    def _patch(self, url, data, *args, **kwargs):

        headers = kwargs.pop('headers', {})
        headers = self._add_auth(headers)
        kwargs['headers'] = headers
        data = self._prep_data(data)
        try:
            response = requests.patch(url, json={'data': data}, *args, **kwargs)
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:
            LOG.error(f'ERROR: {e.args[0]}')
            err_str = f"There was an error connecting to the F0cal Device Farm API. Please contact support@f0cal.com" \
                      f"\nMore info:\n{e.args[0]}"
            raise ConnectionError(err_str)

        self._check_response(response)
        return response.json()['data']

    def _delete(self, url, *args, **kwargs):

        headers = kwargs.pop('headers', {})
        headers = self._add_auth(headers)
        kwargs['headers'] = headers
        try:
            response = requests.delete(url, *args, **kwargs)
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:
            err_str = f"There was an error connecting to the F0cal Device Farm API. Please contact support@f0cal.com" \
                      f"\nMore info:\n{e.args[0]}"
            raise ConnectionError(err_str)
        self._check_response(response)

        return response.json()['data']

    def create(self, noun, data, remote=None):
        url = f'{self.url}/{noun}/'
        return self._post(url, data)

    def update(self, noun, _id,  data, remote=None):
        url = f'{self.url}/{noun}/{_id}'
        return self._patch(url, data)

    def delete(self, noun, _id, remote=None):
        url = f'{self.url}/{noun}/{_id}'
        return self._delete(url)

    def list(self, noun, remote=None):
        url = f'{self.url}/{noun}/'
        return self._get(url)

    def retrieve(self, noun, _id, remote=None):
        url = f'{self.url}/{noun}/{_id}'
        return self._get(url)

    def action(self, noun, _id, verb, data, remote=None):
        url = f'{self.url}/{noun}/{_id}/{verb}/'
        return self._post(url, data)

    def _add_auth(self, headers):
        if self.api_key:
            headers.update({'Authorization': f'APIKEY {self.api_key}'})
        return headers
