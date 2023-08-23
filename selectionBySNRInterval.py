# run: python selectionBySNRInterval.py -i /home/acaviedes/work/analysis/results/save/2022_136/output_new.i3 -h 40 -l 10 -d "/home/acaviedes/work/analysis/results/save/2022_136" -o "output_final_SNR_10-40.i3"

#This script selects the events that for the 3 antennas have SNR values in the chosen interval.
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
parser.add_argument("-h", "--highthreshold", type=int, default=40, help="Higher SNR Cut")
parser.add_argument("-l", "--lowthreshold", type=int, default=40, help="Lower SNR Cut")



args = parser.parse_args()

assert os.path.isfile(args.inputfile), "{} isn't a file!".format(args.inputfile)

tray = I3Tray()

tray.AddModule("I3Reader", "reader", 
         FilenameList = [args.gcdfile] + [args.inputfile])



def FinalFilter(frame):
    SNRList = frame["SNRList"]
    header = frame['I3EventHeader']
    event = header.event_id
    selected_event = 0
    if args.highthreshold > SNRList[0] > args.lowthreshold and args.highthreshold > SNRList[1] > args.lowthreshold and args.highthreshold > SNRList[2] > args.lowthreshold:
        selected_event=event
    return selected_event   
     
tray.AddModule(FinalFilter, "final_events"
              )


   
output_path = args.directory


tray.Add("I3Writer",
         filename=output_path+"/"+args.outputfile,
         DropOrphanStreams=[icetray.I3Frame.DAQ])



tray.Execute()
