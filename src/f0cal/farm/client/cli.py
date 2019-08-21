import f0cal
import json
import os
from .api_client import DeviceFarmApi
from time import sleep, time


@f0cal.plugin(name='device', sets='config_file')
def config_file():
    return '''
    [device]
    #Assumes file will exist in current working directory
    device_filename=.f0cal_device
    
    [api]
    endpoint = http://104.197.189.7/api
    '''


class DeviceFileParser:
    def __init__(self, device_file):
        '''Parser for current device config'''
        self.device_file = device_file
        if os.path.exists(device_file):
            self.data = json.load(open(device_file))
        else:
            self.data = {}

    def __getitem__(self, item):
        return self.data[item]

    def __iter__(self):
        return self.data.__iter__()

    def write(self, device_data):
        with open(self.device_file, 'w') as f:
            json.dump(device_data, f)
        self.data = device_data


def request_args(parser):
    parser.add_argument('--wait', action='store_true', default=False, help='Wait for device status to become ready')
    parser.add_argument('-wt', '--wait-time', default=5,
                        help='How long to wait for the device to become ready in Minutes')
    parser.add_argument('-t', '--type', required=True)
    parser.add_argument('-kp', '--key-pair', required=True)
    # Todo provide argument for startup script


@f0cal.entrypoint(['farm', 'instance', 'create'], args=request_args)
def request(parser, core, type, key_pair, wait, wait_time, **_):
    device_config = DeviceFileParser(core.config['device']['device_filename'])
    api = DeviceFarmApi(api_key=core.config['api']['api_key'], api_url=core.config['api']['endpoint'])
    device_data = api.create_instance(type, key_pair)
    device_config.write(device_data)
    print(f'Successfully requested device of type {type}')
    if wait:
        timeout = time() + wait_time * 60
        while device_data['status'] != 'ready':
            device_data = api.get_instance(device_data['id'])
            if device_data['status'] == 'error':
                print(f'There was an error start vm instance {device_data["id"]} please contact F0cal')
                exit(1)
            # Todo check for change
            device_config.write(device_data)
            print('Waiting for device to become available')
            if time() > timeout:
                print(f"Error waited {wait_time} minutes but device still not ready")
                exit(1)
            sleep(5)
        print(f'Device ready')


@f0cal.entrypoint(['farm', 'instance', 'get', 'ip'])
def get_device_ip(parser, core):
    device_config = DeviceFileParser(core.config['device']['device_filename'])
    if not device_config.data:
        raise Exception(
            f"No device configure in {core.config['device']['device_filename']} please request a device first ")

    elif device_config['status'] != 'ready':
        raise Exception('Device is not ready yet. No ip available')
    print(device_config['ip'])


@f0cal.entrypoint(['farm', 'instance', 'stop'])
def stop_device(parser, core):
    device_config = DeviceFileParser(core.config['device']['device_filename'])
    api = DeviceFarmApi(api_key=core.config['api']['api_key'], api_url=core.config['api']['endpoint'])
    api.stop_instance(device_config['id'])


@f0cal.entrypoint(['farm', 'vpn', 'create'])
def get_vpn_key(parser, core):
    api = DeviceFarmApi(api_key=core.config['api']['api_key'], api_url=core.config['api']['endpoint'])
    key_string = api.get_vpn_key()
    print(key_string)


def configure_args(parser):
    parser.add_argument('-k', '--api-key')
    parser.add_argument('-e', '--endpoint')


@f0cal.entrypoint(['farm', 'configure'], args=configure_args)
def configure(parser, core, api_key, endpoint):
    if api_key:
        core.config['api']['api_key'] = api_key
    if endpoint:
        core.config['api']['endpoint'] = endpoint

    core.config.write_file(core.config_path)
