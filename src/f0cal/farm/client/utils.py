from builtins import print
import argparse
from f0cal.farm.client import entities
import f0cal
from progress.bar import IncrementalBar
from progress.spinner import MoonSpinner
import re
import json
from time import sleep
import os
from f0cal.farm.client.api_client import DeviceFarmApi, ConnectionError, ClientError, ServerError
import wrapt
import sys
import rich.console
import rich.table
from collections.abc import Iterable
from conans.model.ref import ConanName
from conans.errors import InvalidNameException

REFERENCE_REGEX = '([\\w]*)\\/([\\w]*)(#[\\d]*)?$'

class JsonFileParser:
    def __init__(self, json_file):
        '''Parser for current device config'''
        self.json_file = json_file
        if os.path.exists(json_file):
            self.data = json.load(open(json_file))
        else:
            os.makedirs(os.path.dirname(json_file), exist_ok=True)
            self.data = {}

    def __getitem__(self, item):
        return self.data[item]
    def __setitem__(self, key, value):
        self.data[key] = value

    def __iter__(self):
        return self.data.__iter__()

    def write(self):
        with open(self.json_file, 'w') as f:
            json.dump(self.data, f)
def resolve_remote_url(remote_name):
    remotes_file = JsonFileParser(f0cal.CORE.config['api']['remotes_file'])
    if remote_name in remotes_file:
        return remotes_file[remote_name]
    print(f'Remote {remote_name} not found. Please configure the remote first using: f0cal remote add '
          f'<remote_name>  <remote_url>')
    exit(1)

def create_class(class_name, noun, remote=False):
    api_key = f0cal.CORE.config["api"].get("api_key")
    if remote:
        # TODO THIS A HACKY WORKAROUND FOR THE PLUGPARSE RUNNING ALL ARG SETTERS
        parser = argparse.ArgumentParser()
        parser.add_argument("--remote", "-r", type=lambda remote_name: resolve_remote_url(remote_name), required=True)
        ns, _  = parser.parse_known_args()

        api_url = ns.remote
    else:
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
def query(class_name, noun, ref, remote=None):
    cls = create_class(class_name, noun, remote)
    ref_type = _resolve_reference_type(ref)
    if ref_type == 'reference':
        print('Referencing objects is only supported from ids currently. Check back soon for full namespace resolution')
        exit(1)
    try:
        if ref_type == 'name':
            # Instance names are resolved locally
            if noun == 'instance':
                device_config = JsonFileParser(f0cal.CORE.config['api']['device_file'])
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
    except (ConnectionError, ClientError, ServerError) as e:
        print(e.args[0])
        exit(1)

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

class Printer:

    @classmethod
    def _force_string(cls, blob):
        if isinstance(blob, list):
            return "\n".join(blob)
        return str(blob)

    @classmethod
    def _blob_to_table(cls, rows, cols):
        table = rich.table.Table(show_header=True)
        [table.add_column(col_name) for col_name in cols]
        [table.add_row(*r) for r in rows]
        return table

    @classmethod
    def blob_to_table(cls, blob):
        if not isinstance(blob, list):
            blob = [blob]
        _coerce = lambda _row: [cls._force_string(_c) for _c in _row.values()]
        _capitalize = lambda _col: _col.replace("_", " ").title()
        rows = [tuple(_coerce(row)) for row in blob]
        cols = [_capitalize(col) for col in blob.pop().keys()]
        return cls._blob_to_table(rows, cols)

    @classmethod
    def unk_to_blob(cls, unk):
        if isinstance(unk, list):
            return [cls.unk_to_blob(u) for u in unk]
        elif isinstance(unk, dict):
            return unk
        return cls.obj_to_blob(unk)

    @classmethod
    def obj_to_blob(cls, obj):
        if hasattr(obj, 'printable_json'):
            return obj.printable_json
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}

    @classmethod
    def print_table(cls, unk):
        if isinstance(unk, Iterable) and len(unk) == 0:
            print("EMPTY")
            return
        blob = cls.unk_to_blob(unk)
        rich.console.Console().print(cls.blob_to_table(blob))

    @classmethod
    def print_json(cls, unk):
        blob = cls.unk_to_blob(unk)
        print(blob)

@wrapt.decorator
def printer(wrapped, instance, args, kwargs):
    json = kwargs.pop("json", False)
    try:
        out = wrapped(*args, **kwargs)
    except (ConnectionError, ClientError, ServerError) as e:
        print(e.args[0])
        exit(1)
    if json:
        Printer.print_json(out)
    else:
        Printer.print_table(out)
    return out

class QueueingBar(IncrementalBar):
    suffix = '%(spinner)s'
    spinner_pos = 0
    spinner_phases = MoonSpinner.phases
    @property
    def spinner(self):
        self.spinner_pos = (self.spinner_pos + 1) % len(self.spinner_phases)
        return self.spinner_phases[self.spinner_pos]

class InstanceStatusPrinter:
    def __init__(self, instance):
        self.instance = instance
    def block(self):
        self._wait_queued()
        self._wait_provisioning()


    def _wait_queued(self):
        if self.instance.status == 'queued':
            print(f"No hardware immediately available")
            original_queue_position = self.instance.queue_position
            queue_position = original_queue_position
            with QueueingBar(message=f'Current queue length: {queue_position}', max=original_queue_position) as bar:
                while self.instance.status == 'queued':
                    self._refresh_instance()
                    if queue_position != self.instance.queue_position:
                        queue_position = self.instance.queue_position
                        bar.message=f'Current queue length {queue_position}'
                        bar.next()
                    bar.update()
                    sleep(.25)
                bar.finish()
    def _refresh_instance(self):
        error_count = 0
        while error_count < 5:
            try:
                self.instance.refresh()
                return
            except (ConnectionError, ServerError) as e:
                error_count += 1
        self.instance.refresh()

    def _wait_provisioning(self):
        with IncrementalBar('Loading your device image', suffix=' [ %(elapsed_td)s/ 00:06:000 ]', max=360) as bar:
            elapsed_time = 0
            while self.instance.status == 'provisioning':
                bar.next()
                sleep(1)
                elapsed_time += 1
                if elapsed_time % 5 == 0:
                    self._refresh_instance()
            bar.finish()
        if self.instance.status == 'error':
            print(f'There was an error starting instance {self.instance.id} please contact F0cal')
            exit(1)
        if self.instance.status == 'ready':
            print('Your instance is ready to be used')

# TODO REFACTOR TO PULL OUT BASE CLASS
class ImageStatusPrinter:
    def __init__(self, image):
        self.image = image
    def block(self):
        self._wait_saving()
    def _wait_saving(self):
        with MoonSpinner('Saving your device image: ') as bar:
            elapsed_time = 0

            while self.image.status == 'saving':
                bar.next()
                sleep(.25)
                elapsed_time += .25
                if elapsed_time % 3 == 0:
                    self.image.refresh()
            bar.finish()
        if self.image.status == 'ready':
            print('Your image has been saved')
            return
        if 'error' in self.image.status:
            print("There was an error saving you instance please contact F0cal")
            exit(1)

def verify_conan_name(name):
    try:
        ConanName.validate_name(name)
    except InvalidNameException as e:
        print(e.args[0])
        exit(1)
    return name
