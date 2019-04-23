import requests
import json
import copy
import fiona
import os.path as op
DEBUG=False

FEATURESERVERFOLDER = '/code/featureserverdata/'


class FeatureServer:
    def __init__(self, featureserverurl = None, basedata = None, forcereload=False):
        self.features = []
        self.basedata = basedata
        if basedata['Type'] == 'Shapefile':
            self.idfield = 'fid'
            with fiona.open(basedata['Location'], 'r', 'ESRI Shapefile') as inputfile:
                for feature in inputfile:
                    self.features.append(feature)   
            return
        
        self.featureserverurl = op.join(featureserverurl, 'query')
        self.callparams = {'outSR':'4326',\
                          'f':basedata['format'],\
                          'outFields':'*',\
                          'where':'1=1'}
        self.idfield = self.getID()
        if op.isfile(self.getOutputFile()) and forcereload==True:
            with open(self.getOutputFile(), 'r') as inputfile:
                self.features = json.load(inputfile)
        else:
            self.features = None
        
    def getparams(self):
        return copy.deepcopy(self.callparams)
    
    def makecall(self, params):
        res = requests.get(self.featureserverurl, params=params)
#         print("making call", res.url)
        if res.status_code != requests.codes.ok:
            print("****Call Error on ", res.url)
            return None
        try:
            retobj = res.json()
        except Exception as e:
            print("****JSON Decode error", str(e))
            print(res.url)
            return None
        return retobj
        
    def getID(self):
        idparams = self.getparams()
        idparams['returnIdsOnly'] = 'true'
        retobj = self.makecall(idparams)
        if DEBUG:
            print(retobj)
        if not retobj:
            return None
        if self.basedata['format'] in ['pgeojson']:
            return retobj['properties']['objectIdFieldName']
        elif self.basedata['format'] in ['json', 'geojson']:
            return retobj['objectIdFieldName']
        
    def processLayer(self, retobj):
        if self.basedata['format'] == 'json':
            # all json returns are point features at this time
            newlayer = {
                          "type" : "FeatureCollection", 
                          "crs" : 
                          {
                            "type" : "name", 
                            "properties" : 
                            {
                              "name" : "EPSG:4326"
                            }
                          }, 
                          "features" : []
                        }
            basefeat = {"type" : "Feature", 
                              "geometry" : 
                              {
                                "type" : "Point", 
                                "coordinates" : [
                                  -68.9249700019774, 44.4528591273557
                                ]
                              }, 
                              "properties" : {}
                       }
            for feat in retobj['features']:
                basefeat['properties'] = feat['attributes']
                basefeat['geometry']['coordinates'] = [feat['geometry']['x'], feat['geometry']['y']]
                newlayer['features'].append(basefeat)
        else:
            return retobj
            
            
    
    def startCollection(self):
        callparams = self.getparams()
        callparams['orderByFields'] = '{} ASC'.format(self.idfield)
        lastobject = 0
        completefeatures = None
        while True:
            callparams['where'] = '{}>{}'.format(self.idfield, lastobject)
            retobj = self.makecall(callparams)
            newlayer = self.processLayer(retobj)
            if not newlayer:
                break
            if len(newlayer['features']) > 0:
                if completefeatures is None:
                    completefeatures = retobj
                else:
                    completefeatures['features'] += newlayer['features']
            else:
                break
            lastobject = newlayer['features'][-1]['properties'][self.idfield]
        try:
            self.features = completefeatures['features']
        except Exception as e:
            print("Error in call", e)
            print("--- ", completefeatures)
            return
        with open(self.getOutputFile(), 'w') as jsonoutput:
            json.dump(completefeatures, jsonoutput)
            
    def getOutputFile(self):
        return op.join(FEATURESERVERFOLDER, self.basedata['Name'].replace(' ', '_')) + '.json'
    
    def getiterator(self):
        if self.features is not None:
            return self.features
        else:
            return []
    
    @classmethod
    def getOutputPath(cls, name):
        return op.join(FEATURESERVERFOLDER, name.replace(' ', '_')) + '.json'
            