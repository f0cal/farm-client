import f0cal.core
import argparse
import sys
from f0cal.farm.client.utils import query, create_class, JsonFileParser, InstanceStatusPrinter, resolve_remote_url, Printer
from f0cal.farm.client.__codegen__.cli import parse_update_string, printer, api_key_required
from  f0cal.farm.client.conan_client import ConanClient

@f0cal.core.plugin(name='farm_api', sets='config_file')
def config_file():
    return '''
    [api]
    api_url = https://app.f0cal.com/api
    device_file = ${f0cal:prefix}/etc/f0cal/devices.json
    remotes_file = ${f0cal:prefix}/etc/f0cal/remotes.json
    images_file = ${f0cal:prefix}/etc/f0cal/images.json
    
    '''

def configure_args(parser):
    help_string = 'Should be in the form of "key=value" where key is one of {"api_key",  "api_url"}'
    parser.add_argument("update_args", type=lambda update_string: parse_update_string(update_string), help=help_string)


@f0cal.core.entrypoint(['farm', 'config', 'update'], args=configure_args)
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
    parser.add_argument("--image", type=lambda name: query("Image", "image", name), required=True,)
    parser.add_argument("--device-type", type=lambda name: query("DeviceType", "device_type", name, remote=True),required=True,)
    parser.add_argument("--ssh-key", type=lambda name: query("SshKey", "ssh_key", name, remote=False))


@f0cal.core.entrypoint(["farm", "instance", "create"], args=_args_instance_create)
@printer
@api_key_required
def _cli_instance_create(parser, core, name, remote,  no_block=False, wait_time=15, *args, **dargs):
    # TODO MOVE CODE TO INSTANCE ENTITY
    device_config = JsonFileParser(core.config['api']['device_file'])
    if name in device_config:
        print(f'ERROR: You already have a device named {name} please choose a different name')
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
    # ns, _ = parser.parse_known_args()
    # remote = ns.remote

    parser.add_argument( "instance", type=lambda name: query("Instance", "instance", name, remote=True),)
    parser.add_argument('connection_args', nargs=argparse.REMAINDER)


@f0cal.core.entrypoint(["farm", "instance", "connect"], args=args_instance_connect)
def instance_connect(parser, core, instance, connection_args, remote, *args, **kwargs):
    if '--ssh' in connection_args:
        connection_type = 'ssh'
        connection_args.remove('--ssh')
    else:
        print('Only ssh connection are supported at the moment. Please use --ssh')
        exit(1)
    if '--' in connection_args:
        connection_args.remove('--')
    instance.connect(connection_type, connection_args, remote)

def remote_add_args(parser):
    parser.add_argument("name", help="Your local alias for the remote cluster")
    parser.add_argument("--url",  help="The url of that remote cluster")

@f0cal.core.entrypoint(["farm", "remote", "add"], args=remote_add_args)
def add_remote(parser, core, name, url):
    if url is None:
        Cluster = create_class("Cluster", "cluster")
        clusters = Cluster.query()
        for cluster in clusters:
            if cluster.fully_qualified_name == name:
                base_url = f0cal.core.CORE.config["api"]["api_url"]
                url = f'{base_url}{cluster.path}'
                break
        else:
            print(f'No cluster named {name} was found. Please see available clusters via:\nf0cal farm cluster query')
            exit(1)
    remotes_file = JsonFileParser(core.config['api']['remotes_file'])
    if name in remotes_file and remotes_file[name] == url:
        print('WARNING: This remote already exists')
        return
    remotes_file = JsonFileParser(core.config['api']['remotes_file'])
    remotes_file[name] = url
    remotes_file.write()

@f0cal.core.entrypoint(["farm", "remote", "list"])
def remote_list(parser, core):
    remotes_file = JsonFileParser(core.config['api']['remotes_file'])
    data = [dict(alias=k, url=v) for k, v in remotes_file.data.items()]
    Printer.print_table(data)

def image_push_args(parser):
    parser.add_argument("local_image", help='Name of locally cached image')

@f0cal.core.entrypoint(["farm", "image", "push"], args=image_push_args)
def image_push(parser, core, local_image):

    # TODO GENREALLY NEED SOME ERROR HANDELING HERE.
    # TODO MOVE LOGINC INTO IMAGE ENTITY
    img_cls = create_class("Image", "image", remote=True)
    images_file = JsonFileParser(f0cal.core.CORE.config['api']['images_file'])
    if local_image not in images_file:
        print(f'ERROR: Image {local_image} does not exist locally')
        exit(1)
    print("Compressing and uploading you image, this may take a while...")
    img_cls._conan_push(local_image)
    local_image_data = images_file[local_image]
    img = img_cls.create(**local_image_data['data'])
    factory_class = create_class('KnownInstanceFactory')
    for factory in local_image_data['known_instance_factories']:
        print(factory)
        inst = factory_class.create(**factory)

