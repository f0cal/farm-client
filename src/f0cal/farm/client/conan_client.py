import os
import sys
import logging

from conans.client.conan_api import Conan
from conans.model.ref import ConanFileReference
from conans.errors import ConanException

VENV_HOME = sys.prefix
LOG = logging.getLogger(__name__)

class ConanClient:
    #TODO THIS SHOULD GET REPLACED WITH API KEY BASED AUTH
    USER = 'f0cal'
    PASSWORD = 'f0cal'

    @classmethod
    def set_conan_env(cls):
        if sys.prefix == sys.base_prefix:
            LOG.warning('NOT USING F0CAL INSIDE ENV, SETTING CONAN CACHE TO USER HOME DIR INSTEAD OF VENV')
            return
        os.environ["CONAN_USER_HOME"] = VENV_HOME

    def __init__(self):
        self.set_conan_env()
        self.conan = Conan()
        
    def _remote_add(self, name, url):
        try:
            self.conan.remote_add(remote_name=name, url=url)
        except ConanException as e:
            if 'already exists' in e.args[0]:
                self.conan.remote_update(remote_name=name, url=url)
            else:
                raise
    def _authenticate(self, username, password, remote_name):
        self.conan.authenticate(name=username, password=password, remote_name=remote_name)

    def add_remote(self, name, cluster_url):
        url = f'{cluster_url}/conan/'
        self._remote_add(name, url)
        self._authenticate(self.USER, self.PASSWORD, name)

    def image_pull(self, name, remote_name):
        ref = ConanFileReference.loads(name)
        self.conan.install_reference(ref, remote_name=remote_name)

    def image_push(self, name, remote_name):
        self.conan.upload(name, remote_name=remote_name, all_packages=True)
