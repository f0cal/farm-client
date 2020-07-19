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
    def connect(self, connection_type, connection_args):
        if not self.status == 'ready':
            print('The instance is not ready yet')
            exit(1)
        _fn = getattr(self, f'_connect_{connection_type}', None)
        if not _fn:
            print(f'{connection_type} connections not supported')
            exit(1)
        print((connection_args))
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

    def send_scp(self, source, destination, send_args):
        scp_bin = '/usr/bin/scp'
        send_args = self._format_send_args(source, destination, send_args)
        print('*'*80)
        print('Sending your file(s)')
        print('*' * 80)
        subprocess.call([scp_bin] + send_args)

    def get_scp(self, source, destination, get_args):
        scp_bin = '/usr/bin/scp'
        get_args = self._format_get_args(source, destination, get_args)
        print('*' * 80)
        print('Getting your file(s)')
        print('*' * 80)
        subprocess.call([scp_bin] + get_args)

    def _format_send_args(self, source, destination, send_args):
        user = self._get_user()
        ip, port = self._get_url()
        if port:
            send_args = ['-P', f'{port}'] + send_args
        send_args = send_args + [source] + [f'{user}@{ip}:{destination}']
        return send_args

    def _format_get_args(self, source, destination, get_args):
        user = self._get_user()
        ip, port = self._get_url()
        if port:
            get_args = ['-P', f'{port}'] + get_args
        get_args = get_args + [f'{user}@{ip}:{source}'] + [destination]
        return get_args

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
        print(str(parts.port))
        return parts.hostname, parts.port



