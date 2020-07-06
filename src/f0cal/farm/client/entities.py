from builtins import super

from f0cal.farm.client.__codegen__.entities import *
from f0cal.farm.client.api_client import DeviceFarmApi
import argparse
import f0cal
import urllib
import os
import shlex
import subprocess
import yaml
from time import sleep, time
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

    def destroy(self):
        return self.stop()

    def stop(self):
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
        return self._do_verb('save', kwargs)


class Image(Image):
    def _conan_pull(self):
        print('!' * 80)
        print('CONAN PULL IS NOT YET IMPLEMENTED PLEASE MANUALLY PULL THE IMAGE ')
        print('!' * 80)

    def _conan_push(self):
        print('!' * 80)
        print('CONAN PUSH IS NOT YET IMPLEMENTED PLEASE MANUALLY PUSH THE IMAGE ')
        print('!' * 80)

    def serilaze(self):
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

    def pull(self):
        self._conan_pull()
        self.serilaze()
        return self
