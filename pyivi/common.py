
class ShortCut(object):
    def __init__(self, parent):
        self.parent = parent


def add_sc_fields(cls, list_of_pairs, origin = None):
    for shortcut, initial_name in list_of_pairs:
        def getter(self, init_name=initial_name, original_name=origin):
            if origin:
                orig = self.parent.__getattribute__(original_name)
            else:
                orig = self.parent
            return orig.__getattribute__(init_name)
        def setter(self, val, init_name=initial_name, original_name=origin):
            if origin:
                orig = self.parent.__getattribute__(original_name)
            else:
                orig = self.parent
            setattr(orig, init_name, val)
            return val
        setattr(cls, shortcut, property(getter, setter))




class Enum(object):
    def __init__(self, values):
        self._values = values
        for index, value in enumerate(values):
            setattr(self, value, index)
    
    def __repr__(self):
        return str([(index, value) for (index, value)\
                     in enumerate(self._values)])
    
    def __getitem__(self, index):
        return self._values[index]
        
def add_sc_fields_enum(cls, attr, *args):
    setattr(cls, attr + 's', Enum(args))