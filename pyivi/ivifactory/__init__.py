import sys
import os
import ctypes
from comtypes.client import CreateObject, GetModule
from comtypes import gen

sys.path.append(os.environ["IVIROOTDIR32"] + "/Bin/")
sys.path.append(os.environ["IVIROOTDIR32"] + "/Bin/Primary Interop Assemblies")
GetModule(os.environ["IVIROOTDIR32"] + "/Bin/" + "IviConfigServer.dll")
from comtypes.gen import IVICONFIGSERVERLib
DRIVER_SESSION = CreateObject("IviConfigServer.IviDriverSession",
             interface=gen.IVICONFIGSERVERLib.IIviDriverSession)
GetModule(os.environ["IVIROOTDIR32"] + "/Bin/" + "IviDriverTypeLib.dll")
from comtypes.gen.IviDriverLib import IIviDriver
GetModule(os.environ["IVIROOTDIR32"] + "/Bin/" + "IviSpecAnTypeLib.dll")
from comtypes.gen.IviSpecAnLib import IIviSpecAn 
GetModule(os.environ["IVIROOTDIR32"] + "/Bin/" + "IviScopeTypeLib.dll")
from comtypes.gen.IviScopeLib import IIviScope
GetModule(os.environ["IVIROOTDIR32"] + "/Bin/" + "IviFGenTypeLib.dll")
from comtypes.gen.IviFgenLib import IIviFgen
SPECIALIZED_APIS = {'IviScope': IIviScope,
                    'IviSpecAn': IIviSpecAn,
                    'IviFgen': IIviFgen}
try:
    GetModule(os.environ["IVIROOTDIR32"] + "/Bin/" + "AgNA.dll")
except WindowsError:
    pass
else:
    from comtypes.gen.AgilentNALib import IAgilentNA
    SPECIALIZED_APIS['AgNA'] = IAgilentNA
    
    
class NotSupportedError(ValueError):
    pass


class SoftwareModule(object):
    def __repr__(self):
        return self._soft_mod.Name
    
    def __init__(self, soft_mod):
        self._soft_mod = soft_mod
        self.c_apis = dict()
        self.com_apis = dict()
        for index in range(self._soft_mod.PublishedAPIs.Count):
            papi = self._soft_mod.PublishedAPIs.Item(index+1, 0, 0, "")
            if papi.Type == 'IVI-C':
                self.c_apis[papi.name] = papi
            if papi.Type == 'IVI-COM':
                self.com_apis[papi.name] = papi
        self.module_path = self._soft_mod.ModulePath
        
    def supported_instrument_models(self):
        return self._soft_mod.SupportedInstrumentModels.split(',')
    
    def specialized_instrument_type(self):
        specialized_apis = []
        general_apis = []
        
        for papi_name, papi in self.com_apis.items():
            if papi_name in SPECIALIZED_APIS:
                specialized_apis.append(papi_name)
            else:
                general_apis.append(papi_name)
        
        for papi_name, papi in self.c_apis.items():
            if papi_name in SPECIALIZED_APIS:
                specialized_apis.append(papi_name)
            else:
                general_apis.append(papi_name)
                
        specialized_apis = list(set(specialized_apis))
        general_apis = list(set(general_apis))
        if specialized_apis:
            return specialized_apis[0]
        return general_apis[0]
    
    def flavours(self):
        flavour_list = []
        if self.c_apis:
            flavour_list.append('IVI-C')
        if self.com_apis:
            flavour_list.append('IVI-COM')
        return flavour_list

    def get_session(self, flavour = None):
        """
        returns the most specialized API, with the required flavour
        (IVI-COM or IVI-C), or None if the flavour is not supported
        """
        
        specialized_apis_com = []
        general_apis_com = []
        specialized_apis_c = []
        general_apis_c = []
        for papi_name, papi in self.com_apis.items():
            if papi_name in SPECIALIZED_APIS:
                specialized_apis_com.append(papi)
            else:
                general_apis_com.append(papi)
                
        for papi_name, papi in self.c_apis.items():
            if papi_name in SPECIALIZED_APIS:
                specialized_apis_c.append(papi)
            else:
                general_apis_c.append(papi)
                
        if flavour == 'IVI-COM' or flavour == None:
            for api in specialized_apis_com:
                session = SESSION_FACTORY.\
                        CreateSession('pyivi_' + self._soft_mod.Name)
                interface = SPECIALIZED_APIS[api.Name]
                return (self._soft_mod.Name,
                        session.QueryInterface(interface),
                        api.Name,
                        'IVI-COM')
            for api in general_apis_com:
                session = SESSION_FACTORY.\
                        CreateSession('pyivi_' + self._soft_mod.Name)
                if self._soft_mod.Name in SPECIALIZED_APIS:
                    interface = SPECIALIZED_APIS[self._soft_mod.Name]
                else:
                    interface = IIviDriver
                return (self._soft_mod.Name,
                        session.QueryInterface(interface), 
                        api.Name,
                        'IVI-COM')

        if flavour == 'IVI-C' or flavour == None:
            ok = False
            for api in specialized_apis_c:
                return (self._soft_mod.Name,
                        ctypes.windll.LoadLibrary(self.module_path),
                        api.Name,
                        'IVI-C')
            for api in general_apis_c:
                return (self._soft_mod.Name,
                        ctypes.windll.LoadLibrary(self.module_path),
                        api.Name,
                        'IVI-C')
        if flavour:
            raise NotSupportedError('model not supported with flavour '\
                                     + flavour)
        else:
            raise NotSupportedError('no software module supports this model')
        
        
