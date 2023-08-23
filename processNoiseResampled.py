# run: python processNoiseResampled.py -i /data/exp/IceCube/2021/unbiased/surface/V6/sae_data/SAE_data_1349**_1_IT.i3.gz -f "1349_60000" -o "output_snr_1349_60000.i3"

#This script filters the soft triggered events; filters the non-cascaded mode; applies the module "RemoveTAXIArtifacts"; applies the module "TraceResampler"; aplies some other modules; calculates the SNR and creates a key with a list of 3 values for each frame (the 3 values correspond one to each antenna).
#Its output is an I3file.


import numpy as np
import matplotlib.pyplot as plt

from I3Tray import I3Tray
from icecube import icetray, dataio, dataclasses, radcube
from icecube.icetray import I3Units

import os
import argparse


parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-i", "--inputfile", nargs='+', default=None, help="What input file (.i3) do you want to use?")
parser.add_argument("-g", "--gcdfile", default="/data/user/acoleman/datasets/gcd-files/GCD-AntennaSurvey_recent.i3.gz", help="What GCD file (.i3) do you want to use? GCD files contain information on detector geometry and calibration")
parser.add_argument("-d", '--directory', default="/home/acaviedes/work/analysis/results/save", help="Where to save the results")
parser.add_argument("-f", '--folder', default=None, help="Name of the directory to save the output i3file and other specific results")
parser.add_argument("-o", "--outputfile", default=None, help="Name of the output i3 file")
args = parser.parse_args()


#assert os.path.isfile(args.inputfile), "{} isn't a file!".format(args.inputfile)
#this line doesn't work for multiple i3 files.

tray = I3Tray()

tray.AddModule("I3Reader", "reader", 
         FilenameList = [args.gcdfile] + args.inputfile)



def select_soft(frame):
    trigger_info = frame['SurfaceFilters']

    return trigger_info["soft_flag"].condition_passed

tray.Add(select_soft, "select_soft",
         streams=[icetray.I3Frame.DAQ])



def non_cascade(frame):
    RadioTraceLength = frame['RadioTraceLength']    
    if RadioTraceLength.value == 1024:
        return True
    else:
        return False    

tray.Add(non_cascade, "select_non_cascade",
         streams=[icetray.I3Frame.DAQ])



tray.AddModule(radcube.modules.RemoveTAXIArtifacts, "artifactremover",
         InputName="RadioTAXIWaveform",
         OutputName="ArtifactsRemoved"
         )

tray.AddModule("TraceResampler", "Resampler",  #this module runs on Q frames by default
               InputName="ArtifactsRemoved",
               OutputName="ResampledMap",
               ResampledBinning=0.25 ##
              )


tray.AddModule("I3NullSplitter","splitter",
               SubEventStreamName="RadioEvent"
               )

electronics_service = radcube.defaults.CreateDefaultElectronicsResponse(tray)

tray.AddModule("PedestalRemover", "pedestalremover",
                InputName="ArtifactsRemoved",
                OutputName="PedestalRemoved",
                ElectronicsResponse=electronics_service,
                ConvertToVoltage=True
                )

tray.AddModule("BandpassFilter", "filter",
               InputName="PedestalRemoved",
               OutputName="FilteredMap",
               FilterType=radcube.eBox,
               FilterLimits=[80*I3Units.megahertz, 300*I3Units.megahertz] # note the use of I3Units!
               )

tray.AddModule("ElectronicResponseRemover", "elecremover",
               InputName="FilteredMap",
               OutputName="DeconvolvedWaveforms",
               ElectronicsResponse=electronics_service,
               )




class SNRModule(icetray.I3Module): #Creates a list of the SNR values in each event.
  def __init__(self,ctx):
    icetray.I3Module.__init__(self,ctx)       
    self.inputName = ""
    self.AddParameter("InputName", "Input antenna data map", self.inputName)
  def Configure(self):
    self.inputName = self.GetParameter("InputName")
  def Physics(self,frame):
    if frame.Has(self.inputName):
      antDataMap = frame[self.inputName]     
      SNR = dataclasses.I3VectorFloat()
      for iant, antkey in enumerate(antDataMap.keys()):
        channelMap = antDataMap[antkey]
        channelPeakAmp = []
        channelSNR = []
        for ichannel, chkey in enumerate(channelMap.keys()): 
          fft = channelMap[ichannel].GetFFTData() 
          timeSeries = fft.GetTimeSeries()          
          peak = dataclasses.fft.GetHilbertPeak(timeSeries) / I3Units.mV          
          snrValue = radcube.GetSNR(timeSeries)
          channelPeakAmp.append(peak)
          channelSNR.append(snrValue)        
        maxInd = channelPeakAmp.index(max(channelPeakAmp))
        SNR.append(channelSNR[maxInd])
      frame["SNRList"] = SNR
      self.PushFrame(frame)

tray.AddModule(SNRModule, "snr",
               InputName="DeconvolvedWaveforms"
              )


save_path=args.directory  
output_path = os.path.join(save_path, args.folder)
os.makedirs(output_path, exist_ok=True)

tray.AddModule("I3Writer", "writer",
                filename=output_path+"/"+args.outputfile,
                streams=[icetray.I3Frame.DAQ, icetray.I3Frame.Physics] 
              )
 
    
   
tray.Execute(60000)


