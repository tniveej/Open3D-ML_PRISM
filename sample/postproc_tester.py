#MUST BE INCLUDED TO WORK
import sys
sys.path.insert(0,r"/home/helmi/Open3D-ML_PRISM/") #directory to the root project

from utils import CustomDataLoader,PostProcess
import open3d.ml.torch as ml3d
import open3d.ml as _ml3d
import os
import numpy as np

def main():
    #play around with the start and end
    Start = [-100,-50,7]
    End = [95,40,7]
    tol = 0.05 #Huge tolerance of 0.5m for each side of the line
    
        
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path,"sample_Data.npy")
    sliced_path = os.path.join(dir_path,"Sliced_points.npy")
    cfg_directory = os.path.expanduser("~/Open3D-ML_PRISM/ml3d/configs/")
    cfg_file = os.path.join(cfg_directory, "randlanet_parislille3d.yml")
    cfg = _ml3d.utils.Config.load_from_file(cfg_file)
    
    Data = np.load(file_path)
    cross_sec = PostProcess()
    cross_sec.pc_slice(Start,End,tol,Data,"XZ") #try to change the plane orientation XY,XZ,YZ
    
    
    Visualize = CustomDataLoader(cfg)
    Visualize.VisualizingData(sliced_path)
    #Visualize.VisualizingData(file_path)
    
    
if __name__ == "__main__":
    main()