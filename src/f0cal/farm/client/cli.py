import f0cal
import argparse
import sys
from tabulate import tabulate
from f0cal.farm.client.utils import query, create_class, JsonFileParser, InstanceStatusPrinter, resolve_remote_url
from f0cal.farm.client.__codegen__.cli import parse_update_string, printer, api_key_required

@f0cal.plugin(name='farm_api', sets='config_file')
def config_file():
    return '''
    [api]
    api_url = https://app.f0cal.com/api
    device_file = ${f0cal:prefix}/etc/f0cal/devices.json
    remotes_file = ${f0cal:prefix}/etc/f0cal/remotes.json
    
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
    parser.add_argument("--no-queue", required=False, action="store_true",
                        help="Only create an instance if there is a device available immediately")
    parser.add_argument("--no-block", required=False, action="store_true",
                        help='Create an instance but do not wait for it become ready')
    parser.add_argument("--remote", "-r", type=lambda remote_name: resolve_remote_url(remote_name), required=True)
    ns, _ = parser.parse_known_args()
    remote = ns.remote
    parser.add_argument("--image", type=lambda name: query("Image", "image", name, remote), required=True,)
    parser.add_argument("--device-type", type=lambda name: query("DeviceType", "device_type", name, remote),required=True,)
@f0cal.entrypoint(["farm", "instance", "create"], args=_args_instance_create)
@printer
@api_key_required
def _cli_instance_create(parser, core, name, remote,  no_block=False, wait_time=15, *args, **dargs):
    device_config = JsonFileParser(core.config['api']['device_file'])
    if name in device_config:
        print(f'ERROR: You have already name a device {name} please choose a different name')
        exit(1)

    cls = create_class("Instance", "instance", remote)
    inst = cls.create(**dargs)
    print(f"Requested an instance of type {dargs['device_type'].name}")
    device_config[name] = {'id': inst.id}
    device_config.write()
    if not no_block:
        inst_status = InstanceStatusPrinter(inst)
        inst_status.block()
    return inst

def args_instance_connect(parser):
    parser.add_argument("--remote", "-r", type=lambda remote_name: resolve_remote_url(remote_name), required=True)
    ns, _ = parser.parse_known_args()
    remote = ns.remote

    parser.add_argument( "instance", type=lambda name: query("Instance", "instance", name, remote),)
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

def remote_add_args(parser):
    parser.add_argument("name", help="Your local alias for the remote cluster")
    parser.add_argument("url", help="The url of that remote cluster")

@f0cal.entrypoint(["farm", "remote", "add"], args=remote_add_args)
def add_remote(parser, core, name, url):
    remotes_file = JsonFileParser(core.config['api']['remotes_file'])
    remotes_file[name] = url
    remotes_file.write()
@f0cal.entrypoint(["farm", "remote", "list"])
def remote_list(parser, core):
    remotes_file = JsonFileParser(core.config['api']['remotes_file'])
    print(tabulate(remotes_file.data.items(), headers=["Name", "URL"]))