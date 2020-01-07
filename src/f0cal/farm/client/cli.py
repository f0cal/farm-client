import f0cal
import json
import os
import argparse
from time import time, sleep

from f0cal.farm.client.utils import query, create_class, DeviceFileParser
from f0cal.farm.client.__codegen__.cli import parse_update_string, printer, api_key_required
from f0cal.farm.client.api_client import DeviceFarmApi

@f0cal.plugin(name='farm_api', sets='config_file')
def config_file():
    return '''
    [api]
    api_url = https://app.f0cal.com/api
    device_file = ${f0cal:prefix}/etc/f0cal/devices.json
    
    '''

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

def _args_instance_create(parser):
    parser.add_argument("name", )
    parser.add_argument("--image", type=lambda name: query("Image", "image", name), required=True,)
    parser.add_argument("--device-type", type=lambda name: query("DeviceType", "device_type", name),required=True,)
    parser.add_argument("--wait", required=False, action="store_true",)
    parser.add_argument("--wait_time", type=int, required=False,)

@f0cal.entrypoint(["farm", "instance", "create"], args=_args_instance_create)
@printer
@api_key_required
def _cli_instance_create(parser, core, name,  wait=False, wait_time=15, *args, **dargs):
    device_config = DeviceFileParser(core.config['api']['device_file'])
    if name in device_config:
        print(f'ERROR: You have already name a device {name} please choose a different name')
        exit(1)
    client = DeviceFarmApi(
        api_key=core.config["api"].get("api_key"), api_url=core.config["api"]["api_url"]
    )

    cls = create_class("Instance", "instance")
    inst = cls.create(**dargs)
    device_config[name] = {'id': inst.id}
    device_config.write()
    if wait:
        if wait_time is None:
            wait_time = 15
        timeout = time() + wait_time * 60
        while inst.status != 'ready':
            inst = cls.from_id(inst.id)
            if inst.status == 'error':
                print(f'There was an error start vm instance {inst.id} please contact F0cal')
                exit(1)
            if time() > timeout:
                print(f"Error waited {wait_time} minutes but device still not ready")
                exit(1)
            print('Waiting for device to be ready')
            sleep(20)
        print(f'Device ready')
    return inst

def args_instance_connect(parser):
    parser.add_argument( "instance", type=lambda name: query("Instance", "instance", name),)
    parser.add_argument('connection_args', nargs=argparse.REMAINDER)

@f0cal.entrypoint(["farm", "instance", "connect"], args=args_instance_connect)
def instance_connect(parser, core, instance, connection_args,*args, **kwargs):
    if '--ssh' in connection_args:
        connection_type = 'ssh'
        connection_args.remove('--ssh')
    else:
        print('Only ssh connection are supported at the moment. Please use --ssh')
        exit(1)
    connection_args.remove('--')
    instance.connect(connection_type, connection_args)
def devices_args(parser):
    parser.add_argument("name", )
