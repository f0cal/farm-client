from builtins import super

from f0cal.farm.client.__codegen__.entities import *
from f0cal.farm.client.utils import create_class

from f0cal.my_device.conan_utils.conan_data_parser import ConanData
import urllib
import os
import shlex
import subprocess
import yaml
from time import sleep, time
import logging

LOG = logging.getLogger(__name__)


class Instance(Instance):
    def connect(self, connection_type, connection_args):
        if not self.status == 'ready':
            print('The instance is not ready yet')
            exit(1)
        print(connection_type)
        _fn = getattr(self, f'_connect_{connection_type}', None)
        if not _fn:
            print(f'{connection_type} connections not supported')
            exit(1)
        return _fn(connection_args)

    def destroy(self):
        return self.stop()

    def stop(self):
        print('Stopping instance')
        return self._do_verb('stop', {})

    def _connect_ssh(self, connection_args):
        ssh_bin = '/usr/bin/ssh'
        connection_args = self._format_ssh_args(connection_args)
        print('*'*80)
        print('Starting an SSH session with your instance. Press CTRL+d to exit')
        print('*' * 80)
        os.execvp(ssh_bin, connection_args)
    def _format_ssh_args(self, connection_args):
        user = self._get_user()

        ip , port = self._get_url()
        connection_args = ['ssh'] + connection_args + [f'{user}@{ip}']
        if port:
            connection_args = connection_args + ['-p', f'{port}']
        return connection_args
    def _get_user(self):
        try:
            image_id = self.image_id
            img_cls = create_class("Image", "image")

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


class Image(Image):
    CONANDATA_FILE = 'conandata.yml'
    CONANFILE = 'conanfile.py'

    @classmethod
    def _resolve_remote_name(cls, remote_url):
        ret = subprocess.run(shlex.split('conan remote list'), capture_output=True)
        output = ret.stdout.decode()
        output = output.replace('[Verify SSL: True]', '')
        output = output.replace('[Verify SSL: False]', '')

        remotes = yaml.load(output)
        for name, url in remotes.items():
            if url == remote_url:
                return name
        print(f"Error could not find conan remote with url {remote_url}. Please add this conan remote and authenticate")
    @classmethod
    def _conan_push(cls, image_reference,  path, remote_name):
        subprocess.run(shlex.split(f'conan export {path} {image_reference}'))
        subprocess.run(shlex.split(f'conan upload {image_reference} -r {remote_name}'))


    @classmethod
    def create(cls, path, image_reference):
        conandata_path = os.path.join(path, cls.CONANDATA_FILE)
        conanfile_path = os.path.join(path, cls.CONANFILE)
        assert os.path.exists(conandata_path), f"No conandata at {conandata_path} "
        assert os.path.exists(conanfile_path), f"No conanfile at {conanfile_path}"

        conandata = ConanData(conandata_path)

        image = super().create(name=image_reference, admin_user=conandata._admin_user,
                               admin_password=conandata._admin_password)

        remote_url = image.remote
        remote_name = cls._resolve_remote_name(remote_url)
        cls._conan_push(image_reference, path, remote_name)

        return image


