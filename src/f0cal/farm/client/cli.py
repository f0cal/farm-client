import f0cal
import json
import os
import argparse
from time import time, sleep

from f0cal.farm.client.utils import query, create_class, DeviceFileParser, InstanceStatusPrinter
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
    parser.add_argument("--no-queue", required=False, action="store_true",
                        help="Only create an instance if there is a device available immediately")
    parser.add_argument("--no-block", required=False, action="store_true",
                        help='Create an instance but do not wait for it become ready')

@f0cal.entrypoint(["farm", "instance", "create"], args=_args_instance_create)
@printer
@api_key_required
def _cli_instance_create(parser, core, name,  no_block=False, wait_time=15, *args, **dargs):
    device_config = DeviceFileParser(core.config['api']['device_file'])
    if name in device_config:
        print(f'ERROR: You already have a device named {name} please choose a different name')
        exit(1)

    cls = create_class("Instance", "instance")
    inst = cls.create(**dargs)
    print(f"Requested an instance of type {dargs['device_type'].name}")
    device_config[name] = {'id': inst.id}
    device_config.write()
    if not no_block:
        inst_status = InstanceStatusPrinter(inst)
        inst_status.block()
    return inst

def args_instance_connect(parser):
    parser.add_argument( "instance", type=lambda name: query("Instance", "instance", name),)
    parser.add_argument('connection_args', nargs=argparse.REMAINDER)

def args_instance_send(parser):
    parser.add_argument( "instance", type=lambda name: query("Instance", "instance", name),)
    parser.add_argument('send_args', nargs=argparse.REMAINDER)


@f0cal.entrypoint(["farm", "instance", "send"], args=args_instance_send)
def instance_send(parser, core, instance, send_args,*args, **kwargs):
    instance.send_scp(send_args)

@f0cal.entrypoint(["farm", "instance", "connect"], args=args_instance_connect)
def instance_connect(parser, core, instance, connection_args,*args, **kwargs):
    if '--ssh' in connection_args:
        connection_type = 'ssh'
        connection_args.remove('--ssh')
    else:
        print('Only ssh connection are supported at the moment. Please use --ssh')
        exit(1)
    if '--' in connection_args:
        connection_args.remove('--')
    instance.connect(connection_type, connection_args)
def devices_args(parser):
    parser.add_argument("name", )

if __name__ == '__main__':
    from f0cal import __main__
    import sys
    import shlex
    sys.argv = shlex.split('f0cal farm instance create   my_pi   --device-type raspberry-pi/3bp   --image raspbian-lite/10@f0cal/device-farm ')
    __main__.main()
