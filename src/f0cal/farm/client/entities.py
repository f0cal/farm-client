from f0cal.farm.client.__codegen__.entities import *

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

