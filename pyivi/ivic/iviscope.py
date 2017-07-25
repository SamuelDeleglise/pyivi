from pyivi.ivifactory import register_wrapper
from pyivi.ivic import IviCWrapper
from pyivi.ivic.ivicwrapper import RepeatedCapability, \
                                    add_repeated_capability
from pyivi.common import add_sc_fields_enum, \
                         ShortCut, \
                         add_sc_fields, \
                         Enum
from .definesiviscope import add_props
from pyivi import choices
from .ivi_defines import IVI_ATTR_CHANNEL_COUNT

import ctypes
from numpy import array, double, zeros, frombuffer, linspace

class ChannelScope(RepeatedCapability):
    def fetch_waveform(self):
        return self.parent.fetch_waveform(self.name)

    def read_waveform(self, timeout_ms = 10000):
        return self.parent.read_waveform(self.name, timeout_ms=timeout_ms)

class ShortCutScope(ShortCut):
    _channel_related_fields = [("ch_offset", "vertical_offset"),
                               ("ch_coupling", "vertical_coupling"),
                               ("ch_enabled", "channel_enabled"),
                               ("ch_input_impedance", "input_impedance"),
                               ("ch_input_frequency_max", "max_input_frequency"),
                               ("ch_range", "vertical_range")]
    _fields_direct = [("acquisition_type" ,"acquisition_type"),
               ("record_length", "horz_record_length"),
               ("time_per_record","horz_time_per_record"),
               ("sample_rate","horz_sample_rate"),
               ("number_of_averages","num_averages"),
               ("start_time","acquisition_start_time"),
               ("sample_mode","sample_mode")]
    
    _fields = [field[0] for field in _fields_direct]
    _ch_fields = [field[0] for field in _channel_related_fields]

    def __init__(self, parent):
        super(ShortCutScope, self).__init__(parent)
        self.channel_idx = 1
        self.channel_idxs = Enum(['select channel'] + parent.channels.keys())
        
    @property
    def channel_name(self):
        return self.parent.channels.keys()[self.channel_idx-1]

    def fetch(self):
        return self.parent.channels[self.channel_name].fetch_waveform()

add_sc_fields(ShortCutScope, ShortCutScope._fields_direct)
add_sc_fields(ShortCutScope,
              ShortCutScope._channel_related_fields,
              'sc_active_channel')
add_sc_fields_enum(ShortCutScope, 'ch_coupling', *choices.scope_couplings._choices)
add_sc_fields_enum(ShortCutScope, 'sample_mode', *choices.scope_sample_modes._choices)
add_sc_fields_enum(ShortCutScope, 'acquisition_type', *choices.scope_acquisition_types._choices)


@register_wrapper('IVI-C', 'IviScope')
class IviCScope(IviCWrapper):
    _repeated_capabilities = {}

    def __init__(self, *args, **kwds):
        super(IviCScope, self).__init__(*args, **kwds)
        self.sc = ShortCutScope(self)
    
    @property
    def sc_active_channel(self):
        return self.channels[self.sc.channel_name]
    def initiate_acquisition(self):
        self.call('InitiateAcquisition', self.visession)
    
    def read_waveform(self, channel=None, timeout_ms = 10000):
        """
        Same as fetch_waveform, but also initializes an acquisition
        """
        
        if not channel:
            channel = self.channels.keys()[0]
        chan = ctypes.c_char_p(channel)
        py_len = self.horz_record_length
        length = ctypes.c_int(py_len)
        timeout = ctypes.c_int(timeout_ms)
        arr = ctypes.c_double*py_len
        data = zeros(py_len, dtype = double)
        arr = arr.from_buffer_copy(data.data)
        actual_length = ctypes.c_int()
        initial_x = ctypes.c_double()
        x_increment = ctypes.c_double()
        self.call('ReadWaveform',
                  self.visession,
                  chan,
                  length,
                  timeout,
                  arr,
                  ctypes.byref(actual_length),
                  ctypes.byref(initial_x),
                  ctypes.byref(x_increment))
        numpy_y = frombuffer(arr, dtype = double)
        numpy_x = linspace(initial_x.value, x_increment.value*py_len, py_len, False)
        return numpy_x, numpy_y
    
    def fetch_waveform(self, channel=None):
        """
        Channel must be specified as a string
        """
        
        if not channel:
            channel = self.channels.keys()[0]
        chan = ctypes.c_char_p(channel)
        py_len = self.horz_record_length
        length = ctypes.c_int(py_len)
        arr = ctypes.c_double*py_len
        data = zeros(py_len, dtype = double)
        arr = arr.from_buffer_copy(data.data)
        actual_length = ctypes.c_int()
        initial_x = ctypes.c_double()
        x_increment = ctypes.c_double()
        self.call('FetchWaveform',
                  self.visession,
                  chan,
                  length,
                  arr,
                  ctypes.byref(actual_length),
                  ctypes.byref(initial_x),
                  ctypes.byref(x_increment))
        numpy_y = frombuffer(arr, dtype = double)
        numpy_x = linspace(initial_x.value, x_increment.value*py_len, py_len, False)
        return numpy_x, numpy_y
    
IviCScope._new_attr('channel_count', IVI_ATTR_CHANNEL_COUNT,'ViInt32',False,False,True)
add_repeated_capability(IviCScope, 'Channel', ChannelScope)
add_props(IviCScope)