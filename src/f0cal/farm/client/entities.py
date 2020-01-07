from f0cal.farm.client.__codegen__.entities import *
import urllib
import os
import shlex
from time import sleep, time

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


    def _connect_ssh(self, connection_args):
        ssh_bin = '/usr/bin/ssh'
        connection_args = self._format_ssh_args(connection_args)
        print('*'*80)
        print('Starting an SSH session with your instance. Press CTRL+d to exit')
        print('*'*80)
        os.execvp(ssh_bin, connection_args)
    def _format_ssh_args(self, connection_args):
        ip , port = self._get_url()
        connection_args = ['ssh'] + connection_args + [f'f0cal@{ip}']
        if port:
            connection_args = connection_args + ['-p', f'{port}']
        return connection_args
    def _get_url(self):
        ip = self.ip
        if ip is None:
            print('This instance does not have an ip configured yet. Are you sure its ready?')
        parts = urllib.parse.urlparse(ip)
        return parts.hostname, parts.port
    def destroy(self):
        return self.stop()

    def stop(self):
        print('Stopping instance')
        return self._do_verb('stop', {})