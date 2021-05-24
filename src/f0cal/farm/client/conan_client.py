import os
import sys
import logging

from conans.client.conan_api import Conan
from conans.model.ref import ConanFileReference
from conans.errors import ConanException
import f0cal.core

VENV_HOME = sys.prefix
LOG = logging.getLogger(__name__)

CONAN_REMOTE_NAME = 'f0cal_images'

CONAN_PATH = '/conan'

class ConanClient:
    USER = 'f0cal_user'

    @property
    def password(self):
        return f0cal.core.CORE.config["api"]["api_key"]
    @classmethod
    def set_conan_env(cls):
        if sys.prefix == sys.base_prefix:
            LOG.warning('NOT USING F0CAL INSIDE ENV, SETTING CONAN CACHE TO USER HOME DIR INSTEAD OF VENV')
            return
        os.environ["CONAN_USER_HOME"] = VENV_HOME
    def _initialize_conan(self):
        remotes = self.conan.remote_list()
        if CONAN_REMOTE_NAME not in {x.name for x in remotes}:
            api_url = f0cal.core.CORE.config["api"]["api_url"]
            conan_url = f'{api_url}{CONAN_PATH}'
            self.conan.remote_add(remote_name=CONAN_REMOTE_NAME, url=conan_url)
        self._authenticate(self.USER, self.PASSWORD, CONAN_REMOTE_NAME)
    def __init__(self, f0cal_base_url):
        self.set_conan_env()
        self.conan = Conan()
        self._initialize_conan()

    def _authenticate(self, username, password, remote_name):
        self.conan.authenticate(name=username, password=password, remote_name=remote_name)



    def image_pull(self, name):
        ref = ConanFileReference.loads(name)
        self.conan.install_reference(ref, remote_name=CONAN_REMOTE_NAME)

    def image_push(self, name):
        self.conan.upload(name, remote_name=CONAN_REMOTE_NAME, all_packages=True)
