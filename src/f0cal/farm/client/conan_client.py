import os
import sys
import logging

from conans.client.conan_api import Conan
from conans.model.ref import ConanFileReference
from conans.errors import ConanException

VENV_HOME = sys.prefix
LOG = logging.getLogger(__name__)

CONAN_REMOTE_NAME = 'f0cal_images'
#TODO TEMP URL SHOULD BE RELATIVE TO TOTAL URL
CONAN_URL = 'http://conan.f0cal.com'

class ConanClient:
    #TODO THIS SHOULD GET REPLACED WITH API KEY BASED AUTH
    USER = 'f0cal'
    PASSWORD = 'f0cal'

    @classmethod
    def set_conan_cache(cls):
        if sys.prefix == sys.base_prefix:
            LOG.warning('NOT USING F0CAL INSIDE ENV, SETTING CONAN CACHE TO USER HOME DIR INSTEAD OF VENV')
            return
        os.environ["CONAN_USER_HOME"] = VENV_HOME
    def _initialize_conan(self):
        remotes = self.conan.remote_list()
        if CONAN_REMOTE_NAME not in {x.name for x in remotes}:
            self.conan.remote_add(remote_name=CONAN_REMOTE_NAME, url=CONAN_URL)
        self._authenticate(self.USER, self.PASSWORD, CONAN_REMOTE_NAME)
    def __init__(self):
        self.set_conan_cache()
        self.conan = Conan()
        self._initialize_conan()

    def _authenticate(self, username, password, remote_name):
        self.conan.authenticate(name=username, password=password, remote_name=remote_name)



    def image_pull(self, name):
        ref = ConanFileReference.loads(name)
        self.conan.install_reference(ref, remote_name=CONAN_REMOTE_NAME)

    def image_push(self, name):
        self.conan.upload(name, remote_name=CONAN_REMOTE_NAME, all_packages=True)
