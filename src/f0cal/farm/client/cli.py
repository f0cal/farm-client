import f0cal
import json
import os
import argparse
from f0cal.farm.client.utils import query
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

def args_instance_connect(parser):
    parser.add_argument( "instance", type=lambda name: query("Instance", "instance", name),)
    parser.add_argument('--connection_type', '-type', nargs='?', default='ssh')
    parser.add_argument('connection_args', nargs=argparse.REMAINDER)
@f0cal.entrypoint(["farm", "instance", "connect"], args=args_instance_connect)
def instance_connect(parser, core, instance, connection_type, connection_args):
    print(instance)
    instance.connect(connection_type, connection_args)

if __name__ == '__main__':
    from f0cal.__main__ import main
    import sys
    import shlex
    sys.argv=shlex.split('f0cal farm instance connect instance-9f1f40e42d0d11ea91b2dd8503cf15b0')
    main()