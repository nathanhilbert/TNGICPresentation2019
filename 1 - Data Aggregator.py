#!/usr/bin/env python
# coding: utf-8

#  - Gather data for each dataset
#    - If dataset if feature server, download and store as geojson
#    
#  - Merge them together with pushing their attribute into JSON text
#    - Mark Duplicates based on Primary Features
#      - sort by order, buffer, delete from new features, and add what's left
#      
#    
#  
#  - If the features have OSM files, compare them based on buffers and cutting and coverage
# 

# In[1]:


import csv
import os.path as op
FEATURESERVERFOLDER = '/code/featureserverdata/'
BASEFILE = '/code/Data Aggregator - Trails.csv'
aggdatabase = []
with open(BASEFILE, 'r') as basefile:
    dictfile = csv.DictReader(basefile)
    for row in dictfile:
        if dict(row)['Subclass'] == 'ExistingTrails':
            aggdatabase.append(dict(row))        
    


# In[2]:


from featureserver import FeatureServer

    
featconnections = []
for row in aggdatabase:
#     if row['Type'] in ['FeatureServer', 'Shapefile'] and row['Subclass'] == 'ExistingTrails':
    if row['Type'] in ['FeatureServer', 'Shapefile']:
        # gather data
        fs = FeatureServer(featureserverurl=row['Location'], basedata=row)
        if fs.features == None and fs.idfield != None:
            print("Starting Collecting", row['Name'])
            fs.startCollection()
        elif fs.idfield == None:
            print("Failure on ", row['Name'])
            continue
        elif fs.features != None:
            print("Obtained existing features for", row['Name'])
        featconnections.append(fs)
        
        


# In[3]:


import pickle
with open('/code/tempfolder/trails.pickle', 'wb') as fout:
    pickle.dump(featconnections, fout)


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




