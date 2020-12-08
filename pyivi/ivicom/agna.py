from pyivi.ivifactory import register_wrapper
from pyivi.ivicom import IviComWrapper
from pyivi.ivicom.ivicomwrapper import FieldsClass, \
                                       pick_from_session
from pyivi import choices
from pyivi.common import add_sc_fields_enum, \
                         ShortCut, \
                         add_sc_fields, \
                         Enum

from numpy import array
from collections import OrderedDict
from comtypes import COMError

class StimulusRange(FieldsClass):
    _pickup = [  'Center',
                 'ConfigureCenterSpan',
                 'ConfigureStartStop',
                 'Span',
                 'Start',
                 'Stop']

class Measurement(object):
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.session = parent.session.Measurements[name]
        
        pick_from_session(self, ['Create',
                                'DataToMemory',
                                'Delete',
                                'GetSParameter',
                                'Limit',
                                'Markers',
                                'QueryStatistics',
                                'SetSParameter',
                                'Smoothing',
                                'SmoothingAperture',
                                'Trace',
                                'TraceMath'])
    
    @property
    def format(self):
        return self.session.Format
    
    @format.setter
    def format(self, val):
        self.session.Format = val
        return val
    
    def fetch_complex(self):
        real_, imag_ = self.session.FetchComplex()
        return array(list(real_)) + 1j*array(list(imag_))
    
    def fetch_memory_complex(self):
        real_, imag_ = self.session.FetchMemoryComplex()
        return array(list(real_)) + 1j*array(list(imag_))
    
    def fetch_x(self):
        return array(list(self.session.FetchX()))
    
    def fetch_memory_formatted(self):
        return array(list(self.session.FetchMemoryFormatted()))
    
    def fetch_formatted(self):
        return array(list(self.session.FetchFormatted()))

class ShortCutNA(ShortCut):
    _channel_related_fields = [("if_bandwidth", "if_bandwidth"),
                               ("averaging", "averaging"),
                               ("averaging_factor", "averaging_factor"),
                               ("sweep_time", "sweep_time"),
                               ("sweep_type", "sweep_type")]
    
    _stimulus_range_fields = [("frequency_center", "center"),
                               ("span", "span"),
                               ("frequency_start", "start"),
                               ("frequency_stop", "stop")]
    
    _measurement_related_fields = [('format', 'format')]   
    
    _fields = []
    _ch_fields = [field[0] for field in _channel_related_fields]
    _ch_fields+= [field[0] for field in _stimulus_range_fields]
    _m_fields = [field[0] for field in _measurement_related_fields]
    _m_fields+= ['input_port', 'output_port']
    
    def __init__(self, parent):
        super(ShortCutNA, self).__init__(parent)
        self.channel_idx = 1
        self.channel_idxs = Enum(['select channel'] + list(parent.channels.keys()))
        self._measurement_idx = 1
        
        self.measurement_idx = 1
        self.measurement_idxs = Enum(['select measurement'] + \
                                     self.active_channel.measurements.keys())
        self.create_measurement()
    
    @property
    def measurement_idx(self):
        return self._measurement_idx
    
    @measurement_idx.setter
    def measurement_idx(self, val):
        self._measurement_idx = val
        try:
            self.input_port
        except COMError:
            self.create_measurement()
        return val
    
    @property
    def input_port(self):
       return list(self.active_measurement.get_s_parameter())[0] #casting as list may not be necessary
   
    @input_port.setter
    def input_port(self, val):
        self.active_measurement.set_s_parameter(val,
                                        self.output_port)
        return val
    
    @property
    def output_port(self):
        return list(self.active_measurement.get_s_parameter())[1] #casting as list may not be necessary
    
    @output_port.setter
    def output_port(self, val):
        self.active_measurement.set_s_parameter(
                                        self.input_port,
                                        val)
    
    @property
    def measurement_name(self):
        return list(self.active_channel.measurements.keys())[self.measurement_idx-1]
    
    @property
    def active_measurement(self):
        return self.active_channel.measurements[self.measurement_name]
    
    def clear_average(self):
        self.active_channel.clear_average()
        
    @property
    def channel_name(self):
        return list(self.parent.channels.keys())[self.channel_idx-1]

    @property
    def active_channel(self):
        return self.parent.channels[self.channel_name]
    
    def create_measurement(self, input_port=2, output_port=1):
        self.active_measurement.create(input_port, output_port)
    
    def fetch(self,format="formatted"):
        if format not in ("formatted","complex"):
            raise ValueError("Expected format either formatted or complex!")
        if format == "complex":
            y_curve = self.active_measurement.fetch_complex()
        else: 
            y_curve = self.active_measurement.fetch_formatted()
        x_curve = self.active_measurement.fetch_x()
        return x_curve, y_curve
    
    
    
add_sc_fields(ShortCutNA, 
              ShortCutNA._channel_related_fields, 
              'sc_active_channel')
add_sc_fields(ShortCutNA, 
              ShortCutNA._measurement_related_fields, 
              'sc_active_measurement')
add_sc_fields(ShortCutNA,
              ShortCutNA._stimulus_range_fields,
              'sc_active_stimulus_range')
add_sc_fields_enum(ShortCutNA, 'sweep_type', *choices.na_sweep_types._choices)

add_sc_fields_enum(ShortCutNA, 'format',  *choices.na_formats._choices)

class Channel(object):
    measurement_cls = Measurement
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.session = parent.session.Channels[name]
        
        self.stimulus_range = StimulusRange(self.session.StimulusRange, self)
        
        pick_from_session(self, ['AsynchronousTriggerSweep',
                                 'Averaging',
                                 'AveragingFactor',
                                 'CWFrequency',
                                 'ClearAverage',
                                 'Correction',
                                 'GetCorrectionArrays',
                                 'IFBandwidth',
                                 'Number',
                                 'Points',
                                 'PortExtension',
                                 'PortExtensionStatus',
                                 'Segment',
                                 'SetCorrectionArrays',
                                 'SourcePower',
                                 'SweepMode',
                                 'SweepTime',
                                 'SweepTimeAuto',
                                 'SweepType',
                                 'TriggerMode',
                                 'TriggerSweep'])
        self.measurements = OrderedDict()
        for meas_index in range(1, self.session.Measurements.Count+1):
            name = self.session.Measurements.Name(meas_index)
            self.measurements[name] = self.measurement_cls(name, self)

@register_wrapper('IVI-COM', 'AgNA')
class AgNA(IviComWrapper):
    _repeated_capabilities = {}
    channel_cls = Channel
    def __init__(self, *args, **kwds):
        super(AgNA, self).__init__(*args, **kwds)
        self.channels = OrderedDict()
        for channel_index in range(1, self.session.Channels.Count+1):
            name = self.session.Channels.Name(channel_index)
            self.channels[name] = self.channel_cls(name, self)
        self.sc = ShortCutNA(self)
        
    @property
    def sc_active_channel(self):
        return self.channels[self.sc.channel_name]
    
    @property
    def sc_active_measurement(self):
        return self.channels[self.sc.channel_name].\
                    measurements[self.sc.measurement_name]
    
    @property
    def sc_active_stimulus_range(self):
        return self.sc_active_channel.stimulus_range