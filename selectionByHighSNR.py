# run: python selectionByHighSNR.py -i /home/acaviedes/work/analysis/many_events_upsampled_corrections_more/save/1349_1million/output_snr_1349_1million.i3 -d "/home/acaviedes/work/analysis/many_events_upsampled_corrections_more/save/1349_1million" -p 0.25


#This script selects only a % of the events that for the 3 antennas have high SNR. 
#Its output is a list of these events (specifying EventID and RunID).


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
args = parser.parse_args()

assert os.path.isfile(args.inputfile), "{} isn't a file!".format(args.inputfile)

tray = I3Tray()

tray.AddModule("I3Reader", "reader", 
         FilenameList = [args.gcdfile] + [args.inputfile])

output_path = args.directory

class CommonEvents(icetray.I3Module):
    def __init__(self,ctx):
        icetray.I3Module.__init__(self,ctx)        
        self.snr_ant1_list=[]
        self.snr_ant2_list=[]
        self.snr_ant3_list=[]
        self.common_events_list=[]
        self.outputDir = ""
        self.AddParameter("OutputDir", "Outputdir", self.outputDir)
    def Configure(self):
        self.outputDir = self.GetParameter("OutputDir")
    def Physics(self,frame):
        snr_list = frame["SNRList"]
        header = frame["I3EventHeader"]    
        eventID = header.event_id
        runID = header.run_id
        tuple1=(eventID, runID, snr_list[0])
        tuple2=(eventID, runID, snr_list[1])
        tuple3=(eventID, runID, snr_list[2])       
        self.snr_ant1_list.append(tuple1)
        self.snr_ant2_list.append(tuple2)
        self.snr_ant3_list.append(tuple3)  
    def Finish(self):
        self.snr_ant1_list.sort(key=lambda x: x[2], reverse=True)
        self.snr_ant2_list.sort(key=lambda x: x[2], reverse=True)
        self.snr_ant3_list.sort(key=lambda x: x[2], reverse=True) 
        num_tuples_to_select = int(len(self.snr_ant1_list) * args.percentage)
        selected_tuples1 = self.snr_ant1_list[:num_tuples_to_select]
        selected_tuples2 = self.snr_ant2_list[:num_tuples_to_select]
        selected_tuples3 = self.snr_ant3_list[:num_tuples_to_select]
        events1 = [[item[0], item[1]] for item in selected_tuples1]
        events2 = [[item[0], item[1]] for item in selected_tuples2]
        events3 = [[item[0], item[1]] for item in selected_tuples3]  
        events1_set = set(map(tuple, events1))
        events2_set = set(map(tuple, events2))
        events3_set = set(map(tuple, events3))
        
        common_sublists_set = events1_set.intersection(events2_set, events3_set)
        self.common_events_list = [list(item) for item in common_sublists_set]        
        
        
        list_path = os.path.join(self.outputDir, 'selected_events_withRUNID.pkl')
        
        with open(list_path, 'wb') as file:
            pickle.dump(self.common_events_list, file)
        l1=sorted(events1)
        l2=sorted(events2)
        l3=sorted(events3)
        numberofevents=len(self.common_events_list)
        print(f"Total number of high SNR events: {numberofevents}")
        print(self.common_events_list)
        
tray.AddModule(CommonEvents, "selected_events",
               OutputDir=output_path
              )




tray.Execute(60000)
