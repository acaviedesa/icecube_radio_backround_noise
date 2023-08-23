# run: python plottingReconstructionAndBuildings.py -i /home/acaviedes/work/analysis/results/save/2022_136/output_reconstructed_events_2_SNR_10-40.i3 -d "/home/acaviedes/work/analysis/results/save/2022_136/plot_2nd_filter_SNR_10-40"


#This script uses the output i3file from the reconstruction and plots the reconstructed direction of the selected events; it also plots the coordinates of buildings (only azimuth angles). 
#Additionally it plots a 2D histogram.


import pandas as pd
import math
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm


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

directory=args.directory

class reconstruction(icetray.I3Module): 
    def __init__(self,ctx):
        icetray.I3Module.__init__(self,ctx)      
        self.inputName = ""
        self.zen=[]
        self.azi=[] 
        self.zenrad=[]
        self.azirad=[]
        self.event=[]
        self.run=[]        
        self.AddParameter("InputName", "Input antenna data map", self.inputName)
    def Configure(self):    
        self.inputName = self.GetParameter("InputName") 
    def Physics(self,frame): 
        header=frame['I3EventHeader']
        eventid=header.event_id
        runid=header.run_id
        recons_info = frame[self.inputName]
        
        zenval=recons_info.dir.zenith
        azival=recons_info.dir.azimuth
        
        self.zenrad.append(zenval)
        self.azirad.append(azival) 
        
        rec_zenith = zenval/I3Units.degree
        rec_azimuth = azival/I3Units.degree
        if rec_azimuth < 0:
            rec_azimuth+=360
        self.zen.append(rec_zenith)
        self.azi.append(rec_azimuth)  
        self.event.append(eventid)
        self.run.append(runid)
        
        snrlist=frame['SNRList']        
            
    def Finish(self):
        data = {
            'Event ID': self.event,
            'Run ID': self.run,
            'Azimuth (°)': self.azi,
            'Zenith (°)': self.zen
                }
        df = pd.DataFrame(data)
        
        dataname = 'final_data.csv'          
        data_path = os.path.join(directory, dataname)
        df.to_csv(data_path)        
        
        fig = plt.figure(figsize=(6, 6))
        ax1 = fig.add_subplot(111, projection='polar') # 211: 2 rows, 1 column, at position 1
        ax1.scatter(np.deg2rad(self.azi), self.zen, marker='x', c='red', s=20)
        
        #coordinates of buildings
        ICL_az=32.18157430526908 
        DSL_az=5.627914983887684 
        SPT_az=28.926293961391167 
        VIPER_az=13.391525720423619
        MAPO_az=11.640040688204127 
        B61_az=10.531885163277781        

        ax1.scatter(np.deg2rad(ICL_az), 85, marker='o', c='green', label='ICL')
        ax1.scatter(np.deg2rad(DSL_az), 85, marker='o', c='blue', label='DSL')
        ax1.scatter(np.deg2rad(SPT_az), 85, marker='o', c='orange', label='SPT')
        ax1.scatter(np.deg2rad(VIPER_az), 85, marker='o', c='yellow', label='VIPER')
        ax1.scatter(np.deg2rad(MAPO_az), 85, marker='o', c='purple', label='MAPO')
        ax1.scatter(np.deg2rad(B61_az), 85, marker='o', c='cyan', label='B61')
        ax1.legend()
        
        
        ax1.set_theta_zero_location("E")
        ax1.set_rlabel_position(0)
        ax1.tick_params(axis='y', labelsize=7)
        ax1.tick_params(axis='x', labelsize=13)
        ax1.set_ylim(0, 90)
        ax1.set_xlabel('Azimuth')
        label_position=ax1.get_rlabel_position()
        ax1.text(np.radians(label_position-4),ax1.get_rmax()/1.2 ,r"Zenith [°]",
                    rotation=label_position,ha='center',va='center', fontsize=10)       
        plot1name = "direction_polar_build.png"          
        plot1_path = os.path.join(directory, plot1name)
        plt.savefig(plot1_path)
        
        
        #makes a 2D histogram         
        #removes de NaN values (necessary to make the histogram)
        azi_data = np.array(self.azi)
        zen_data = np.array(self.zen)
        combined_mask = np.logical_or(np.isnan(azi_data), np.isnan(zen_data))
        azi_data = azi_data[~combined_mask]
        zen_data = zen_data[~combined_mask]
        #
        fig2 = plt.figure(figsize=(14, 4))
        ax2 = fig2.add_subplot(111)
        ax2.grid(False)        
        
        hist, xedges, yedges, im = ax2.hist2d(azi_data, zen_data, bins=(36,9),cmap='viridis_r')
        
        vmin = hist[hist > 0].min()  # Avoid 0 for LogNorm
        vmax = hist.max()
        norm = LogNorm(vmin=vmin, vmax=vmax)
        im.set_norm(norm)
        
        ax2.set_xlim(0, 360)
        ax2.set_ylim(0, 90)
        ax2.set_xlabel('Azimuth (°)')
        ax2.set_ylabel('Zenith (°)')
        
        plt.colorbar(im, ax=ax2)         
        plot2name = "direction_hist_log.png"          
        plot2_path = os.path.join(directory, plot2name)
        plt.savefig(plot2_path)
        
        
        """
        print("+-----------------------+----------------------+")
        print("| Azimuth               | Zenith               |")
        print("+-----------------------+----------------------+")
        for aziang, zenang in zip(self.azi, self.zen):
            print(f"| {str(aziang).ljust(20)} | {str(zenang).ljust(20)} |")
        print("+-----------------------+----------------------+")   
        """


tray.AddModule(reconstruction, "reconstruction",
               InputName = "reconstructedI3Particle"
              )


tray.Execute()