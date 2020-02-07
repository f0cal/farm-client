from f0cal.farm.client import entities
import f0cal
import re
import json
import os
from f0cal.farm.client.api_client import DeviceFarmApi
import wrapt
REFERENCE_REGEX = '([\\w]*)\\/([\\w]*)(#[\\d]*)?$'

class DeviceFileParser:
    def __init__(self, device_file):
        '''Parser for current device config'''
        self.device_file = device_file
        if os.path.exists(device_file):
            self.data = json.load(open(device_file))
        else:
            os.makedirs(os.path.dirname(device_file), exist_ok=True)
            self.data = {}

    def __getitem__(self, item):
        return self.data[item]
    def __setitem__(self, key, value):
        self.data[key] = value

    def __iter__(self):
        return self.data.__iter__()

    def write(self):
        with open(self.device_file, 'w') as f:
            json.dump(self.data, f)

def create_class(class_name, noun):
    api_key = f0cal.CORE.config["api"].get("api_key")
    api_url = f0cal.CORE.config["api"]["api_url"]
    client = DeviceFarmApi(api_url, api_key)
    cls = type(
        class_name, (getattr(entities, class_name),), {"CLIENT": client, "NOUN": noun}
    )
    return cls

def _resolve_reference_type(ref):
    # match = re.match(REFERENCE_REGEX, ref)
    # if match:
    #     return 'reference'
    if ref.startswith(':'):
        return 'id'

    return 'name'
def query(class_name, noun, ref):
    cls = create_class(class_name, noun)
    ref_type = _resolve_reference_type(ref)
    if ref_type == 'reference':
        print('Referencing objects is only supported from ids currently. Check back soon for full namespace resolution')
        exit(1)
    if ref_type == 'name':
        # Instance names are resolved locally
        if noun == 'instance':
            device_config = DeviceFileParser(f0cal.CORE.config['api']['device_file'])
            if ref not in device_config:
                print(
                    'Name instance name not found. If you created in a different env try querying '
                    'all instances: \n f0cal farm instance query and then referencing it via id \n :<id> ')
                exit(1)
            return cls.from_id(device_config[ref]['id'])
        inst = cls.from_name(ref)
    else:
        _id = ref.replace(':', '')
        inst = cls.from_id(_id)
    return inst


def parse_query_string(query_string):
    ret = {}
    try:
        pairs = query_string.split(",")
        for pair in pairs:
            key, val = map(lambda x: x.strip(), pair.split("=="))
            ret[key] = val
    except:
        print("Error parsing query string. Please make sure it is formatted correctly")
    return ret


def parse_update_string(update_string):
    ret = {}
    try:
        pairs = update_string.split(",")
        for pair in pairs:
            key, val = map(lambda x: x.strip(), pair.split("="))
            ret[key] = val
    except:
        print("Error update tring. Please make sure it is formatted correctly")
    return ret

@wrapt.decorator
def api_key_required(wrapped, instance, args, kwargs):
    api_key = f0cal.CORE.config['api'].get('api_key')
    if api_key is None:
        print(
            'An API KEY is required for this action please set one with\n$f0cal farm config update "api_key=$YOU_API_KEY"\n'
            'You can obtain one at f0cal.com')
        exit(1)
    return wrapped(*args, **kwargs)

@wrapt.decorator
def printer(wrapped, instance, args, kwargs):
    out = wrapped(*args, **kwargs)
    if isinstance(out, list):
        for x in out:
            print({k: v for k, v in x.__dict__.items() if not k.startswith("_")})
    else:
        print({k: v for k, v in out.__dict__.items() if not k.startswith("_")})
    return out