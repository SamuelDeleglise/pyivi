===============================================
pyivi: python interface for IVI-instruments
===============================================
        

What is it
==========

**pyivi** is a thin wrapper layer that is aware of all IVI-drivers
installed on a windows computer and can wrap them to interface remote 
instruments from python modules or scripts. Since IVI-COM drivers are not 
always provided, IVI-C is also supported.
 
The specificity of pyivi is that it is **not** re-implementing the IVI interface
using lower-level communication protocols, but rather directly communicating 
with the installed IVI-drivers. The main advantage of this approach is that
all the boring code that needs to be written for every new instrument is 
done by the instrument's manufacturer (99% of the instruments come with either 
IVI-C or IVI-COM drivers). The drawback is that pyivi is not cross-platform
and needs to run on a windows computer.


Step-by-step communication with a spectrum analyzer:
====================================================

A good example is better than 10000 words, so let's try and install a new
Agilent MXA N9020A Spectrum analyzer. If you don't have 20 000 $ to spend just 
for the sake of testing pyivi, that's OK, IVI drivers come with a simulation 
feature. We'll go step-by-step to the point where we can communicate with our
simulated spectrum analyzer.

1/ Install pyivi using the windows installer below.

2/ Install the IVI-driver for the MXA N9020A from Agilent's website (you might
have to create an account for this... ;-/)
http://www.home.agilent.com/agilent/software.jspx?ckey=2044474&lc=eng&cc=US&nid=-33932.536910861&id=2044474
If this is the first IVI-driver you have been installing, you will be asked
to install the IVI-shared components as well. They can be found for free
either from National Instruments or directly from the IVI foundation website:
http://www.ivifoundation.org/shared_components/

3/ Open your favorite python interpreter and look at the IVI software_modules
installed on your computer ::

		import pyivi
		pyivi.software_modules
		
You should see the software module AgXSan that was just installed. This module 
provides at the same time an IVI-C and an IVI-COM interface. Every time a new
IVI software module is installed it will appear in this list.

4/ Create a connection to a virtual N9020A instrument::
		
		comspecan = pyivi.ivi_instrument('dummy_address', model='N9020A', simulate=True)

In the case where you would have a real instrument connected at address 
'USB0::12345678::INSTR', the following code would have been enough::
		
		comspecan = pyivi.ivi_instrument('USB0::12345678::INSTR')

The model would have been queried directly using the IDN? command.
By default, the instrument uses the IVI-COM interface, but we can
ask for the IVI-C interface using the appropriate keyword argument::
		
		cspecan = ivi_instrument('dummy_address', flavour='IVI-C', model='N9020A', simulate=True)
	
That's it! You can now browse through the attributes and functions of 
the instrument.

If you have tried both flavours of the driver, you have noticed that some attributes
are not accessed in the same way, for instance, to set the measurement bandwidth to 10 kHz, one would write::

		cspecan.resolution_bandwidth = 10000 # IVI-C interface
		comspecan.sweep_coupling.resolution_bandwidth = 10000 # IVI-COM interface

Of course, that's not very nice for us because, mostly, we will be using one or the other versions 
of the drivers interface because it is the only one available. Moreover, some functions are quite cumbersome to locate
for instance, with trace-related capabilities. For this reason, shortcuts commands, identical for IVI-C and IVI-COM 
interfaces have been added:

5/ Using shortcut commands (on IVI-C or IVI-COM drivers)::

		cspecan.sc.trace_idx = 2 # all the manipulation will be performed on 'Trace2'
		cspecan.sc.fetch() # Fetches the simulated trace
		
Supported IVI-interfaces:
=========================
In the current versions, the following IVI apis are supported:
	- IviScope (IVI-C, IVI-COM)
	- IviSpecAn (IVI-C, IVI-COM)
	- IviFGen (IVI-C)

The software module AgNA to control Agilent Network analyzers is also supported via the COM api.

Tested already on the following IVI software modules:
=====================================================
tktds1k2k,
tkafg3k,
AgSAn,
Ag34410,
ww257x,
lcscope,
AgInfiniiVision,
AgM933x,
TekScope,
AgilentSAnBasic,
AgN57xx,
Tkdpo2k3k4k,
Ag532xx,
AgNA,
AgXSAn,
 


Dependencies
============
  - comtypes (for communication with the IVI-configuration store and IVI-COM drivers)
  - ctypes (for communication with IVI-C drivers)