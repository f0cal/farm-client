from builtins import super

from f0cal.farm.client.__codegen__.entities import *
from f0cal.farm.client.api_client import DeviceFarmApi
import subprocess
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
    def connect(self, connection_type, connection_args, instance_name):
        if not self.status == 'ready':
            print('The instance is not ready yet')
            exit(1)
        _fn = getattr(self, f'_connect_{connection_type}', None)
        if not _fn:
            print(f'{connection_type} connections not supported')
            exit(1)
        return _fn(connection_args, instance_name)

    def destroy(self):
        return self.stop()

    def stop(self):
        print('Stopping instance')
        return self._do_verb('stop', {})

    def _connect_ssh(self, connection_args, instance_name):
        ssh_bin = '/usr/bin/ssh'
        connection_args = self._format_ssh_args(connection_args)
        print('*'*80)
        print(f'Starting an SSH session with instance {instance_name}. Press CTRL+d to exit')
        print('*' * 80)
        os.execvp(ssh_bin, connection_args)

    def _connect_scp(self, connection_args, instance_name):
        scp_bin = '/usr/bin/scp'
        connection_args = self._format_scp_args(connection_args, instance_name)
        print('*' * 80)
        print(f'Copying your file(s) to/from instance {instance_name}')
        print('*' * 80)
        subprocess.call([scp_bin] + connection_args)

    def get_scp(self, source, destination, get_args):
        scp_bin = '/usr/bin/scp'
        get_args = self._format_get_args(source, destination, get_args)
        print('*' * 80)
        print('Getting your file(s)')
        print('*' * 80)
        subprocess.call([scp_bin] + get_args)

    def _format_scp_args(self, connection_args, instance_name):
        user = self._get_user()
        ip, port = self._get_url()
        if port:
            connection_args = ['-P', f'{port}'] + connection_args
        connection_args = [f'{user}@{ip}' + arg[len(instance_name):] if arg.startswith(f'{instance_name}:')
                           else arg for arg in connection_args]
        return connection_args

    def _format_ssh_args(self, connection_args):
        user = self._get_user()
        ip , port = self._get_url()
        if port:
            connection_args = ['-p', f'{port}'] + connection_args
        connection_args = ['ssh']+ [f'{user}@{ip}'] + connection_args
        return connection_args

    def _get_user(self):
        try:
            image_id = self.image_id
            api_key = f0cal.CORE.config["api"].get("api_key")
            api_url = f0cal.CORE.config["api"]["api_url"]
            client = DeviceFarmApi(api_url, api_key)
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



