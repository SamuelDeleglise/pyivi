#from model_utils import Choices #I don't want to import the whole django just for this
##===============================================================
##  Don't edit: This file should always be a straight copy of pyinstruments.choices 
##===============================================================

class Choices(list):
    def __init__(self, *args):
        self._choices = args
        for choice in args:
            setattr(self, choice, choice)
        super(Choices, self).__init__(zip(args, args))
        self._choice_dict = dict(self)

scope_acquisition_types = Choices( "normal",
                                   "peak_detect",
                                   "hi_res",
                                   "enveloppe",
                                   "average")

scope_sample_modes = Choices('real_time',
                            'equivalent_time')

spec_an_detector_types = Choices(   '',
                                    'auto_peak',
                                    'average',
                                    'max_peak',
                                    'min_peak',
                                    'sample',
                                    'rms')
                     
spec_an_trace_types = Choices('',
                              'clear_write',
                              'max_hold',
                              'min_hold',
                              'video_average',
                              'view',
                              'store')

scope_couplings = Choices("AC",
                   "DC",
                   "GND")

na_formats = Choices(   "log_mag", 
                        "lin_mag", 
                        "phase", 
                        "group_delay", 
                        "SWR",
                        "real",
                        "imag",
                        "polar", 
                        "smith",
                        "s_lin",
                        "s_log",
                        "s_complex",
                        "s_admittance",
                        "p_lin",
                        "p_log",
                        "u_phase",
                        "p_phase")

na_sweep_types = Choices('lin_frequency',
                          'log_frequency',
                          'segment',
                          'power',
                          'cw_time')

