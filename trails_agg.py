import pickle
with open('/code/tempfolder/trails.pickle', 'rb') as fin:
    featconnections = pickle.load(fin) 

import fiona
import json
from shapely.ops import linemerge
from shapely.geometry import shape, mapping 
from shapely.geometry import MultiLineString
from shapely import geometry
trailslayers = [d for d in featconnections if d.basedata['Subclass'] == 'ExistingTrails']
for t in trailslayers:
    t.priority = int(t.basedata['AuthorityLevel'])
sortedlist = sorted(trailslayers, key=lambda i: i.priority)


def mergelines(features):
    pass

# clip new lines to buffer and add
def bufferfeatures(features):
    ls = []
    ms = []
    for f in features:
        if f['geometry'] is None:
            continue
        snew = shape(f['geometry'])
        if isinstance(snew, geometry.linestring.LineString):
            ls.append(snew)
        else:
            ms.append(snew)
    newmulti = linemerge(ls)
    multimapping = mapping(newmulti)
    for z in ms:
        zmap = mapping(z)
        multimapping['coordinates'] += zmap['coordinates']
    alllines = shape(multimapping)
    # about 6m
    buffedlines = alllines.buffer(.00016)
    schema = {'geometry': 'MultiPolygon', 'properties': {}}
    with fiona.open('tempfolder/linemergebuffer.shp', 'w', 'ESRI Shapefile', schema) as output:
        output.write({'geometry': mapping(buffedlines), 'properties': {}})
    return buffedlines

collection = None
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
            'OLength': feat['origgeom'].length
        }
        tempcollection.append(feat)
    if collection is None:
        collection=tempcollection
        continue
    bufferedcollection = bufferfeatures(collection)
    addeddistance = 0
    rejecteddistance = 0
    for f in tempcollection:
        origgeom = shape(f['geometry'])
        newgeom = origgeom.difference(bufferedcollection)
        if newgeom.length > 0 and float(newgeom.length)/float(f['properties']['OLength']) > .5:
            addeddistance += origgeom.length
#             f['geometry'] = mapping(origgeom)
            collection.append(f)
        else:
            rejecteddistance += origgeom.length
            rejectedfeatures.append(f)
    print("added distance", addeddistance)
    print("rejected distance", rejecteddistance)
    
from fiona.crs import from_epsg

newschema = {
    'geometry': 'LineString',
    'properties': {
        'OName': 'str:256',
        'OAuthorityLevel': 'int',
        'OManaging': 'str:256',
        'OSource': 'str:256',
        'OProperties': 'str:5000',
        'OLength': 'float:16'
    }
}
with fiona.open('/code/output/trails_aggregated.shp', 'w', driver='ESRI Shapefile', schema=newschema, crs=from_epsg(4326)) as output:
    for f in collection:
        output.write(f)
        
with fiona.open('/code/output/trails_rejected.shp', 'w', driver='ESRI Shapefile', schema=newschema, crs=from_epsg(4326)) as output:
    for f in rejectedfeatures:
        output.write(f)
    
    