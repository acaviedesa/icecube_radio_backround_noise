# run: python e_reconstruction_module_applied_from_list.py -i /home/acaviedes/work/analysis/results/save/1349_60000/output_snr_1349_60000.i3 -l /home/acaviedes/work/analysis/results/save/1349_60000/selected_events_withRUNID_10p.pkl -o "/home/acaviedes/work/analysis/results/save/1349_60000/output_recons_events10q.i3"

#This script uses the events of the output list from selectionByHighSNR.py and reconstructs the direction which is saved in a new output i3 file.

import os
import pickle
import numpy as np
import matplotlib.pyplot as plt

from I3Tray import I3Tray
from icecube import icetray, dataio, dataclasses, radcube
from icecube.icetray import I3Units

#icetray.set_log_level(icetray.I3LogLevel.LOG_TRACE)  #to find possible errors

import os
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-i", "--inputfile", default=None, help="What input file (.i3) do you want to use?")
parser.add_argument("-t", "--inputPKLfile", default=None, help="What input file (.pkl) do you want to use?")
parser.add_argument("-g", "--gcdfile", default="/data/user/acoleman/datasets/gcd-files/GCD-AntennaSurvey_recent.i3.gz", help="What GCD file (.i3) do you want to use? GCD files contain information on detector geometry and calibration")
parser.add_argument("-l", '--list', default=None, help="List of selected events")
parser.add_argument("-o", "--outputfile", default="/home/acaviedes/work/analysis/results/save/output_reconstructed_events.i3", help="Where to save the output i3 file")
args = parser.parse_args()

assert os.path.isfile(args.inputfile), "{} isn't a file!".format(args.inputfile)

tray = I3Tray()

tray.AddModule("I3Reader", "reader", 
         FilenameList = [args.gcdfile] + [args.inputfile])



list_path=args.list
with open(list_path, 'rb') as file:
    loaded_list = pickle.load(file)
    #print(loaded_list)
    #here is the list of the events to plot

def EventFilter(frame):
    selected_event = 0
    header = frame['I3EventHeader']
    eventID = header.event_id
    runID = header.run_id
    pair = [eventID, runID]
    
    if pair in loaded_list:
        selected_event = pair[0]        
        
    return selected_event

tray.Add(EventFilter, "hightSNR_selected_events",
         streams=[icetray.I3Frame.DAQ, icetray.I3Frame.Physics])


tray.AddModule("EstimateRadioShower", "radioshower",
                InputName="DeconvolvedWaveforms",
                OutputName="reconstructedI3Particle"
               )

tray.AddModule("I3Writer", "writer",
                filename=args.outputfile,
                streams=[icetray.I3Frame.DAQ, icetray.I3Frame.Physics] 
              )


tray.Execute()