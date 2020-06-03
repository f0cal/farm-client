
from f0cal.services.central_api import models

class DbEntityParser:
    def __init__(self, models):
        self._dict = None
        self.entities = {}


    def _get_cls(self, name):
        proper_name = name.title().replace("_", "")
        try:
            cls = getattr(models, proper_name)
        except AttributeError:
            raise AttributeError(f"There is no such entity as a {name}")
        return cls

    def get_inst_by_name(self, _type, name):
        # TODO! THis does not look at the dict but instead the existing enittiies so the yaml file must be orders
        # correctly
        #
        for inst_name, inst in self.entities.values():
            if inst_name == name:
                return inst
        return None

    def _resolve_attrs(self, cls, attrs):
        columns = list(map(lambda x: x.name, cls.__table__.columns))
        relations = list(map(lambda x: x.key, inspect(cls).relationships))
        inst_attrs = {key: attrs[key] for key in attrs.keys() if key in columns or key in relations}
        for key, val in inst_attrs.items():
            try:
                cls = self._get_cls(key)
                inst = self.get_inst_by_name(cls, val)
                inst_attrs[key] = inst
            except AttributeError:
                if key == "supported_device_types":
                    cls = models.DeviceType
                    supported = []
                    for h in val:
                        inst = self.get_inst_by_name(cls, h)
                        supported.append(inst)
                    inst_attrs[key] = supported

        return inst_attrs

    def create_inst(self, cls, attrs):
        
        inst = self.get_inst_by_name(cls, attrs)
        if inst is not None:
            raise Exception(f"THIS PARSER DOES NOT ALLOW ENTITIES WITH THE SAME KEY. PLEASE RENAME {name}")
        inst_attrs = self._resolve_attrs(cls, attrs)
        inst = cls(**inst_attrs)
        self.entities['name'] = (inst)
        return inst

    def load_entities(self, entities_dict):
        for entity_type, entities in entities_dict.items():
            cls = self._get_cls(entity_type)
            name = entity
        
            insts = []
            for entity_attrs in entities:
                inst = self.create_inst(cls, entity_attrs)
            return self.entities