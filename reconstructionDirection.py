# run: python reconstructionDirection.py -i /home/acaviedes/work/analysis/results/save/2022_136/output_final_SNR_10-40.i3 -o "/home/acaviedes/work/analysis/results/save/2022_136/output_reconstructed_events_2_SNR_10-40.i3"

#This script reconstructs the direction of the pulses by applyng the module "EstimateRadioShower".
#Its output is an I3file.


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
parser.add_argument("-g", "--gcdfile", default="/data/user/acoleman/datasets/gcd-files/GCD-AntennaSurvey_recent.i3.gz", help="What GCD file (.i3) do you want to use? GCD files contain information on detector geometry and calibration")
parser.add_argument("-o", "--outputfile", default="/home/acaviedes/work/analysis/results/save/output_reconstructed_events.i3", help="Where to save the output i3 file")
args = parser.parse_args()

assert os.path.isfile(args.inputfile), "{} isn't a file!".format(args.inputfile)

tray = I3Tray()

tray.AddModule("I3Reader", "reader", 
         FilenameList = [args.gcdfile] + [args.inputfile])



tray.AddModule("EstimateRadioShower", "radioshower",
                InputName="DeconvolvedWaveforms",
                OutputName="reconstructedI3Particle"
               )

tray.AddModule("I3Writer", "writer",
                filename=args.outputfile,
                DropOrphanStreams=[icetray.I3Frame.DAQ] 
              )


tray.Execute()