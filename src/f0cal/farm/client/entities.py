from urllib import response

from f0cal.farm.client.__codegen__.entities import *
from f0cal.farm.client.api_client import DeviceFarmApi
from f0cal.farm.client.conan_client import ConanClient
import argparse
import f0cal.core
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
        user = self.user
        ip, port = self._get_ip()
        if port:
            connection_args = ['-p', f'{port}'] + connection_args
        connection_args = ['ssh'] + [f'{user}@{ip}'] + connection_args
        return connection_args
    @property
    def user(self):
        try:
            image_id = self.image_id
            api_key = f0cal.core.CORE.config["api"]["api_key"]
            api_url = f0cal.core.CORE.config["api"]["api_url"]
            client = DeviceFarmApi(api_url, api_key)
            img_cls = type('Image', (Image,), {"CLIENT": client, "NOUN": 'image'})
            image = img_cls.from_id(image_id)
            return image.admin_user
        except NoSuchItemException as e:
            print(e.args[0])
            exit(1)
        except Exception as e:
            LOG.error(e)
            print('Error: Could not get user for the image this instance is using')
            exit(1)

    def _get_ip(self):
        ip = self.ip
        port = None
        if ip is None:
            print('This instance does not have an ip configured yet. Are you sure its ready?')
        if ':' in ip:
            ip, _, port = ip.rpartition(':')
        return ip, port

    def save(self, *args, **kwargs):
        no_block = kwargs.pop('no_block')
        # TODO THIS IS A BIT UGLY SAVE SHOULD ACTAULLY BE A MODE OF CREATION ON AN IMAGE NO VERB ON INSTANCWE
        image_data = self._do_verb('save', kwargs)
        client = DeviceFarmApi(
            api_key=f0cal.core.CORE.config["api"].get("api_key"), api_url=f0cal.core.CORE.config["api"]["api_url"]
        )
        cls = type("Image", (Image,), {"CLIENT": client, "NOUN": 'image'})
        image = cls.from_id(image_data.id)
        if not no_block:
            # Ugly circular import
            from f0cal.farm.client.utils import ImageStatusPrinter
            printer = ImageStatusPrinter(image)
            printer.block()
        return image
    def get_serial_log(self, output_file, *args, **kwargs):
        url = f'{self.CLIENT.url}/instance/{self.id}/serial_log/'
        response = self.CLIENT._get_raw(url)
        with open(output_file, 'w') as f:
            f.write(response.text)
        print(f'Successfully wrote serial logs  to {output_file}')
        exit(0)
    @property
    def printable_json(self):
        return {'status': self.status, 'id': self.id, 'public_ip': self.ip, 'user': self.user,
                'queue_position': self.queue_position,
                'created_at': self.created_at, 'ended_at': self.ended_at}


class Image(Image):
    @classmethod
    def _conan_pull(cls, remote, image_name):
        conan_client = ConanClient()
        conan_client.image_pull(image_name)
    @classmethod
    def _conan_push(cls, image_name):
        conan_client = ConanClient()
        conan_client.image_push(image_name)

    def serialize(self):
        # TODO (HACKY) MOVE JSONFILE PARSER TO AVOID CIRCULAR IMPORT AND IMPORT UP TOP
        from f0cal.farm.client.utils import JsonFileParser
        images_file = JsonFileParser(f0cal.core.CORE.config['api']['images_file'])
        if self.name in images_file:
            raise Exception(f'The image {self.name} already exists locally')
        for factory in self.known_instance_factories:
            factory.pop('id')
        images_file[self.name] = {
            'data': {'name': self.name, 'admin_user': self.admin_user, 'admin_password': self.admin_password},
            'known_instance_factories': self.known_instance_factories}
        images_file.write()

    def pull(self):
        self._conan_pull(self.name)
        self.serialize()
        return self

    @property
    def printable_json(self):
        _s = [x['name'] for x in self.supported_device_types]
        return {'name': self.name,
                'supported_device_types': _s,
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
