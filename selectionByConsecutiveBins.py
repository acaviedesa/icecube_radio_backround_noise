# run: python selectionByConsecutiveBins.py -i /home/acaviedes/work/analysis/results/save/2022_136/output_snr_136_nores.i3 -d "/home/acaviedes/work/analysis/results/save/2022_136" -o "output_new.i3"

#This script selects only the events that have 3 consecutive bins with high SNR by comparing their amplitude with respect to the RMS.
#Its output is an I3file.


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
parser.add_argument("-p", '--percentage', type=float, default=0.10, help="Percentage")
parser.add_argument("-o", "--outputfile", default=None, help="Name of the output i3 file")

args = parser.parse_args()

assert os.path.isfile(args.inputfile), "{} isn't a file!".format(args.inputfile)

tray = I3Tray()

tray.AddModule("I3Reader", "reader", 
         FilenameList = [args.gcdfile] + [args.inputfile])


def SNRFilter(frame):
    antmap = frame["DeconvolvedWaveforms"]
    chpassed=0
    antpassed=0
    header = frame['I3EventHeader']
    event = header.event_id
    run = header.run_id
    selected_event = 0
    for ikey, antkey in enumerate(antmap.keys()):
        chanmap = antmap[antkey]
        for ichan, chankey in enumerate(chanmap.keys()):                   
            fft = chanmap[chankey].GetFFTData()
            timeseries = fft.GetTimeSeries()/I3Units.mV
            RMSValue = radcube.GetRMS(timeseries)
            t, A = radcube.RadTraceToPythonList(timeseries)
            for i in range(len(A)):
                if i<=1021:   #1021 for non-cascade
                    if abs(A[i])>3*RMSValue and abs(A[i+1])>3*RMSValue and abs(A[i+2])>3*RMSValue:
                        chpassed+=1                     
            if chpassed>0:
                antpassed+=1
        if antpassed==3:
            selected_event = event    
    return selected_event   

tray.Add(SNRFilter, "possible_events",
         streams=[icetray.I3Frame.Physics])



output_path = args.directory

tray.Add("I3Writer",
         filename=output_path+"/"+args.outputfile,
         DropOrphanStreams=[icetray.I3Frame.DAQ])


tray.Execute()
