import re
from comtypes import COMError



def to_lower_case_notation(name):
    """
    see http://stackoverflow.com/questions/1175208/
    elegant-python-function-to-convert-camelcase-to-camel-case
    """
    
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def pick_from_session(self, propnames):
    for name in propnames:
        try:
            attr = self.session.__getattribute__(name)
        except COMError:
            pass
        else:
            def getter(self, attr=name):
                return self.session.__getattribute__(attr)
            def setter(self, val, attr=name):
                setattr(self.session, attr, val)
                return val
            
            setattr(self.__class__,
                to_lower_case_notation(name),
                property(getter, setter))

class FieldsClass(object):
    def __init__(self, session, parent):
        self.parent = parent
        self.session = session    
        pick_from_session(self, self._pickup)
                          
    

class IviComWrapper(object):
    def __init__(self, session, address, simulate = False):
        self.session = session
        self.session.Initialize(address,
                                      False,
                                      False,
                                      'Simulate = ' + str(simulate).lower())

        