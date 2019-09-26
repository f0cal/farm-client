###########################################################
import f0cal
import wrapt

from f0cal.farm.client import entity
from f0cal.farm.client.api_client import DeviceFarmApi


@f0cal.plugin(name="device", sets="config_file")
def config_file():
    return """
    [device]
    #Assumes file will exist in current working directory
    device_filename=.f0cal_device

    [api]
    api_url = http://104.197.189.7/api
    """


def query(class_name, noun, name):
    api_key = f0cal.CORE.config["api"].get("api_key")
    api_url = f0cal.CORE.config["api"]["api_url"]
    client = DeviceFarmApi(api_url, api_key)
    cls = type(class_name, (entity.Entity,), {"CLIENT": client, NOUN: noun})
    return cls.from_name(noun, name)


@wrapt.decorator
def api_key_required(wrapped, instance, args, kwargs):
    api_key = f0cal.CORE.config["api"].get("api_key")
    if api_key is None:
        print(
            "An API KEY is required for this action please set one with\n$ f0cal farm config set api_key\n"
            "You can obtain one at f0cal.com"
        )
        exit(1)
    return wrapped(*args, **kwargs)


@wrapt.decorator
def printer(wrapped, instance, args, kwargs):
    out = wrapped(*args, **kwargs)
    if isinstance(out, list):
        for x in out:
            print(x, {k: v for k, v in x.__dict__.items() if not k.startswith("_")})
    else:
        print(out, {k: v for k, v in out.__dict__.items() if not k.startswith("_")})
    return out


def _args_device_type_describe(parser):

    parser.add_argument(
        "--device_type",
        type=lambda name: query("DeviceType", "device_type", name),
        required=False,
    )


@f0cal.entrypoint(["device_type", "describe"], args=_args_device_type_describe)
@printer
@api_key_required
def _cli_device_type_describe(parser, core, *args, **dargs):
    client = DeviceFarmApi(
        api_key=core.config["api"]["api_key"], api_url=core.config["api"]["endpoint"]
    )

    inst = dargs.pop("device_type")
    return inst.describe(*args, **dargs)


def _args_device_type_list(parser):

    pass


@f0cal.entrypoint(["device_type", "list"], args=_args_device_type_list)
@printer
@api_key_required
def _cli_device_type_list(parser, core, *args, **dargs):
    client = DeviceFarmApi(
        api_key=core.config["api"]["api_key"], api_url=core.config["api"]["endpoint"]
    )

    cls = type("DeviceType", (entity.Entity,), {"CLIENT": client, NOUN: "device_type"})
    return cls.list(*args, **dargs)


def _args_image_list(parser):

    pass


@f0cal.entrypoint(["image", "list"], args=_args_image_list)
@printer
@api_key_required
def _cli_image_list(parser, core, *args, **dargs):
    client = DeviceFarmApi(
        api_key=core.config["api"]["api_key"], api_url=core.config["api"]["endpoint"]
    )

    cls = type("Image", (entity.Entity,), {"CLIENT": client, NOUN: "image"})
    return cls.list(*args, **dargs)


def _args_image_describe(parser):

    parser.add_argument(
        "--image", type=lambda name: query("Image", "image", name), required=False
    )


@f0cal.entrypoint(["image", "describe"], args=_args_image_describe)
@printer
@api_key_required
def _cli_image_describe(parser, core, *args, **dargs):
    client = DeviceFarmApi(
        api_key=core.config["api"]["api_key"], api_url=core.config["api"]["endpoint"]
    )

    inst = dargs.pop("image")
    return inst.describe(*args, **dargs)


def _args_instance_create(parser):

    parser.add_argument(
        "--image", type=lambda name: query("Image", "image", name), required=False
    )

    parser.add_argument(
        "--device_type",
        type=lambda name: query("DeviceType", "device_type", name),
        required=True,
    )


@f0cal.entrypoint(["instance", "create"], args=_args_instance_create)
@printer
@api_key_required
def _cli_instance_create(parser, core, *args, **dargs):
    client = DeviceFarmApi(
        api_key=core.config["api"]["api_key"], api_url=core.config["api"]["endpoint"]
    )

    cls = type("Instance", (entity.Entity,), {"CLIENT": client, NOUN: "instance"})
    return cls.create(*args, **dargs)


def _args_instance_describe(parser):

    parser.add_argument(
        "--instance",
        type=lambda name: query("Instance", "instance", name),
        required=False,
    )


@f0cal.entrypoint(["instance", "describe"], args=_args_instance_describe)
@printer
@api_key_required
def _cli_instance_describe(parser, core, *args, **dargs):
    client = DeviceFarmApi(
        api_key=core.config["api"]["api_key"], api_url=core.config["api"]["endpoint"]
    )

    inst = dargs.pop("instance")
    return inst.describe(*args, **dargs)


def _args_instance_list(parser):

    pass


@f0cal.entrypoint(["instance", "list"], args=_args_instance_list)
@printer
@api_key_required
def _cli_instance_list(parser, core, *args, **dargs):
    client = DeviceFarmApi(
        api_key=core.config["api"]["api_key"], api_url=core.config["api"]["endpoint"]
    )

    cls = type("Instance", (entity.Entity,), {"CLIENT": client, NOUN: "instance"})
    return cls.list(*args, **dargs)


def _args_instance_start(parser):

    parser.add_argument(
        "--instance",
        type=lambda name: query("Instance", "instance", name),
        required=False,
    )


@f0cal.entrypoint(["instance", "start"], args=_args_instance_start)
@printer
@api_key_required
def _cli_instance_start(parser, core, *args, **dargs):
    client = DeviceFarmApi(
        api_key=core.config["api"]["api_key"], api_url=core.config["api"]["endpoint"]
    )

    inst = dargs.pop("instance")
    return inst.start(*args, **dargs)


def _args_instance_stop(parser):

    parser.add_argument(
        "--instance",
        type=lambda name: query("Instance", "instance", name),
        required=False,
    )


@f0cal.entrypoint(["instance", "stop"], args=_args_instance_stop)
@printer
@api_key_required
def _cli_instance_stop(parser, core, *args, **dargs):
    client = DeviceFarmApi(
        api_key=core.config["api"]["api_key"], api_url=core.config["api"]["endpoint"]
    )

    inst = dargs.pop("instance")
    return inst.stop(*args, **dargs)


def _args_instance_connect(parser):

    parser.add_argument(
        "--instance",
        type=lambda name: query("Instance", "instance", name),
        required=False,
    )

    parser.add_argument("--connection_type", type=str, required=False)


@f0cal.entrypoint(["instance", "connect"], args=_args_instance_connect)
@printer
@api_key_required
def _cli_instance_connect(parser, core, *args, **dargs):
    client = DeviceFarmApi(
        api_key=core.config["api"]["api_key"], api_url=core.config["api"]["endpoint"]
    )

    inst = dargs.pop("instance")
    return inst.connect(*args, **dargs)
