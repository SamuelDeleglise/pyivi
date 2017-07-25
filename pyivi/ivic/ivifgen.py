from pyivi.ivifactory import register_wrapper
from pyivi.ivic import IviCWrapper
from pyivi.ivic.ivicwrapper import RepeatedCapability, \
                                   add_repeated_capability
from pyivi.common import add_sc_fields_enum, \
                         ShortCut, \
                         add_sc_fields
from .definesivifgen import add_props

import ctypes
from numpy import array, double

class ChannelFgen(RepeatedCapability):
    pass


class ShortCutFreqGen(ShortCut):
    _fields = [("create_arb_waveform", "create_arb_waveform"),
               ('output_mode', 'output_mode'),
               ('operation_mode', 'operation_mode'),
               ('arb_sample_rate', 'arb_sample_rate')]
    
    _channel_related_fields = [("output_enabled", "output_enabled"),
                               ("frequency", "func_frequency"),
                               ("amplitude", "func_amplitude"),
                               ("offset", "func_dc_offset"),
                               ("start_phase", "func_start_phase"),
                               ("duty_cycle_high", "func_duty_cycle_high"),
                               ("waveform", "func_waveform"),
                               ("arb_frequency", "arb_frequency"),
                               ("arb_gain", "arb_gain"), 
                               ("arb_waveform_handle", "arb_waveform_handle"),
                               ("arb_sequence_handle", "arb_sequence_handle")]
    
    def __init__(self, parent):
        super(ShortCutFreqGen, self).__init__(parent)
        self.channel_idx = 1
        
    @property
    def channel_name(self):
        return self.parent.channels.keys()[self.channel_idx-1]


add_sc_fields(ShortCutFreqGen, 
              ShortCutFreqGen._fields)
add_sc_fields(ShortCutFreqGen, 
              ShortCutFreqGen._channel_related_fields,
              'sc_active_channel')
add_sc_fields_enum(ShortCutFreqGen, 'output_mode', 'func', 'arb', 'seq')
add_sc_fields_enum(ShortCutFreqGen, 'operation_mode', 'continuous', 'burst')

@register_wrapper('IVI-C', 'IviFgen')
class IviCFGen(IviCWrapper):
    _repeated_capabilities = {}
    
    def __init__(self, *args, **kwds):
        super(IviCFGen, self).__init__(*args, **kwds)
        self.sc = ShortCutFreqGen(self)
    
    @property
    def sc_active_channel(self):
        return self.channels[self.sc.channel_name]    
        
    def create_arb_waveform(self, waveform):
        """
        waveform is a numpy array, with values normalized between 0 and 1.
        Returns the integer handle of the created waveform.
        """

        waveform = array(waveform)
        
        if waveform.dtype != double:
            waveform = waveform.astype(dtype=double, casting='safe')
        
        length = len(waveform)
        c_array = ctypes.c_double*length
        c_array = c_array.from_buffer(waveform.data)
        handle = ctypes.c_int()
        
        self.call('CreateArbWaveform',
                  self.visession,
                  length,
                  c_array,
                  ctypes.byref(handle))
        
        return handle.value
    
    def get_channel_name(self, ch_index):
        name = ctypes.create_string_buffer(256)
        self.call("GetChannelName", self.visession, ch_index, 256, name)
        return name.value
    
add_repeated_capability(IviCFGen, 'Channel', ChannelFgen)
add_props(IviCFGen)