from f0cal.farm.client.__codegen__.entities import *
import urllib
import os
import shlex

import time
class Instance(Instance):
    @classmethod
    def create(cls, wait=False, wait_time=5, **data):
        inst = super().create(**data)

        # if wait:
        #     timeout = time() + wait_time * 60
        #     while device_data['status'] != 'ready':
        #         device_data = api.get_instance(device_data['id'])
        #         if device_data['status'] == 'error':
        #             print(f'There was an error start vm instance {device_data["id"]} please contact F0cal')
        #             exit(1)
        #         # Todo check for change
        #         device_config.write(device_data)
        #         print('Waiting for device to become available')
        #         if time() > timeout:
        #             print(f"Error waited {wait_time} minutes but device still not ready")
        #             exit(1)
        #         sleep(5)
        #     print(f'Device ready')
        return inst

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