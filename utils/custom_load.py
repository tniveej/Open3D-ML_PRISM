import open3d.ml.torch as ml3d #Must be first to import to fix bugs when running OpenGL
import laspy
import numpy as np
import os
import glob
import math
import json



class CustomDataLoader():
    def __init__(self,las_path = None):
        
        self.dir = os.path.dirname(os.path.realpath(__file__))
        self.folder = os.path.basename(self.dir) 
        self.file_path = os.path.join(self.dir, self.folder + "_Data.npy")
        self.las_path = las_path
        
        
        if self.las_path != None:
            #Checking if the path to directory is correct
            
            abs_path = os.path.abspath(self.las_path)
            las = laspy.read(abs_path)
            points = np.vstack((las.x, las.y, las.z)).transpose()
            
            #Checking if the .las file has color data
            try:
                red = las.red
                green = las.green
                blue = las.blue
                colors = np.vstack((red, green, blue)).transpose()/65536 #Normalize to 1
                data = np.hstack((points,colors))
                np.save(self.file_path, data)
            
            except:
                data = points
                np.save(self.file_path, data)
                print("\nRGB data are not found. Data will only consist of points")
            
        else:
            pass
    
    def VisualizingData(self,data_path = None):
        
        vis = ml3d.vis.Visualizer()
                                                
        #Checking if the user has passed input for data_path
        if data_path == None:
            data_path = self.file_path
                                         
        
        points = np.load(data_path)[:,0:3]
        print(f"\nPreparing data for visualization...")
        try:
                 
            color = np.load(data_path)[:, 3:] 
            data = [
                    {
                    'name'  : self.folder + str('_PC'),
                    'points': points.astype(np.float32),
                    'color' : color.astype(np.int32),
                    }  
                ]
                                    
            vis.visualize(data)
            
        except:
            print(f"\nNo color found in data.\nRandomizing color for visualization...")
            color = np.random.rand(*points.shape) 
            data = [
                    {
                        'name'  : self.folder + str('_PC'),
                        'points': points.astype(np.float32),
                        'color' : color.astype(np.float32),
                    }
                ]
                         
            vis.visualize(data)
                 
    
    def Domain_Split(self,Xsplit=int,Ysplit=int,Zsplit=int,feat = False, point_path = None,label_path = None,color_path = None):
        
        """
        Domain_Split is a function which takes in parameters such as Xsplit,Ysplit,Zsplit to split the global
        domain into multiple subdomain by dividing the corresponding axes based on 
        the specified number given. These number must be in integer format. 'feat' has been 
        set to False by default if 'color' parameter is not required to be included when running
        inferences. Path to points and colors are optional to be passed in, however, if nothing is
        set, the function will search for them in the current directory. Color is excluded if 'feat'
        is set to False which is its default setting. Change it to True if color is needed when
        running inferences.

        Parameters:
        Xsplit (int): Number of subdomains to be split in the x-axis
        Ysplit (int): Number of subdomains to be split in the y-axis
        Zsplit (int): Number of subdomains to be split in the z-axis
        feat (bool): Whether or not to include color data in the point cloud
        point_path (str): Path to the .npy file containing the point cloud
        label_path (str): Path to the .npy file containing the labels
        color_path (str): Path to the .npy file containing the color data

        Returns:
        batches (list): A list containing dictionaries of point cloud data
        """
        if point_path == None:
            point = np.load(self.file_path)[:,0:3]
            print(f"\nUsing points from {self.file_path} directory")
        else:
            point = np.load(point_path)
                            
        
        if label_path == None:
            label = np.zeros(np.shape(point)[0], dtype = np.int32)
        else:
            label = np.load(label_path)
            
                       
        if(color_path == None and feat == True):  
            color = np.load(self.file_path)[:,3:]
            print(f"Using colors from {self.file_path} directory\n")
        elif(color_path != None and feat == True):
            color = np.load(color_path)
                    
                 
        xmax = max(point[:,0])
        ymax = max(point[:,1])
        zmax = max(point[:,2])
        xmin = min(point[:,0])
        ymin = min(point[:,1])
        zmin = min(point[:,2])

        dom_max = [xmax, ymax, zmax]
        dom_min = [xmin, ymin, zmin]

        split = [Xsplit,Ysplit,Zsplit]

        #Create a boundary limit for each sectional domain using:
        dom_lim = []
        for i in range(len(split)):
            box = list(np.linspace(math.floor(dom_min[i]), 
                                    math.floor(dom_max[i]), 
                                    split[i]+1))
            
            if box[-1] < dom_max[i]:
                box[-1] = int(math.ceil(dom_max[i] +1))

            dom_lim.append(box[1:])

        Xlim,Ylim,Zlim = np.meshgrid(dom_lim[0],dom_lim[1],dom_lim[2])
        Xlim = Xlim.flatten()
        Ylim = Ylim.flatten()
        Zlim = Zlim.flatten()
        Class_limits = np.vstack((Xlim,Ylim,Zlim)).T
        print(Class_limits)

        # Do a for loop which iterates through all of the point cloud (pcs)
        Code_name = "000"
        batches = []
        counter = 0
        
        #To allow function to take in None for 'color' in feat or with variable being passed in:
        if feat == False:
            
            for Class_limit in Class_limits:
                
                Condition = point < Class_limit
                InLimit = point[np.all(Condition == True, axis=1)]
                point = point[np.any(Condition == False, axis=1)]
                InLabel = label[np.all(Condition == True, axis=1)]
                label = label[np.any(Condition == False, axis=1)]
                                
                if len(InLimit) < 10:
                    pass
                
                else:
                    name = Code_name + str(counter)
                    data = {
                        'name': name,
                        'limit': Class_limit,
                        'point': InLimit,
                        'label': InLabel,
                        'feat': None
                        }
                    
                    print(f"\nPoint cloud - {data['name']} has been successfully loaded")
                    print(f"\nNumber of Point Cloud: {len(InLimit)}")
                    batches.append(data)
                    counter += 1

        else:
            
            for Class_limit in Class_limits:
                
                Condition = point < Class_limit
                InLimit = point[np.all(Condition == True, axis=1)]
                point = point[np.any(Condition == False, axis=1)]
                InLabel = label[np.all(Condition == True, axis=1)]
                label = label[np.any(Condition == False, axis=1)]
                InColor = color[np.all(Condition == True, axis=1)]
                color = color[np.any(Condition == False, axis=1)]
                
                if len(InLimit) < 10:
                    # pass
                    a = 0
                
                else:
                    name = Code_name + str(counter)
                    data = {
                        'name': name,
                        'limit': Class_limit,
                        'point': InLimit,
                        'label': InLabel,
                        'feat': InColor
                        }
                    
                    print(f"\nPoint cloud - {data['name']} has been successfully loaded")
                    print(f"\nNumber of Point Cloud: {len(InLimit)}")
                    batches.append(data)
                    counter += 1

        return batches
    
    def CustomConfig(self,cfg,ckpt_path = None):
               
        if ckpt_path == None:
            print("\nFetching checkpoint model in the current directory")
            ckpts = glob.glob(os.path.join(self.dir, "*.pth"))
            ckpt_path = ckpts[-1] #If there is more than one, select the last one in the list of array
            print(f"Using checkpoint model {ckpt_path} to run inference")
              
                        
        print('\nConfiguring model...')    
        try: 
            model = ml3d.models.RandLANet(**cfg.model)
            print("RandLANet model configured...")
        except:
            model = ml3d.models.KPFCNN(**cfg.model)
            print("KPConv model configured...")
            
           
        pipeline = ml3d.pipelines.SemanticSegmentation(model=model, device="gpu", **cfg.pipeline)
        print(f"The device is currently running on: {pipeline.device}\n")
        pipeline.load_ckpt(ckpt_path=ckpt_path)
        
        return pipeline
    
    
    def CustomInference(self,pipeline,batches):
        Results = []
                                      
        print('Running Inference...')

        for i,batch in enumerate(batches):
            i += 1
            print(f"\nIteration number: {i}")
            results = pipeline.run_inference(batch)
            print('Inference processed successfully...')
            print(f"\nInitial result: {results['predict_labels'][:13]}")
            pred_label = (results['predict_labels'] +1).astype(np.int32) 
            
            
            vis_d = {
                "name": batch['name'],
                "points": batch['point'].astype(np.float32),
                "labels": batch['label'].astype(np.float32),
                "pred": pred_label,
                    }
            
                   
            pred_val = vis_d["pred"][:13]
            print(f"\nPrediction values: {pred_val}")
            Results.append(vis_d)      
                
        return Results
        
    def PytoJson(self,Predictions,interval = 400000):   #Predictions variable refers to Results
        file_name = self.folder + str('_PredictedResults.json')
        JsonData = []

        #To bypass the RAM issue when converting .tolist all at once
        for Prediction in Predictions:
            if len(Prediction["points"]) < interval:
                Prediction["points"] = (Prediction["points"]).tolist()
                Prediction["labels"] = (Prediction["labels"]).tolist()
                Prediction["pred"] = (Prediction["pred"]).tolist()
                JsonData.append(Prediction)
                print(f"\nPoint cloud - {Prediction['name']} has been converted to Json")
            
            else:
                print(f"\nPoint cloud - {Prediction['name']} has exceeded {interval} points\nSplitting the batch...")
                Range = list(range(0,len(Prediction["points"]),interval))
                print(f"Limit: {Range}")
                print(f"Last limit: {Range[-1]}")
                for i, content in enumerate(Range):
                    if content == Range[-1]:
                        print(f"Content: {content}")
                        split_name = Prediction["name"] + str('-') + str(i)
                        split_points = Prediction["points"][content:, :]
                        split_labels = Prediction["labels"][content:]
                        split_pred = Prediction["pred"][content:]
                    else:
                        print(f"The range content: {content}")
                        split_name = Prediction["name"] + str('-') + str(i)
                        split_points = Prediction["points"][content:Range[i+1], :]
                        split_labels = Prediction["labels"][content:Range[i+1]]
                        split_pred = Prediction["pred"][content:Range[i+1]]

                    JsonData.append({
                        "name": split_name,
                        "points": split_points.tolist(),
                        "labels": split_labels.tolist(),
                        "pred": split_pred.tolist(),
                    })
                    print(f"\nPoint cloud - {split_name} has been converted to Json")
                        
                        
        if os.path.exists(file_name):
                print(f"{file_name} already exists. No need to rewrite.")
        else:
                            
                with open(file_name, "w") as file:
                    json.dump(JsonData, file, indent=4)
                print(f"{file_name} has been created and written.")