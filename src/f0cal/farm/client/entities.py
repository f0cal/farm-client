from f0cal.farm.client.__codegen__.entities import *
from f0cal.farm.client.api_client import DeviceFarmApi
from f0cal.farm.client.conan_client import ConanClient
import argparse
import f0cal
import urllib
import os
import logging

LOG = logging.getLogger(__name__)


class Instance(Instance):
    def connect(self, connection_type, connection_args, remote):
        if not self.status == 'ready':
            print('The instance is not ready yet')
            exit(1)
        _fn = getattr(self, f'_connect_{connection_type}', None)
        if not _fn:
            print(f'{connection_type} connections not supported')
            exit(1)
        return _fn(connection_args, remote)

    def destroy(self, *args, **kwargs):
        return self.stop()

    def stop(self, *args, **kwargs):
        print('Stopping instance')
        return self._do_verb('stop', {})

    def _connect_ssh(self, connection_args, remote):
        ssh_bin = '/usr/bin/ssh'
        connection_args = self._format_ssh_args(connection_args, remote)
        print('*' * 80)
        print('Starting an SSH session with your instance. Press CTRL+d to exit')
        print('*' * 80)
        os.execvp(ssh_bin, connection_args)

    def _format_ssh_args(self, connection_args, remote):
        user = self._get_user(remote)
        ip, port = self._get_url()
        if port:
            connection_args = ['-p', f'{port}'] + connection_args
        connection_args = ['ssh'] + [f'{user}@{ip}'] + connection_args
        return connection_args

    def _get_user(self, remote):
        try:
            image_id = self.image_id
            api_key = f0cal.CORE.config["api"].get("api_key")
            client = DeviceFarmApi(remote, api_key)
            img_cls = type('Image', (Image,), {"CLIENT": client, "NOUN": 'image'})
            image = img_cls.from_id(image_id)
            return image.admin_user
        except Exception as e:
            LOG.error(e)
            print('Error: Could not get user for the image this instance is using')
            exit(1)

    def _get_url(self):
        ip = self.ip
        if ip is None:
            print('This instance does not have an ip configured yet. Are you sure its ready?')
        parts = urllib.parse.urlparse(ip)
        return parts.hostname, parts.port

    def save(self, *args, **kwargs):
        no_block = kwargs.pop('no_block')
        # TODO THIS IS A BIT UGLY SAVE SHOULD ACTAULLY BE A MODE OF CREATION ON AN IMAGE NO VERB ON INSTANCWE
        image_data = self._do_verb('save', kwargs)
        cls = type("Image", (Image,), {"CLIENT": self.CLIENT, "NOUN": 'image'})
        image = cls.from_id(image_data.id)
        if not no_block:
            # Ugly circular import
            from f0cal.farm.client.utils import ImageStatusPrinter
            printer = ImageStatusPrinter(image)
            printer.block()
        return image

    @property
    def printable_json(self):
        return {'status': self.status, 'id': self.id, 'queue_position': self.queue_position,
                'created_at': self.created_at, 'ended_at': self.ended_at}


class Image(Image):
    def _conan_pull(self, remote):
        conan_client = ConanClient()
        conan_client.image_pull(self.name, remote)

    def _conan_push(self, remote):
        conan_client = ConanClient()
        conan_client.image_push(self.name, remote)

    def serialize(self):
        # TODO MOVE JSONFILE PARSER TO AVOIND CIRCULAR IMPORT AND IMPORT UP TOP
        from f0cal.farm.client.utils import JsonFileParser
        images_file = JsonFileParser(f0cal.CORE.config['api']['images_file'])
        if self.name in images_file:
            raise Exception(f'The image {self.name} already exists locally')
        for factory in self.known_instance_factories:
            factory.pop('id')
        images_file[self.name] = {
            'data': {'name': self.name, 'admin_user': self.admin_user, 'admin_password': self.admin_password},
            'known_instance_factories': self.known_instance_factories}
        images_file.write()

    def pull(self, remote):
        self._conan_pull(remote)
        self.serialize()
        return self

    @property
    def printable_json(self):
        _s = [x['name'] for x in self.supported_device_types]
        return {'name': self.name, \
                'supported_device_types': _s, \
                }


class SshKey(SshKey):
    @classmethod
    def create(cls, **data):
        save_file = data.pop('file')
        inst = super().create(**data)
        with open(save_file, 'w') as f:
            f.write(inst.private_key)
        os.chmod(save_file, 0o600)
        return inst

    @property
    def printable_json(self):
        return {'name': self.name, 'id': self.id}
