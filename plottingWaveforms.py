# run: python plottingWaveforms.py -i /home/acaviedes/work/analysis/results/save/2022_136/output_reconstructed_events_2_SNR_10-40.i3 -d "/home/acaviedes/work/analysis/results/save/2022_136/plot_2nd_filter_SNR_10-40/waveforms_zenith60-70_azimuth170-180"

#This script plots the waveforms of certain directions. Change the region to plot in line 54.

import numpy as np
import matplotlib.pyplot as plt
import pickle

from I3Tray import I3Tray
from icecube import icetray, dataio, dataclasses, radcube
from icecube.icetray import I3Units

import os
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-i", "--inputfile", default=None, help="What input file (.i3) do you want to use?")
parser.add_argument("-g", "--gcdfile", default="/data/user/acoleman/datasets/gcd-files/GCD-AntennaSurvey_recent.i3.gz", help="What GCD file (.i3) do you want to use? GCD files contain information on detector geometry and calibration")
parser.add_argument("-d", '--directory', default="/home/acaviedes/work/analysis/results/save", help="Where to save the plots")

args = parser.parse_args()

assert os.path.isfile(args.inputfile), "{} isn't a file!".format(args.inputfile)

tray = I3Tray()

tray.AddModule("I3Reader", "reader", 
         FilenameList = [args.gcdfile] + [args.inputfile])

  
output_path = args.directory


class plotFilteredEvents(icetray.I3Module):
  def __init__(self,ctx):
    icetray.I3Module.__init__(self,ctx) 
    self.dataToPlot = [] 
    self.AddParameter("DataToPlot", "Input antenna data map", self.dataToPlot)   
  def Configure(self):    
    self.dataToPlot = self.GetParameter("DataToPlot")
  def Physics(self,frame):
    header = frame['I3EventHeader']
    eventID = header.event_id  
    runID = header.run_id
    pair = [eventID, runID]    
    
    recons_info = frame["reconstructedI3Particle"]        
    zenval=recons_info.dir.zenith
    azival=recons_info.dir.azimuth
    
    if azival<0:
        azival+=2*np.pi
    
    if np.deg2rad(170)<azival<np.deg2rad(180) and np.deg2rad(50)<zenval<np.deg2rad(60):  #define the region to plot    
    
        fig, axes = plt.subplots(3,3, sharex=False, sharey=False, figsize=(40, 20))    
        for imap in range(3):
            antmap = frame[self.dataToPlot[imap][0]]  
            val = self.dataToPlot[imap][1]  #one of 2 possible lists: [1,0] or [0,1]
            for ikey, antkey in enumerate(antmap.keys()):
                chanmap = antmap[antkey]
                for ichan, chankey in enumerate(chanmap.keys()):                   
                    fft = chanmap[chankey].GetFFTData()
                    timeseries = fft.GetTimeSeries()
                    tseries = timeseries*val[0] +timeseries*val[1]/I3Units.mV  #val is to correct the units
                    t, A = radcube.RadTraceToPythonList(tseries)

                    spectrum = fft.GetFrequencySpectrum()
                    freqs, amps = radcube.RadTraceToPythonList(spectrum)
                    freqs=freqs/I3Units.megahertz

                    amps = [radcube.GetDbmHzFromFourierAmplitude(abs(thisAmp), spectrum.binning, 50 * I3Units.ohm) for thisAmp in amps]



                    axes[ikey][imap].plot(t, A, alpha=0.5) 
                    #axes[ikey][imap*2+1].plot(freqs, amps, color='green', alpha=0.7)
                    #axes[ikey][imap*2+1].set_xlim(50, 350)
            axes[0][imap].set_title(f"Event {eventID} {self.dataToPlot[imap][0]}",fontsize=25)


            #plt.xlabel("Time (ns)")         
        plt.tight_layout()
        directory=args.directory   
        filename = f"plot_event{eventID}run{runID}.pdf"          
        file_path = os.path.join(directory, filename)
        fig.savefig(file_path)


tray.AddModule(plotFilteredEvents, "final_plots",
               DataToPlot=[["RadioTAXIWaveform", [1,0]],  #the lists [1,0] and [0,1] are for units
                           ["SpikesRemoved", [1,0]],
                           ["DeconvolvedWaveforms", [0,1]]] 
                  ) 



tray.Execute()
