# run: python plottingHistogram.py -i /home/acaviedes/work/analysis/results/save/2022_136/output_final_SNR_10-40.i3 -d "/home/acaviedes/work/analysis/results/save/2022_136" -l y -b 20 -c 2

#This script makes a histogram for each antenna, all in the same file. Also makes zoomed histograms (change limits in line 73). Prints the amount of events analysed.


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
parser.add_argument("-d", '--directory', default="/home/acaviedes/work/analysis/results/save", help="Where to save the histogram")
parser.add_argument("-l", '--log', default=None, help="Plot in logarithmic scale?")
parser.add_argument("-b", '--bins', type=int, default=15, help="Number of bins")
parser.add_argument("-c", '--stage', type=int, default=0, help="Stage of processing. 0: soft triggered events; 1: events that passed the first filter of 3 consecutive bins to have high SNR; 2: events that passed the second filter of selecting events of an interval of SNR values")

args = parser.parse_args()


tray = I3Tray()

tray.AddModule("I3Reader", "reader", 
         FilenameList = [args.gcdfile] + args.inputfile)




output_path = args.directory

class SNRHistogram(icetray.I3Module): 
  def __init__(self,ctx):
    icetray.I3Module.__init__(self,ctx)
    self.inputName = ""
    self.outputDir = ""
    self.snrValues1 = []
    self.snrValues2 = []
    self.snrValues3 = []    
    self.AddParameter("InputName", "Input antenna data map", self.inputName)
    self.AddParameter("OutputDir", "Outputdir", self.outputDir)
  def Configure(self):
    self.inputName = self.GetParameter("InputName")
    self.outputDir = self.GetParameter("OutputDir")
  def Physics(self,frame):
    if frame.Has(self.inputName):
      SNR_values = frame[self.inputName]
      self.snrValues1.append(SNR_values[0])
      self.snrValues2.append(SNR_values[1])
      self.snrValues3.append(SNR_values[2])
  def Finish(self):  
    fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(12, 4))
    for i, snr_values in enumerate([self.snrValues1, self.snrValues2, self.snrValues3]): 
      b=args.bins
      ax = axes[i,0]
      ax.hist(snr_values, bins=b, edgecolor='black') 
      if args.log is not None:   
        ax.set_yscale('log')
      fig.text(0.25, 0.02, 'SNR value', va='center', rotation='horizontal')
      fig.text(0.07, 0.5, 'Frequency', va='center', rotation='vertical')
        
      ax = axes[i,1]
      ax.hist(snr_values, bins=b, edgecolor='black')
      if args.log is not None:   
        ax.set_yscale('log')
      fig.text(0.65, 0.02, 'SNR value', va='center', rotation='horizontal')
      ax.set_xlim(75, 400) #for the zoomed histogram          
              
    histo = os.path.join(self.outputDir, f'SNR_Histograms_norm{args.stage}.pdf')
    plt.savefig(histo)
    amount_events=len(self.snrValues1)
    if args.stage == 0:
        print(f"Total number of soft triggered events: {amount_events}")
    if args.stage == 1:
        print(f"Total number of events that passed the 1st filter: {amount_events}")
    if args.stage == 2:
        print(f"Total number of events that passed the 2nd filter: {amount_events}")
    
    
tray.AddModule(SNRHistogram, "PlotHistSNR", 
               InputName="SNRList",
               OutputDir=output_path
              )

    

tray.Execute()


