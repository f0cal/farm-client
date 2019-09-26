from .api_client import DeviceFarmApi


class NoSuchItemException(Exception):
    pass


class Entity:
    CLIENT = DeviceFarmApi(None, None)
    NOUN = None

    def set_attr(self, key, val):
        # TODO Resolve related enities here
        self.__setattr__(key, val)

    @classmethod
    def _from_response(cls, response):
        inst = cls()
        for key, val in response.items():
            inst.set_attr(key, val)
        return inst

    @classmethod
    def create(cls, data):
        response = cls.CLIENT.create(cls.NOUN, data)
        return cls._from_response( response)

    @classmethod
    def list(cls):
        response = cls.CLIENT.list(cls.NOUN)
        return [cls._from_response(i) for i in response]

    @classmethod
    def from_id(cls, _id):
        response = cls.CLIENT.retrieve(cls.NOUN, _id)
        return cls._from_response( response)

    @classmethod
    def from_name(cls, name):
        # TODO this quite inefficient right now and lists all items available to the user and assumes there is a
        #  unique contraints on the name within that list

        all_items = cls.CLIENT.list(cls.NOUN)
        # TODO should use pandas or something here
        for i in all_items:
            if i.get('name') == name:
                return cls._from_response( i)
        raise NoSuchItemException(f'There is no {cls.NOUN} named {name}')

    def do_verb(self, verb, data):
        response = self.CLIENT.action(self.noun, self.id, verb, data)
