import ctypes
from collections import OrderedDict

class IviCError(BaseException):
    pass


def add_repeated_capability(cls, name, wrapper_class):
    """
    Use the Capitalize name in the original driver here, without an s,
    will be translated in a lower case name.
    """
    
    def get_repeated_name(self, ch_index):
        queried_name = ctypes.create_string_buffer(256)
        func_name = "Get" + name + "Name"
        self.call(func_name, self.visession, ch_index, 256, queried_name)
        return queried_name.value
    get_rep_name_func_name = 'get_' + name.lower() + '_name'
    setattr(cls, get_rep_name_func_name, get_repeated_name)
    
    def get_repeated_count(self):
        """
        Work around to avoid querying the attribute by id...
        """
        return self.__getattribute__(name.lower() + '_count')
        #func = self.__getattribute__(get_rep_name_func_name)
        #index = 0
        #while(True):
        #    index+=1
        #    try:
        #        func(index)
        #    except IviCError:#COMError:
        #        return index-1
    get_rep_count_func_name = 'get_' + name.lower() + '_count'
    setattr(cls, get_rep_count_func_name, get_repeated_count)
    
    attr_class_name = name.lower() + '_cls'
    cls._repeated_capabilities[name.lower()] = wrapper_class

class RepeatedCapability(object):
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.visession = parent.visession
        self.call = parent.call

class IviCWrapper(object):
    
    def __init__(self, session, address, simulate = False):
        self._session = session
        self.visession = ctypes.c_int()
        self.call('InitWithOptions',
                  address,
                  False,
                  False, 
                  'Simulate = ' + str(simulate).lower(),
                  ctypes.byref(self.visession))
        for name, wrapper_class in self._repeated_capabilities.items():
            dic = OrderedDict()
            setattr(self, name + 's', dic)
            get_rep_count_func_name = 'get_' + name.lower() + '_count'
            get_rep_name_func_name = 'get_' + name.lower() + '_name'
            func_count = self.__getattribute__(get_rep_count_func_name)
            func_name = self.__getattribute__(get_rep_name_func_name)
            for index in range(1, func_count()+1):
                repeated_name = func_name(index)
                dic[repeated_name] = wrapper_class(repeated_name, self)
            
    
    @classmethod  
    def _new_attr(cls, name, id, type_, multi_channel, multi_trace, read_only):
        """
        sets-up a new argument for the instrument
        """
        
        c_type = {"ViInt32":ctypes.c_int,
                  "ViReal64":ctypes.c_double,
                  "ViBoolean":ctypes.c_bool,
                  "ViString":ctypes.c_char_p}
            
        def getter(self):
            val = c_type[type_]()
            if type_ == "ViString":
                val = ctypes.create_string_buffer(256)
            if multi_channel:
                channel_name = self.name
            else:
                channel_name = ''
                if multi_trace:
                    channel_name = self.name
                else:
                    channel_name = ''
            try:
                self.call('GetAttribute'+type_,
                          self.visession,
                          channel_name,
                          id,
                          ctypes.byref(val))
            except IviCError:
                raise AttributeError('This property seems not to exist in this device')
            return val.value
        
        if read_only:
            setter = None
        else:
            def setter(self, val):
                if multi_channel:
                    channel_name = self.name
                else:
                    channel_name = ''
                    if multi_trace:
                        channel_name = self.name
                    else:
                        channel_name = ''
                val = c_type[type_](val)
                self.call('SetAttribute'+type_,
                          self.visession,
                          channel_name,
                          id,
                          val)
        if multi_channel:
            concerned_cls = cls._repeated_capabilities['channel']
        else:
            concerned_cls = cls
            if multi_trace:
                concerned_cls = cls._repeated_capabilities['trace']
            else:
                concerned_cls = cls
        setattr(concerned_cls, name, property(getter, setter))
        
        
    def call(self, funcname, *args):
        """
        appends the stupid 'tkafg3k_' to the function name and adds the
        arguments
        """
        
        func = self._session.__getattr__(self._session._name + '_' +\
                                              funcname)
        return_value = func(*args)
        if return_value:
            error_message = ctypes.create_string_buffer(256)
            self.call('error_message',
                      self.visession,
                      return_value, 
                      ctypes.byref(error_message))
            raise IviCError(error_message.value)
        
        
