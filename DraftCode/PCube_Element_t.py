
import numpy as np

class PCube_Element:
    MAX_DEPTH = 5
    MIN_DEPTH = 2
	DIV_DET = [0.0,0.0,0.0,2.0,1.0,0.5,0.25,0.125,0.0625,0.03125,0.015625]
	RED_DET = [100.0,100.0,100.0,2.4,1.2,0.6,0.3,0.15,0.075,0.0375,0.01875]
    
    def __init__(self,level, c00,c01,c11,c10):
        self.level = level
        self.c00 = c00
        self.c01 = c01
        self.c11 = c11
        self.c10 = c10
        self.children = 0
        self.c0 = (self.c00+self.c11)/2
        self.facedata = {'vertex': [], 'index':[]}
        
    def divide(self):
        if (self.children == 0) and (self.level <= self.MAX_DEPTH): #qui anche possibile limitare la profondita
            c02 = (self.c00+self.c01)/2
            c20 = (self.c00+self.c10)/2
            c12 = (self.c10+self.c11)/2
            c21 = (self.c01+self.c11)/2
            c22 = self.c0
            self.children=[PCube_Element(self.level+1,self.c00,c02,c22,c20)]
            self.children.append(PCube_Element(self.level+1,c20,c22,c12,self.c10))
            self.children.append(PCube_Element(self.level+1,c22,c21,self.c11,c12))
            self.children.append(PCube_Element(self.level+1,c02,self.c01,c21,c22))
            return 1
        else: return 0
            
    def reduce(self):
        if (self.children > 0) and (self.level > self.MIN_DEPTH):
            for ch in self.children:
                ch.reduce()
                del ch
            self.children = 0
            return 1
        else: return 0
     
    def do_triangles(self):
        #per il momento presuppone che datadict sia un dizionario con campi 'vertex' e 'index'
        #se l'oggetto e una foglia
        tempdict = {'vertex': [], 'index':[]}
        if tempdict['vertex'] == []:
            len = 0
        else:
            len = tempdict['vertex'].__len__()
            
        if self.children == 0:
            tempdict['vertex'].append(self.c00)
            tempdict['vertex'].append(self.c10)
            tempdict['vertex'].append(self.c11)
            tempdict['vertex'].append(self.c01)
            tempdict['index'].append([0+len,2+len,3+len])
            tempdict['index'].append([0+len,1+len,2+len])
        else:
            for ch in self.children:
                ch.get_triangles(tempdict) 
        self.facedata = tempdict
        
    def get_triangles(self, datadict):
        #per il momento presuppone che datadict sia un dizionario con campi 'vertex' e 'index'
        #se l'oggetto e una foglia
        if datadict['vertex'] == []:
            len = 0
        else:
            len = datadict['vertex'].__len__()
            
        if self.children == 0:
            datadict['vertex'].append(self.c00)
            datadict['vertex'].append(self.c10)
            datadict['vertex'].append(self.c11)
            datadict['vertex'].append(self.c01)
            datadict['index'].append([0+len,2+len,3+len])
            datadict['index'].append([0+len,1+len,2+len])
        else:
            for ch in self.children:
                ch.get_triangles(datadict)
                
    def tessellate_all_to_level(self,level):
        #this is a test code
        self.divide()
        if (self.children <>0) and (level>0):
            for ch in self.children: ch.tessellate_all_to_level(level-1)
            
            
    def tessellate_by_distance(self,cam_pos_trasf):
        #returns zero if no update is necessary
        dist = np.linalg.norm(cam_pos_trasf - self.c0)
        #print self.level, ' -  ',dist
        if self.children == 0:
            if dist < self.DIV_DET[self.level]: return self.divide()
            else: return 0
        elif dist > self.RED_DET[self.level]: return self.reduce()
        else:
            ret = 0
            for ch in self.children: ret += ch.tessellate_by_distance(cam_pos_trasf)
            return ret 