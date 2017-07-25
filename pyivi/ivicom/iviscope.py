from pyivi.ivifactory import register_wrapper
from pyivi.ivicom import IviComWrapper
from pyivi.ivicom.ivicomwrapper import  FieldsClass, \
                                        pick_from_session
from pyivi.common import add_sc_fields_enum, \
                         ShortCut, \
                         add_sc_fields, \
                         Enum
from pyivi import choices
                         
from collections import OrderedDict
from numpy import array, double, linspace

class Channel(object):
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.session = parent.session.Channels[name]
        
        pick_from_session(self, ['Configure',
                                 'ConfigureCharacteristics',
                                 'Coupling',
                                 'Enabled',
                                 'InputFrequencyMax',
                                 'InputImpedance',
                                 'Offset',
                                 'ProbeAttenuation',
                                 'ProbeSense',
                                 'Range'])
        
class Measurement(object):
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.session = parent.session.Measurements[name]
        
        pick_from_session(self, ['FetchWaveformMeasurement',
                                 'FetchWaveformMinMax',
                                 'ReadWaveform',
                                 'ReadWaveformMeasurement',
                                 'ReadWaveformMinMax'])

    def fetch_waveform(self):
        y_trace, initial_x, x_increment = self.session.FetchWaveform()
        y_trace = array(list(y_trace))
        x_trace = linspace(initial_x, 
                           x_increment*len(y_trace), 
                           len(y_trace), 
                           False)
        return x_trace, y_trace
        
class Trigger(FieldsClass):
    _pickup = ['AcLine',
                 'AddRef',
                 'Configure',
                 'Continuous',
                 'Coupling',
                 'Edge',
                 'Glitch',
                 'Holdoff',
                 'Level',
                 'Modifier',
                 'Release',
                 'Runt',
                 'Source',
                 'TV',
                 'Type',
                 'Width']
    
class DriverOperation(FieldsClass):
    _pickup = ['Cache',
             'ClearInterchangeWarnings',
             'DriverSetup',
             'GetNextCoercionRecord',
             'GetNextInterchangeWarning',
             'InterchangeCheck',
             'InvalidateAllAttributes',
             'IoResourceDescriptor',
             'LogicalName',
             'QueryInstrumentStatus',
             'RangeCheck',
             'RecordCoercions',
             'Release',
             'ResetInterchangeCheck',
             'Simulate']

class ReferenceLevel(FieldsClass):
    _pickup = [  'Configure',
                 'High',
                 'Low',
                 'Mid']

#class Measurements(FieldsClass):
#    _pickup = [  'Abort',
#                 'AutoSetup',
#                 'Count',
#                 'Initiate',
#                 'IsWaveformElementInvalid',
#                 'Item',
#                 'Name',
#                 'Status']
class Identity(FieldsClass):
    _pickup = [  'AddRef',
                 'Description',
                 'GroupCapabilities',
                 'Identifier',
                 'InstrumentFirmwareRevision',
                 'InstrumentManufacturer',
                 'InstrumentModel',
                 'Release',
                 'Revision',
                 'SpecificationMajorVersion',
                 'SpecificationMinorVersion',
                 'SupportedInstrumentModels',
                 'Vendor']

class Acquisition(FieldsClass):
    _pickup = [ 'AddRef',
                'ConfigureRecord',
                'Interpolation',
                'NumberOfAverages',
                'NumberOfEnvelopes',
                'NumberOfPointsMin',
                'RecordLength',
                'Release',
                'SampleMode',
                'SampleRate',
                'StartTime',
                'TimePerRecord',
                'Type']

class ShortCutScope(ShortCut):
    _acquisition_fields = [("record_length", "record_length"),
                           ("time_per_record","time_per_record"),
                           ("sample_rate","sample_rate"),
                           ("number_of_averages","number_of_averages"),
                           ("start_time","start_time"),
                           ("sample_mode","sample_mode"),
                           ("acquisition_type", "type")]
    
    _channel_related_fields = [("ch_enabled", "enabled"),
                               ("ch_coupling", "coupling"),
                               ("ch_offset", "offset"),
                               ("ch_range", "range"),
                               ("ch_input_impedance", "input_impedance"),
                               ("ch_input_frequency_max", "input_frequency_max")]
    
    _fields = [field[0] for field in _acquisition_fields]
    _ch_fields = [field[0] for field in _channel_related_fields]                           
    
    def __init__(self, parent):
        super(ShortCutScope, self).__init__(parent)
        self.channel_idx = 1
        self.channel_idxs = Enum(['select channel'] + parent.channels.keys())
    @property
    def channel_name(self):
        return self.parent.channels.keys()[self.channel_idx-1]
    
    def fetch(self):
        return self.parent.measurements[self.channel_name].fetch_waveform()

add_sc_fields(ShortCutScope, ShortCutScope._acquisition_fields, 'acquisition')
add_sc_fields(ShortCutScope, 
              ShortCutScope._channel_related_fields,
              'sc_active_channel')
add_sc_fields_enum(ShortCutScope, 'ch_coupling', *choices.scope_couplings._choices)
add_sc_fields_enum(ShortCutScope, 'sample_mode', *choices.scope_sample_modes._choices)
add_sc_fields_enum(ShortCutScope, 'acquisition_type', *choices.scope_acquisition_types._choices)


@register_wrapper('IVI-COM', 'IviScope')
class IviComScope(IviComWrapper):
    _repeated_capabilities = {}
    measurement_cls = Measurement
    channel_cls = Channel
    def __init__(self, *args, **kwds):
        super(IviComScope, self).__init__(*args, **kwds)
        self.trigger = Trigger(self.session.Trigger, self)
        self.driver_operation = DriverOperation(self.session.DriverOperation, self)
        self.reference_level = ReferenceLevel(self.session.ReferenceLevel, self)
        #self.measurements = Measurements(self.session.Measurements, self)
        self.identity = Identity(self.session.Identity, self)
        self.acquisition = Acquisition(self.session.Acquisition, self)
        self.channels = OrderedDict()
        for channel_index in range(1, self.session.Channels.Count+1):
            name = self.session.Channels.Name(channel_index)
            self.channels[name] = self.channel_cls(name, self)
        self.measurements = OrderedDict()
        for meas_index in range(1, self.session.Measurements.Count+1):
            name = self.session.Measurements.Name(meas_index)
            self.measurements[name] = self.measurement_cls(name, self)
            
        self.sc = ShortCutScope(self)
        
    @property
    def sc_active_channel(self):
        return self.channels[self.sc.channel_name]