import f0cal
import json
import os
from f0cal.farm.client.__codegen__.cli import parse_update_string

@f0cal.plugin(name='farm_api', sets='config_file')
def config_file():
    return '''
    [api]
    api_url = https://app.f0cal.com/api
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


def configure_args(parser):
    help_string = 'Should be in the form of "key=value" where key is one of {"api_key",  "api_url"}'
    parser.add_argument("update_args", type=lambda update_string: parse_update_string(update_string), help=help_string)


@f0cal.entrypoint(['farm', 'config', 'update'], args=configure_args)
def configure(parser, core,  update_args):
    if 'api_key' in update_args:
        core.config['api']['api_key'] = update_args['api_key']
        print("Updated API key")
    if 'api_url' in update_args:
        core.config['api']['api_url'] = update_args['api_url']
        print("Updated API url")


    core.config.write_file(core.config_path)
