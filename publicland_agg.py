import pickle
from featureserver import FeatureServer
with open('/code/tempfolder/publicland.pickle', 'rb') as fin:
    featconnections = pickle.load(fin)    

import fiona
import json
from shapely.geometry import shape, mapping 
from shapely.ops import cascaded_union
from shapely.geometry import MultiLineString, MultiPolygon
from shapely import geometry
for t in featconnections:
    t.priority = int(t.basedata['AuthorityLevel'])
sortedlist = sorted(featconnections, key=lambda i: i.priority)


collection = []
singlepolygon = None
rejectedfeatures = []

for layer in sortedlist:
    print("working on ", layer.basedata['Name'])
    tempcollection = []
    for feat in layer.features:
        try:
            feat['origgeom'] = shape(feat['geometry'])
        except Exception as e:
            continue
        feat['properties'] = {
            'OName': layer.basedata['Name'],
            'OAuthorityLevel': layer.basedata['AuthorityLevel'],
            'OManaging': layer.basedata['Managing Org'],
            'OSource': layer.basedata['Source'],
            'OProperties':  json.dumps(dict(feat['properties'])),
            'OArea': feat['origgeom'].area
        }
        tempcollection.append(feat)
    if singlepolygon is None:
        print("length of tempcollection", len(tempcollection))
        collection = tempcollection
        singlepolygon = cascaded_union([shape(f['geometry']) for f in tempcollection]).buffer(0)
        continue
    addeddistance = 0
    rejecteddistance = 0
    for f in tempcollection:
        origgeom = shape(f['geometry']).buffer(0)
        newgeom = origgeom.difference(singlepolygon)
        if newgeom.area > 0 and float(newgeom.area)/float(f['properties']['OArea']) > .5:
            addeddistance += origgeom.area
#             f['geometry'] = mapping(origgeom)
            collection.append(f)
        else:
            rejecteddistance += origgeom.area
            rejectedfeatures.append(f)
    fs = []
    nonvalid_count = 0
    for f in collection:
        try:
            fgeom = shape(f['geometry'])
        except Exception as e:
            print(e)
        else:
            if fgeom.is_valid:
                fs.append(fgeom)
            else:
                nonvalid_count +=1
    print("Total nonvalid geoms", nonvalid_count)
    print("number of geom features", len(fs))
    singlepolygon = cascaded_union(fs).buffer(0)
    print("added area", addeddistance)
    print("rejected area", rejecteddistance)
    
from fiona.crs import from_epsg

newschema = {
    'geometry': 'Polygon',
    'properties': {
        'OName': 'str:256',
        'OAuthorityLevel': 'int',
        'OManaging': 'str:256',
        'OSource': 'str:256',
        'OProperties': 'str:5000',
        'OArea': 'float:16'
    }
}
with fiona.open('/code/output/publicland_aggregated.shp', 'w', driver='ESRI Shapefile', schema=newschema, crs=from_epsg(4326)) as output:
    for f in collection:
        output.write(f)
        
with fiona.open('/code/output/publicland_rejected.shp', 'w', driver='ESRI Shapefile', schema=newschema, crs=from_epsg(4326)) as output:
    for f in rejectedfeatures:
        output.write(f)
    
    