class Session(object):
    def __repr__(self):
        return self._session.Name
    
    def __init__(self, session):
        self._session = session
        
class LogicalName(object):
    def __repr__(self):
        return self._logical_name.Name
    
    def __init__(self, logical_name):
        self._logical_name = logical_name

class ConfigStore(object):
    def __init__(self):
        self._config_store = CreateObject("IviConfigServer.IviConfigStore",
                            interface=gen.IVICONFIGSERVERLib.\
                                                        IIviConfigStore)
        self._config_store.Deserialize(self._config_store.MasterLocation)
        self.software_modules = dict()
        for index in range(self._config_store.SoftwareModules.count):
            self.software_modules[self._config_store.SoftwareModules[index+1].Name]\
             = SoftwareModule(self._config_store.SoftwareModules[index+1])
        self._sessions = dict()
        for index in range(self._config_store.Sessions.count):
            self._sessions[self._config_store.Sessions[index+1].Name]\
             = Session(self._config_store.Sessions[index+1])
        self._logical_names = dict()
        for index in range(self._config_store.LogicalNames.count):
            self._logical_names[self._config_store.LogicalNames[index+1].Name]\
             = LogicalName(self._config_store.LogicalNames[index+1])
        
    def _add_required_sessions(self):
        for soft_mod_name, soft_mod in self.software_modules.items():
            required_name = 'pyivi_' + soft_mod_name
            if required_name not in self._logical_names.keys():
                new_log_name = CreateObject("IviConfigServer.IviLogicalName",
                     interface=gen.IVICONFIGSERVERLib.IIviLogicalName)
                new_log_name.Name = required_name
                if required_name not in self._sessions.keys():
                    new_session = CreateObject("IviConfigServer.IviDriverSession")
                    new_session.QueryInterface(gen.IVICONFIGSERVERLib.IIviDriverSession)
                    new_session.Name = required_name
                    new_session.SoftwareModule = soft_mod._soft_mod
                    self._add_session(new_session)
                else:
                    new_session = self._sessions[required_name]._session
                new_log_name.Session = new_session
                self._add_logical_name(new_log_name)
        self._config_store.Serialize(self._config_store.MasterLocation)
    
    def _add_logical_name(self, log_name):
        self._config_store.LogicalNames.Add(log_name)
    
    def _add_session(self, session):
        self._config_store.Sessions.Add(session)
        
CONFIG_STORE = ConfigStore()
CONFIG_STORE._add_required_sessions()
GetModule(os.environ["IVIROOTDIR32"] + "/Bin/" +"IviSessionFactory.dll")
SESSION_FACTORY = CreateObject("IviSessionFactory.IviSessionFactory",
        interface=gen.IVISESSIONFACTORYLib.IIviSessionFactory)


def supporting_modules(model):
    supporting = []
    for soft_mod_name, soft_mod in CONFIG_STORE.software_modules.items():
         if model in soft_mod.supported_instrument_models():
             supporting.append(soft_mod)
    return supporting

def get_model_name(address):
    """Physically queries the instrument model at the given address"""
    
    from visa import VisaIOError
    import visa
    model = "no device"
    try:
        rm = visa.ResourceManager()
        instr = rm.open_resource(str(address))
        timeout = instr.timeout
    except VisaIOError:
        print("instrument at address " + str(address) + " didn't reply in "
                                                        "time...")
    else:
        try:   
            instr.timeout = 100  # in ms
            ret = instr.query("*IDN?")
        except (VisaIOError, TypeError):
            print("instrument at address " + \
                address + \
                " didn't reply in time...")
        else:
            model = ret.split(",")[1]
            model = model.replace(' ', '')
        finally:
            instr.timeout = timeout
            instr.close()
    return model

def register_wrapper(flavour, instrument_type):
    """
    use this decorator to register the wrapper class for an instrument type
    """
    
    def func(cls):
        WRAPPERS[flavour][instrument_type] = cls
        return cls
    return func
WRAPPERS = dict()
WRAPPERS["IVI-C"] = dict()
WRAPPERS["IVI-COM"] = dict()
def ivi_instrument(address, flavour = None, simulate = False, model = None):
    """
    top-level factory-function.
    
    address: the VISA address of the instrument (ex:USB0:XXXX:1)
    flavour: IVI-C or IVI-COM
    model: model string, if not specified, will query it.
    simulate: boolean, should the instrument be simulated ?
    
    
    Returns the specialized wrapper class if the supporting module
    has a "specialized API" (IviScope, for instance) or the generic wrapper
    if only Driver API exists.
    """
    
    if not model:
        model = get_model_name(address)
    modules = supporting_modules(model)
    for module in modules:
        try:
            (name,
             session, 
             instrument_type, 
             flavour) = module.get_session(flavour)
            session._name = name
        except NotSupportedError:
            pass
        else:
            if instrument_type=='IviDriver':
                return WRAPPERS[flavour][name](session, 
                                               address, 
                                               simulate)
            return WRAPPERS[flavour][instrument_type](session, 
                                               address, 
                                               simulate)
