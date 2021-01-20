from OpenGL.GL import *
from OpenGL.GL.ARB import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np
from RequestManager import RequestManager
from MaterialManager  import MaterialManager
from Utils import *
from OpenGL.raw.GL.VERSION.GL_4_5 import glGetTextureSubImage   

# todo: 
#replace the datadict structure with a static numpy array (large enough) and a index to free element
# the same for indexes. this will avoid a call to np.array during drawing reducing lag
# in case we reach the max size of the array a "resize" can be called during get_triangles
# 


class SurfaceNode:
    MAX_DEPTH = 20
    MIN_DEPTH = -1
    GRID = 16
    K_DET_DIV = 3.0 #higher tessellates more
    K_DET_RED = 3.2
    Nodes = []
    NodesStats={'Nodes':0,'Triangles':0}
    
    
    def __init__(self,face,level,cfx,cfy,c00,c01,c11,c10, su,planetdesc, texatlas):
        self.su = su
        self.pd = planetdesc
        self.face = face
        self.level = level
        if level == 0:
            self.scalelevel = 0
        else:
            self.scalelevel = level-1
        self.c00 = c00
        self.c01 = c01
        self.c11 = c11
        self.c10 = c10
        self.cf = np.array([cfx,cfy]) #center of the element in face space
        self.tex_atlas = texatlas
        self.facenormal = np.cross(c10[0:3]-c00[0:3], c01[0:3]-c00[0:3])
        self.facenormal /= np.linalg.norm(self.facenormal)
        self.children = 0
        self.c0 = (self.c00+self.c11)/2
        self.facedata = {'vertex': [], 'index':[]}
        self.NodesStats['Nodes'] +=1
        self.currenttrianglecount = 0
        self.VBO_update=[False,False]
        self.sc0 = cube2sphere(self.c0[0:3])
        
        self.texture_baking = False
        self.texture_baked = False
        self.tex_id = None
        #pre initialize internal calculation arrays, to speed up during update
        self.cd00 = np.zeros(9)
        self.cd01 = np.zeros(9)
        self.cd10 = np.zeros(9)
        self.cd11 = np.zeros(9)
        self.ustep = np.zeros(9)
        self.vstep = np.zeros(9)
        self.zstep = np.zeros(9)
        self.zstep = np.array([0.0,0.0,0.0,0.0,0.0,0.0,0.001,0.0,0.0],dtype='float32')
        self.texture_baking = False
        self.vertici = np.zeros(10000)
        
        #code for lod texturing
        self.Prepare_Own_Lod_Texture(0)
        
        
    def divide(self):
        if (self.children == 0) and (self.level <= self.MAX_DEPTH): #qui anche possibile limitare la profondita
            
            #split the node
            c02 = (self.c00+self.c01)/2
            c20 = (self.c00+self.c10)/2
            c12 = (self.c10+self.c11)/2
            c21 = (self.c01+self.c11)/2
            c22 = np.array(self.c0)
            cfdelta = 1.0/(2**(self.level+1))
            cfx = self.cf[0]
            cfy = self.cf[1]
            self.children=[SurfaceNode(self.face,self.level+1,cfx-cfdelta,cfy-cfdelta,np.array(self.c00),np.array(c02),np.array(c22),np.array(c20),self.su,self.pd,self.tex_atlas)]
            self.children.append(SurfaceNode(self.face,self.level+1,cfx+cfdelta,cfy-cfdelta,np.array(c20),np.array(c22),np.array(c12),np.array(self.c10),self.su,self.pd,self.tex_atlas))
            self.children.append(SurfaceNode(self.face,self.level+1,cfx+cfdelta,cfy+cfdelta,np.array(c22),np.array(c21),np.array(self.c11),np.array(c12),self.su,self.pd,self.tex_atlas))
            self.children.append(SurfaceNode(self.face,self.level+1,cfx-cfdelta,cfy+cfdelta,np.array(c02),np.array(self.c01),np.array(c21),np.array(c22),self.su,self.pd,self.tex_atlas))
            return 1
        else: return 0
            
    def reduce(self,asktexture = False):
        if (self.children > 0) and (self.level > self.MIN_DEPTH):
            if (self.Has_Tex_Id()<>None) or (asktexture == False):
                for ch in self.children:
                    ch.reduce()
                    ch.Free_texture()
                    del ch
                self.children = 0
                self.NodesStats['Nodes'] -=4
                return 1
            else:
                if self.texture_baked == True:
                    #ok go
                    return 0
                else:
                    if self.texture_baking== True:
                        return 0
                    else:
                        #chiedi di generare una texture se non gia in corso
                        self.Prepare_Own_Lod_Texture(0)
                        return 0

        else: 
            return 0
     
    def do_triangles(self,force_completion = False):
        #per il momento presuppone che datadict sia un dizionario con campi 'vertex' e 'index'
        #se l'oggetto e una foglia
        self.VBO_update = [False,False]
        self.datadict = {'vertex': [], 'index':[]}
        if self.datadict['vertex'] == []:
            len = 0
        else:
            len = self.datadict['vertex'].__len__()
         
        if force_completion:
            if self.children == 0:
                self.get_triangles(self.datadict,True)
            else:
                for ch in self.children:
                    ch.get_triangles(self.datadict,True)
            self.do_triangles_finalize(True)
        else:      
            if self.children == 0:
                RequestManager.add_request(self.get_triangles,[self.datadict],'get_triangles'+str(self.face),self.NodePriority)
            else:
                for ch in self.children:
                    RequestManager.add_request(ch.get_triangles,[self.datadict],'get_triangles'+str(ch.face),ch.NodePriority)
            #now the job that have to be executed last
            RequestManager.add_request(self.do_triangles_finalize,[],'get_triangles'+str(self.face),self.MinimumPriority)

        
    def do_triangles_finalize(self,force_completion=False):
        #before doing anything let's check if a texture is baking
        if (self.texture_baking == True) and (force_completion == False):
            #reschedule and exit
            RequestManager.add_request(self.do_triangles_finalize,[],'get_triangles'+str(self.face),self.MinimumPriority)
        else:
            #update triangle count info
            self.NodesStats['Triangles'] -= self.currenttrianglecount
            self.currenttrianglecount = self.datadict['index'].__len__()
            self.NodesStats['Triangles'] += self.currenttrianglecount
            t01 = time.time()*1000
            self.vertici = np.concatenate(self.datadict['vertex'])
            self.indici = np.array(self.datadict['index'],dtype='uint32')

            print(" ****  time conversion to nparrays: "+str(time.time()*1000-t01))
            self.VBO_update = [True,True]
        
    def get_triangles(self,datadict,force_completion = False):
        #before doing anything let's check if a texture is baking
        if (self.texture_baking == True) and (force_completion == False) and False:
            #reschedule and exit
            RequestManager.add_request(self.get_triangles,[datadict],'get_triangles'+str(self.face),self.NodePriority)
        else:
            if datadict['vertex'] == []:
                len = 0
            else:
                len = datadict['vertex'].__len__()
                
            if self.children == 0:
                #add all vertexes of this node to the data dictionary
                self.ustep = (self.c01 - self.c00)/float(self.GRID)
                self.vstep = (self.c10 - self.c00)/float(self.GRID)
                self.ustep[6] = 0.0
                self.vstep[6] = 0.0
                diag = 0
                offset = 0
                #nodescale = 2**self.scalelevel
                for u in range(0,self.GRID):
                    u_ustep = u*self.ustep
                    for v in range(0,self.GRID):
                        self.cd00 = self.c00+v*self.vstep+u_ustep
                        self.cd01 = self.cd00 + self.ustep
                        self.cd10 = self.cd00 + self.vstep
                        self.cd11 = self.cd01 + self.vstep

                        datadict['vertex'].append(self.cd00)
                        datadict['vertex'].append(self.cd10)
                        datadict['vertex'].append(self.cd11)
                        datadict['vertex'].append(self.cd01)
                        if diag == 0:
                            datadict['index'].extend([0+len+offset,2+len+offset,3+len+offset])
                            datadict['index'].extend([0+len+offset,1+len+offset,2+len+offset])
                        else:
                            datadict['index'].extend([0+len+offset,1+len+offset,3+len+offset])
                            datadict['index'].extend([3+len+offset,1+len+offset,2+len+offset])                       
                        offset += 4
                        diag = 1-diag
                    diag = 1-diag # at column's end double inversion to make a diamond at the new column
                    
                #emit the skirts
                for u in range(0,self.GRID):
                    u_ustep = u*self.ustep
                    self.cd00 = self.c00+u_ustep
                    self.cd01 = self.cd00+self.ustep
                    self.cd10 = self.cd00 - self.zstep
                    self.cd11 = self.cd01 - self.zstep  
                    datadict['vertex'].append(self.cd00)
                    datadict['vertex'].append(self.cd10)
                    datadict['vertex'].append(self.cd11)
                    datadict['vertex'].append(self.cd01)
                    datadict['index'].extend([0+len+offset,3+len+offset,2+len+offset])
                    datadict['index'].extend([0+len+offset,2+len+offset,1+len+offset])
                    offset += 4
                    self.cd00 = self.c10+u_ustep
                    self.cd01 = self.cd00+self.ustep
                    self.cd10 = self.cd00 - self.zstep
                    self.cd11 = self.cd01 - self.zstep 
                    datadict['vertex'].append(self.cd00)
                    datadict['vertex'].append(self.cd10)
                    datadict['vertex'].append(self.cd11)
                    datadict['vertex'].append(self.cd01)
                    datadict['index'].extend([0+len+offset,2+len+offset,3+len+offset])
                    datadict['index'].extend([0+len+offset,1+len+offset,2+len+offset])
                    offset += 4
                for v in range(0,self.GRID):
                    v_vstep = v*self.vstep
                    self.cd00 = self.c00+v_vstep
                    self.cd01 = self.cd00+self.vstep
                    self.cd10 = self.cd00 - self.zstep
                    self.cd11 = self.cd01 - self.zstep  
                    datadict['vertex'].append(self.cd00)
                    datadict['vertex'].append(self.cd10)
                    datadict['vertex'].append(self.cd11)
                    datadict['vertex'].append(self.cd01)
                    datadict['index'].extend([0+len+offset,2+len+offset,3+len+offset])
                    datadict['index'].extend([0+len+offset,1+len+offset,2+len+offset])
                    offset += 4
                    self.cd00 = self.c01+v_vstep
                    self.cd01 = self.cd00+self.vstep
                    self.cd10 = self.cd00 - self.zstep
                    self.cd11 = self.cd01 - self.zstep 
                    datadict['vertex'].append(self.cd00)
                    datadict['vertex'].append(self.cd10)
                    datadict['vertex'].append(self.cd11)
                    datadict['vertex'].append(self.cd01)
                    datadict['index'].extend([0+len+offset,3+len+offset,2+len+offset])
                    datadict['index'].extend([0+len+offset,2+len+offset,1+len+offset])
                    offset += 4
                    
                
            else:
                if force_completion:
                    for ch in self.children:
                        ch.get_triangles(datadict,True)
                else:
                    for ch in self.children:
                        RequestManager.add_request(ch.get_triangles,[datadict],'get_triangles'+str(ch.face),ch.NodePriority)
                        
    def tessellate_all_to_level(self,level):
        #this is a test code
        self.divide()
        if (self.children <>0) and (level>0):
            for ch in self.children: ch.tessellate_all_to_level(level-1)
            
            
    def tessellate_by_distance(self,cam_pos,offset,k_det_div = 3.0,k_det_red = 3.2):
        #returns zero if no update is necessary
        #calculate distance from camera and save it for other purposes
        self.dist = np.linalg.norm(cam_pos-self.sc0)-offset
        ret = 0
        if self.children <> 0:
            for ch in self.children: ret += ch.tessellate_by_distance(cam_pos,offset,k_det_div,k_det_red)
        if self.dist < k_det_div/(2.0**self.level):
            ret += self.divide()
        elif self.dist >= k_det_red/(2.0**self.level): 
            ret += self.reduce(True)
        else: ret += 0

        return ret 
            
    def set_tex_id(self,id):
        self.tex_id = id
        
    def NeedUpdate(self,index):
        if hasattr(self, 'VBO_update'):
            return self.VBO_update[index]
        
    def VBO_Updated(self,index):
            self.VBO_update[index] = False
            
    def VBO_All_Updated(self):
            self.VBO_update = [False,False]
            
    def Rescale_Tex_Coord(self,T00x,T00y,Dx,Dy):
        #determine current lower left corner and sizes:
        L = [self.c00,self.c10,self.c01,self.c11]
        tox = 1.0
        toy = 1.0
        tdx = 0.0
        tdy = 0.0
        for C in L:
            if C[3]<tox: tox = C[3]
            if C[4]<toy: toy = C[4]
        for C in L:
            if (C[3]-tox)>tdx: tdx=C[3]-tox
            if (C[4]-toy)>tdy: tdy=C[4]-toy
        #rescale and shift the tex_coords
        L.extend([self.c0])
        for C in L:
            C[3] = (((C[3]-tox) / tdx) * Dx)+T00x
            C[4] = (((C[4]-toy) / tdy) * Dy)+T00y
            self.scalelevel = self.level
        
        if self.children >0: #propagate rescaling to children nodes
            self.children[0].Rescale_Tex_Coord(T00x,T00y,Dx/2.0,Dy/2.0)
            self.children[1].Rescale_Tex_Coord(T00x+Dx/2.0,T00y,Dx/2.0,Dy/2.0)
            self.children[2].Rescale_Tex_Coord(T00x+Dx/2.0,T00y+Dy/2.0,Dx/2.0,Dy/2.0)
            self.children[3].Rescale_Tex_Coord(T00x,T00y+Dy/2.0,Dx/2.0,Dy/2.0)
            
        
    def Assign_TexAtlas_Layer(self,index):
        L = [self.c00,self.c10,self.c01,self.c11,self.c0]
        self.tex_atlas.add_tex_user(index,self)
        self.set_tex_id(index)
        for C in L:
            C[5] = index
        if self.children <>0:
            for Ch in self.children: Ch.Assign_TexAtlas_Layer(index)

    def Free_texture(self):
        index = int(self.c00[5])
        self.tex_atlas.remove_tex_user(index,self)
        self.tex_id = None
        self.texture_baked = False
        
    def Prepare_Own_Lod_Texture(self,step):
        if step == 0: #just reserve a tex slot and schedule execution of 1step
            if self.level <self.MAX_DEPTH and self.tex_atlas.count_free_slots()>0:
                self.temp_slot = self.tex_atlas.reserve_slot(self)
                self.texture_baking = True
                RequestManager.add_request(self.Prepare_Own_Lod_Texture,[1],'NodeTexBaking',self.Distance_From_Camera)
     
        if step == 1: #prepare height texture
            self.su['fbo'].set_fbo_scene()
            self.temp_htex = self.su['fbo'].draw_fbo_cube(self.pd,self.face,'pass_1',self.cf[0],self.cf[1],self.level,0)
            #print(self.temp_htex)
            self.su['fbo'].set_base_scene()
            RequestManager.add_request(self.Prepare_Own_Lod_Texture,[2],'NodeTexBaking',self.Distance_From_Camera)
             
        if step == 2: #prepare hnorm texture
            self.su['fbo'].set_fbo_scene()
            self.temp_hnorm = self.su['fbo'].draw_fbo_cube(self.pd,self.face,'pass_2',self.cf[0],self.cf[1],self.level,self.temp_htex)
            #print(self.temp_hnorm)
            self.su['fbo'].set_base_scene()
            RequestManager.add_request(self.Prepare_Own_Lod_Texture,[3],'NodeTexBaking',self.Distance_From_Camera)
            
             
        if step == 3: #set textures and cascade text coordinates
            self.tex_atlas.fill_reserved_slot(self.temp_hnorm,self.temp_slot)
            self.Assign_TexAtlas_Layer(self.temp_slot)
            self.Rescale_Tex_Coord(0.0,0.0,1.0,1.0)
            #delete temp textures to free memory
            glDeleteTextures([self.temp_htex,self.temp_hnorm])
            self.texture_baking = False
            self.texture_baked = True
            
    def Has_Tex_Id(self):
        if hasattr(self, 'tex_id'):
            return self.tex_id
        else:
            return None 
        
    def Distance_From_Camera(self):
        if hasattr(self, 'dist'):
            return self.dist  
        else:
            return 10 
        
    def MinimumPriority(self):
        return 99999
    
    def NodePriority(self):
        return self.level
    
    def NodeTexValue(self,u,v):

        if self.children <> 0:
            if u <= self.cf[0]:
                if (v <= self.cf[1]) and (self.children[0].Has_Tex_Id()<>self.Has_Tex_Id()): return(self.children[0].NodeTexValue(u,v))
                if (v > self.cf[1]) and (self.children[3].Has_Tex_Id()<>self.Has_Tex_Id()): return(self.children[3].NodeTexValue(u,v))
            else:
                if (v <= self.cf[1]) and (self.children[1].Has_Tex_Id()<>self.Has_Tex_Id()): return(self.children[1].NodeTexValue(u,v))
                if (v > self.cf[1]) and (self.children[2].Has_Tex_Id()<>self.Has_Tex_Id()): return(self.children[2].NodeTexValue(u,v))
        #if it arrives here, have to return its value
        #given node level, u and v,  node center in uv space (cf) , rescale the u and v to tex level
        scale = (2.0**self.level)
        ut = scale * (u - self.cf[0])
        vt = scale * (v - self.cf[1])
        si = 0.02 # si: sampling interval, the range around vt and ut which will be sampled
        # rescale from -1..+1 to 0..+1:
        ut = ut * 0.5 +0.5
        vt = vt * 0.5 +0.5
        #call the testure array method to retrieve the value
        data = self.tex_atlas.Evaluator.GetTexValue(ut-si,ut+si,vt-si,vt+si,self.Has_Tex_Id())
        self.su['fbo'].set_base_scene()
        return (self.level,data[13,13])
       
    def HaveAllChildrenTextures(self):
        #check if the node's children have own textures
        if self.children <> 0:
            all_have_textures = True
            for ch in self.children:
                if (ch.texture_baked == False): all_have_textures = False
            return all_have_textures
        else: return False 
    