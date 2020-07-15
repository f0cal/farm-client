from conans.client.conan_api import Conan
from conans.model.ref import ConanFileReference
from conans.errors import ConanException
class ConanClient:
    #TODO THIS SHOULD GET REPLACED WITH API KEY BASED AUTH
    USER = 'f0cal'
    PASSWORD = 'f0cal'

    def __init__(self):
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
