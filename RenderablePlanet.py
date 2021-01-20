  
import OpenGL 

import numpy as np
import math as mt
import quaternions as qts
from quaternions import Quat
from OpenGL.arrays import vbo  
import RendObject
import random
import transformations
import time
from SurfaceNode import SurfaceNode
from RenderableSkydome import RenderableSkydome
from FBO_RTT import FBO_RTT
from RequestManager import RequestManager
from TextureAtlasArray import TextureAtlasArray
from MaterialManager import MaterialManager
from transformations import identity_matrix, scale_matrix, translation_matrix
from multiprocessing import Process
#from RenderableSkydome import RenderableSkydome
from PlanetDescriptor import PlanetDescriptor




OpenGL.ERROR_ON_COPY = True 
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# PyOpenGL 3.0.1 introduces this convenience module...
from OpenGL.GL.shaders import *

import time, sys

from Utils import *
from RendLight import RendLight




       
# our renderable planet class
class RenderablePlanet(RendObject.RendObject):
    Timer = 0
    
    
    def __init__(self,type, x, y, z,SceneUtils,PlanetDesc):

        # create the texture atlas for the cube 
        self.TexAtlas = TextureAtlasArray(96*4,128,128)
        self.PlanetDescriptor = PlanetDesc
        
        #in the future, the active camera should be linked to the object using a more global methods 
        # or making sceneutils a global access object
        self.ActiveCamera = SceneUtils['cam']
        self.SceneMgr = SceneUtils['fbo']
        
        #code to be put only if the planet has water bodies
        #set up a helper fbo for difraction maps
        self.helpfbo = FBO_RTT(1024,1024)
        # and one for reflection maps
        self.helpfbo2 = FBO_RTT(1024,1024)
        
        # state of the main texture data: 0 = full, <>0, not fully completed
        self.state = 1
        

        #create the cube face object
        # - define corners
        c000 = np.array([-1.0,-1.0,1.0],dtype='float32')
        c010 = np.array([-1.0,1.0,1.0],dtype='float32')
        c110 = np.array([1.0,1.0,1.0],dtype='float32')
        c100 = np.array([1.0,-1.0,1.0],dtype='float32')
        c001 = np.array([-1.0,-1.0,-1.0],dtype='float32')
        c011 = np.array([-1.0,1.0,-1.0],dtype='float32')
        c111 = np.array([1.0,1.0,-1.0],dtype='float32')
        c101 = np.array([1.0,-1.0,-1.0],dtype='float32')
        t00 = np.array([0.0,0.0,0.0,1.0,0.0,0.0],dtype='float32')
        t10 = np.array([1.0,0.0,0.0,1.0,1.0,0.0],dtype='float32')
        t11 = np.array([1.0,1.0,0.0,1.0,1.0,1.0],dtype='float32')
        t01 = np.array([0.0,1.0,0.0,1.0,0.0,1.0],dtype='float32')
        # - create the 6 cube faces, specifying vertices and texture coordinates with np.lib.append([x,y,z],[s,t]) calls
        self.face = []
        self.face.append(SurfaceNode(0,0,0,0,np.lib.append(c000,t00),np.lib.append(c010,t01),np.lib.append(c110,t11),np.lib.append(c100,t10),SceneUtils,PlanetDesc,self.TexAtlas))
        self.face.append(SurfaceNode(1,0,0,0,np.lib.append(c001,t00),np.lib.append(c011,t01),np.lib.append(c010,t11),np.lib.append(c000,t10),SceneUtils,PlanetDesc,self.TexAtlas))
        self.face.append(SurfaceNode(2,0,0,0,np.lib.append(c101,t00),np.lib.append(c111,t01),np.lib.append(c011,t11),np.lib.append(c001,t10),SceneUtils,PlanetDesc,self.TexAtlas))
        self.face.append(SurfaceNode(3,0,0,0,np.lib.append(c100,t00),np.lib.append(c110,t01),np.lib.append(c111,t11),np.lib.append(c101,t10),SceneUtils,PlanetDesc,self.TexAtlas))
        self.face.append(SurfaceNode(4,0,0,0,np.lib.append(c001,t00),np.lib.append(c000,t01),np.lib.append(c100,t11),np.lib.append(c101,t10),SceneUtils,PlanetDesc,self.TexAtlas))
        self.face.append(SurfaceNode(5,0,0,0,np.lib.append(c010,t00),np.lib.append(c011,t01),np.lib.append(c111,t11),np.lib.append(c110,t10),SceneUtils,PlanetDesc,self.TexAtlas))
        
        # generate heigthmap
        #self.GenHeightMapTex(SceneUtils['fbo'])
        RequestManager.add_request(self.CheckLevelZeroTexComplete,[])


        for aface in self.face:
            #aface.tessellate_all_to_level(2)
            aface.do_triangles(True)
            aface.VBO_All_Updated()
         
        #parameters for dynamic level of detail
        self.kdiv = 3.0
        self.kred = 3.2  

        leng = 0
        
        self.activeVBO = [0,0,0,0,0,0]  #implementing doublevbo
        self.VBO_need_update = [3,3,3,3,3,3] # to check
        self.sidetocheck = 6 #temporarily we check one side at a time to see if we tessellate
        self.updatelist = []
        self.vbotocomplete = [7,7] #face number and active number
        
        self.vertexVBO = [[]]
        self.indexVBO = [[]]
        self.vertexVBO.append([])
        self.indexVBO.append([])
        index = 0
        for i in self.face:
            i.faceindex = index
            index += 1
            self.vertici = np.array(np.array(i.datadict['vertex'],dtype='float32'))
            self.vertexVBO[0].append(vbo.VBO(data=self.vertici, usage=GL_DYNAMIC_DRAW, target=GL_ARRAY_BUFFER))
            self.vertexVBO[1].append(vbo.VBO(data=self.vertici, usage=GL_DYNAMIC_DRAW, target=GL_ARRAY_BUFFER))
            self.indici = np.array(np.array(i.datadict['index'],dtype='uint32'))
            self.indexVBO[0].append(vbo.VBO(data=self.indici, usage=GL_DYNAMIC_DRAW,target=GL_ELEMENT_ARRAY_BUFFER))
            self.indexVBO[1].append(vbo.VBO(data=self.indici, usage=GL_DYNAMIC_DRAW,target=GL_ELEMENT_ARRAY_BUFFER)) 
            leng += self.vertici.shape[0]       

        

        
        # assign other object properties
        self.scale = PlanetDesc.radius
        self.position = [x,y,z]
        self.orientation = qts.Quat([0.0,0.3,0.5])
        
        #add a light as a test ..light should not be there
        self.light = RendLight((2000000.0,0.0,0.0),(1.0,1.0,0.8))
        
        #add a test skydome object
        self.sky = RenderableSkydome(16)
        self.sky.attach_light(self.light)
        
        # assign the shader and get attribute and uniform indexes (pointers)
        self.program = MaterialManager.Materials[PlanetDesc.main_material]
        self.program_sea = MaterialManager.Materials['planetsea']
        self.attrib_position = glGetAttribLocation(self.program,'position')
        self.attrib_texcoord = glGetAttribLocation(self.program,'texcoord')
        self.attrib_texcoord2 = glGetAttribLocation(self.program,'texcoord2')
        self.attrib_scale = glGetAttribLocation(self.program,'nodescale')

        self.main_attribs={'position': glGetAttribLocation(self.program, 'position'),
                            'texcoord': glGetAttribLocation(self.program, 'texcoord'),
                            'nodescale': glGetAttribLocation(self.program, 'nodescale'),
                            'texcoord2': glGetAttribLocation(self.program, 'texcoord2'),
            }

        self.sea_attribs={'position': glGetAttribLocation(self.program_sea, 'position'),
                            'texcoord': glGetAttribLocation(self.program_sea, 'texcoord'),
                            'nodescale': glGetAttribLocation(self.program_sea, 'nodescale'),
                            'texcoord2': glGetAttribLocation(self.program_sea, 'texcoord2'),
            }

        self.main_unifs={'u_model': glGetUniformLocation(self.program, 'u_model'),
                         'u_view': glGetUniformLocation(self.program, 'u_view'),
                         'u_normal': glGetUniformLocation(self.program, 'u_normal'),
                         'u_proj': glGetUniformLocation(self.program, 'u_proj'),
                         'u_lposition3': glGetUniformLocation(self.program, 'u_lposition3'),
                         'u_lintensity3': glGetUniformLocation(self.program, 'u_lintensity3'),
                         'planet_radius': glGetUniformLocation(self.program, 'planet_radius'),
                         'planet_height': glGetUniformLocation(self.program, 'planet_height'),
                         'sea_level': glGetUniformLocation(self.program, 'sea_level'),
                         'camdist': glGetUniformLocation(self.program, 'camdist'),
                         'skirt_off': glGetUniformLocation(self.program, 'skirt_off'),
                         'state': glGetUniformLocation(self.program, 'state'),
                         'verse': glGetUniformLocation(self.program, 'verse'),

            }
        self.sea_unifs={'model_m': glGetUniformLocation(self.program_sea, 'model_m'),
                         'view_m': glGetUniformLocation(self.program_sea, 'view_m'),
                         'normal_m': glGetUniformLocation(self.program_sea, 'normal_m'),
                         'proj_m': glGetUniformLocation(self.program_sea, 'proj_m'),
                         'u_lposition3': glGetUniformLocation(self.program_sea, 'u_lposition3'),
                         'u_lintensity3': glGetUniformLocation(self.program_sea, 'u_lintensity3'),
                         'planetradius': glGetUniformLocation(self.program_sea, 'planetradius'),
                         'planetheight': glGetUniformLocation(self.program_sea, 'planetheight'),
                         'sealevel': glGetUniformLocation(self.program_sea, 'sealevel'),
                         'time': glGetUniformLocation(self.program_sea, 'time'),
                         'camdist': glGetUniformLocation(self.program_sea, 'camdist'),
                         'skirt_off': glGetUniformLocation(self.program_sea, 'skirt_off'),


            }


        # inscribe the object in the static list of the parent object
        RenderablePlanet.ListRends.append(self)
        # funny test code
        rand_axis = np.array([random.random(),random.random(),random.random()])
        norma = np.linalg.norm(rand_axis)
        rand_axis /= norma
        #self.axis = np.array([0.0,1.0,0.0])
        self.axis = rand_axis
        self.rand_angle = 0.000 * (random.uniform(0.0,20.0)-10)
        self.cam_distance = 10
        ##test signals for the hud

        GlobalSignals.set('Triangles', leng)
        GlobalSignals.set('req nr', 0)
        GlobalSignals.set('req max time', 0)
        GlobalSignals.set('draw ms', 0)
        GlobalSignals.set('tessel ms', 0)
        GlobalSignals.set('tex slot free', 0)
        GlobalSignals.set('Nodes', leng)

        
    def draw(self):
        #pre draw stuff and preparation
        t1 = time.time()*1000
        
        if GlobalSettings.read('linemode') == GL_LINE:
            skirt_off = 1.0
        else:
            skirt_off = 0.0
            
        #apply local transformations
        selfrot = np.ascontiguousarray(np.transpose(np.append(np.append(self.orientation._get_transform(),[[0],[0],[0]],1),[[0,0,0,1]],0)))
        S = scale_matrix(self.scale)
        R = selfrot
        T = translation_matrix(self.position)
        self.model= np.dot(T,np.dot(R,S))
        #calculate mirror matrix
        #normalize camera position in object space
        selfrot = np.ascontiguousarray(np.transpose(np.append(np.append(self.orientation._get_transform(),[[0],[0],[0]],1),[[0,0,0,1]],0)))
        Si = scale_matrix(float(1/self.scale))
        Ri = np.transpose(selfrot)
        Ti = translation_matrix([-self.position[0],-self.position[1],-self.position[2]])
        Minv= np.dot(Si,np.dot(Ri,Ti))
        self.campostr = np.ravel(np.dot(Minv,np.append(self.ActiveCamera.position,1)))[0:3]
        self.cam_distance = np.linalg.norm(self.campostr)
        GlobalSignals.set('cam distance', self.cam_distance)
        
        #mcamera = np.dot(flip,np.dot(mirror,np.linalg.inv(self.ActiveCamera.view)))
        #mview = self.ActiveCamera.view
        
        if (self.cam_distance < 1.3) and (self.PlanetDescriptor.sea_level>0) and (self.state == 0):
            self.draw_fbo_refraction()
            self.draw_fbo_reflection(self.ActiveCamera.view)



        
        #test draw the sky if we are inside
        if (self.cam_distance <= 100):
            glBlendFunc (GL_SRC_ALPHA, GL_ZERO)
            #glDisable(GL_CULL_FACE)
            glCullFace(GL_FRONT)
            self.sky.draw_inner_sky(self.ActiveCamera.proj,self.ActiveCamera.view,self.model)
            #glEnable(GL_CULL_FACE)
            glCullFace(GL_BACK)
           
            
        #draw the planet 
        
        glBlendFunc (GL_ONE, GL_ZERO)  
        MaterialManager.use_material('planetmat1')       
        #glUseProgram(self.program)
        
        glEnableVertexAttribArray(self.main_attribs['position'])
        glEnableVertexAttribArray(self.main_attribs['texcoord'])
        glEnableVertexAttribArray(self.main_attribs['nodescale'])
        glEnableVertexAttribArray(self.main_attribs['texcoord2'])
        
        glUniformMatrix4fv(self.main_unifs['u_model'],1,GL_TRUE,self.model)
        glUniformMatrix4fv(self.main_unifs['u_view'],1,GL_FALSE,self.ActiveCamera.view)
        glUniformMatrix4fv(self.main_unifs['u_normal'],1,GL_FALSE,np.transpose(np.linalg.inv(np.dot(np.transpose(self.model),self.ActiveCamera.view))))
        glUniformMatrix4fv(self.main_unifs['u_proj'],1,GL_FALSE,self.ActiveCamera.proj)
        
        glUniform3fv(self.main_unifs['u_lposition3'],1,self.light.get_pos())
        glUniform3fv(self.main_unifs['u_lintensity3'],1,self.light.get_intensity())


        glUniform1f(self.main_unifs['planet_radius'],self.PlanetDescriptor.radius)
        glUniform1f(self.main_unifs['planet_height'],self.PlanetDescriptor.height)
        glUniform1f(self.main_unifs['sea_level'],self.PlanetDescriptor.sea_level)
        glUniform1f(self.main_unifs['camdist'],self.cam_distance)
        glUniform1f(self.main_unifs['skirt_off'],skirt_off)
        glUniform1i(self.main_unifs['state'],self.state)
        glUniform1f(self.main_unifs['verse'],1.0)
         
        glEnable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.PlanetDescriptor.mixmap)
        glUniform1i(glGetUniformLocation(self.program,'surfacecolor'),0)
        
        #bind the texture (from texture atlas array) for heightmap / normals
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.TexAtlas.get_tex_id())
        glUniform1i(glGetUniformLocation(self.program,'heightmap'),1)
        
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.PlanetDescriptor.surface_textures.get_tex_id())
        glUniform1i(glGetUniformLocation(self.program,'surface'),2)
        #draw pass of the 6 VBOs
        for index in range(0,6):
        
            #bind the VBO
            act = self.activeVBO[index]
            self.vertexVBO[act][index].bind()
            self.indexVBO[act][index].bind()
            #draw
            glVertexAttribPointer(self.attrib_position,3,GL_FLOAT,GL_FALSE,36,self.vertexVBO[act][index])
            glVertexAttribPointer(self.attrib_texcoord,3,GL_FLOAT,GL_FALSE,36,self.vertexVBO[act][index]+(3*4))
            glVertexAttribPointer(self.attrib_scale,1,GL_FLOAT,GL_FALSE,36,self.vertexVBO[act][index]+(6*4))
            glVertexAttribPointer(self.attrib_texcoord2,2,GL_FLOAT,GL_FALSE,36,self.vertexVBO[act][index]+(7*4))
            nb_elements = self.indexVBO[act][index].shape[0]
            glDrawElements(GL_TRIANGLES,nb_elements,GL_UNSIGNED_INT,self.indexVBO[act][index])
            # disable/unbind the arrays
            self.vertexVBO[act][index].unbind()
            self.indexVBO[act][index].unbind()

        glDisableVertexAttribArray(self.main_attribs['position'])
        glDisableVertexAttribArray(self.main_attribs['texcoord'])
        glDisableVertexAttribArray(self.main_attribs['nodescale'])
        glDisableVertexAttribArray(self.main_attribs['texcoord2'])
           
        # draw the sea
        #glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        if (self.cam_distance < 1.05) and (self.PlanetDescriptor.sea_level>0) and (GlobalSettings.read('nosea')) and (self.state == 0 ):
            glUseProgram(self.program_sea)
            #enable attributes arrays      
            glEnableVertexAttribArray(self.sea_attribs['position'])
            glEnableVertexAttribArray(self.sea_attribs['texcoord'])
            glEnableVertexAttribArray(self.sea_attribs['nodescale'])
            glEnableVertexAttribArray(self.sea_attribs['texcoord2'])

            glUniformMatrix4fv(self.sea_unifs['model_m'],1,GL_TRUE,self.model)
            glUniformMatrix4fv(self.sea_unifs['view_m'],1,GL_FALSE,self.ActiveCamera.view)
            glUniformMatrix4fv(self.sea_unifs['normal_m'],1,GL_FALSE,np.transpose(np.linalg.inv(np.dot(np.transpose(self.model),self.ActiveCamera.view))))
            glUniformMatrix4fv(self.sea_unifs['proj_m'],1,GL_FALSE,self.ActiveCamera.proj)
            
            glUniform3fv(self.sea_unifs['u_lposition3'],1,self.light.get_pos())
            glUniform3fv(self.sea_unifs['u_lintensity3'],1,self.light.get_intensity())
            
            glUniform1f(self.sea_unifs['planetradius'],self.PlanetDescriptor.radius)
            glUniform1f(self.sea_unifs['planetheight'],self.PlanetDescriptor.height)
            glUniform1f(self.sea_unifs['sealevel'],self.PlanetDescriptor.sea_level)
            glUniform1f(self.sea_unifs['time'],time.clock())
            glUniform1f(self.sea_unifs['camdist'],self.cam_distance)
            glUniform1f(self.sea_unifs['skirt_off'],skirt_off)
            
            glEnable(GL_TEXTURE_2D)
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D_ARRAY, self.PlanetDescriptor.wavetext)
            glUniform1i(glGetUniformLocation(self.program_sea,'wavetext'),0)
            
            #bind the texture (from texture atlas array) for heightmap / normals
            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D_ARRAY, self.TexAtlas.get_tex_id())
            glUniform1i(glGetUniformLocation(self.program_sea,'heightmap'),1)
            
            glActiveTexture(GL_TEXTURE2)
            glBindTexture(GL_TEXTURE_2D, self.helpfbo.rtt)
            glUniform1i(glGetUniformLocation(self.program_sea,'refractiontexture'),2)
            
            glActiveTexture(GL_TEXTURE3)
            glBindTexture(GL_TEXTURE_2D, self.helpfbo2.rtt)
            glUniform1i(glGetUniformLocation(self.program_sea,'reflectiontexture'),3)
            
            for index in range(0,6):
                
                #bind the VBO
                act = self.activeVBO[index]
                self.vertexVBO[act][index].bind()
                self.indexVBO[act][index].bind()
                #draw
                glVertexAttribPointer(self.attrib_position,3,GL_FLOAT,GL_FALSE,36,self.vertexVBO[act][index])
                glVertexAttribPointer(self.attrib_texcoord,3,GL_FLOAT,GL_FALSE,36,self.vertexVBO[act][index]+(3*4))
                glVertexAttribPointer(self.attrib_scale,1,GL_FLOAT,GL_FALSE,36,self.vertexVBO[act][index]+(6*4))
                glVertexAttribPointer(self.attrib_texcoord2,2,GL_FLOAT,GL_FALSE,36,self.vertexVBO[act][index]+(7*4))
                nb_elements = (self.indexVBO[act][index].shape[0])
                glDrawElements(GL_TRIANGLES,nb_elements,GL_UNSIGNED_INT,self.indexVBO[act][index])
                # disable/unbind the arrays
                self.vertexVBO[act][index].unbind()
                self.indexVBO[act][index].unbind()

            glDisableVertexAttribArray(self.sea_attribs['position'])
            glDisableVertexAttribArray(self.sea_attribs['texcoord'])
            glDisableVertexAttribArray(self.sea_attribs['nodescale'])
            glDisableVertexAttribArray(self.sea_attribs['texcoord2'])

        
        #test draw the sky if we are outside
        if (self.cam_distance >= 1.1):
            glBlendFunc (GL_SRC_ALPHA, GL_ONE)
            glCullFace(GL_BACK)
            self.sky.draw_inner_sky(self.ActiveCamera.proj,self.ActiveCamera.view,self.model)


        glUseProgram(0)
        
        #VBO updating / maintenance
        for index in range(0,6):
            #check if current face has a VBO to complete update
            if self.VBO_need_update[index] <> 3:
                RequestManager.add_request(self.VBOupdate,[index])
            #swap active VBO if no pending updates
            if self.VBO_need_update[index] <> (1-act):
                self.activeVBO[index] = 1-act
            
        #debug code
        t2 = time.time()*1000-t1
        GlobalSignals.set('draw ms', t2)
        GlobalSignals.set('tex slot free', self.TexAtlas.free_count) 
        #test
          

        
    def update(self):
        #funny test: rotate o fa fraction around the rand_axis
        ca = np.cos(self.rand_angle/2)
        sa = np.sin(self.rand_angle/2)
        v = np.append(self.axis*sa,ca)
        qr = qts.Quat(v)
        self.orientation = qr.__mul__(self.orientation) 
        

        
        #adapt near plane to current distance
        obj_space_distance = np.linalg.norm(self.ActiveCamera.position - self.position)/self.scale
        near_plane = smoothstephilo(0.1,10,1.005,1.1,obj_space_distance)
        self.ActiveCamera.set_near_far(near_plane ,200000.0)
        GlobalSignals.set('near distance: ',near_plane  )
        #check if we tessellate
        RequestManager.add_request(self.CheckTessellation,[])
        
        #check if a reduction of lod is required
        if self.TexAtlas.free_below_level(0.05):
            self.kdiv *= 0.995
            self.kred *= 0.995
        elif self.kdiv < 3.0 and self.TexAtlas.free_over_level(0.25):
            self.kdiv *=1.001
            self.kred *=1.001
            
        GlobalSignals.set('kdiv: ',self.kdiv)
        GlobalSignals.set('kred: ',self.kred)


        #debug
        GlobalSignals.set('req nr', RequestManager.get_queue_length())
        GlobalSignals.set('req max time', RequestManager.get_queue_max_wait_time_ms())
        GlobalSignals.set('size of patch:',2*3.14*self.PlanetDescriptor.radius/4/(2**GlobalSignals.read('level:')))
        GlobalSignals.set('size of unit:',GlobalSignals.read('size of patch:')/16)


    def CheckTessellation(self):
        t1 = time.time()*1000
        #retrieve the camera position in objectspace 
        campostr = self.campostr

        self.GetHeightFieldValue(campostr)


        #check if there are cube faces to update from previous loop, otherwise, re-evaluate the needs
        if self.updatelist ==[]:  # the list of required updates is empty, reevaluate priorities
            #compute for each face the dot product with oncubecam
            #then sort the refresh order by this value
            for oneface in self.face:
                dotp = np.dot(campostr,oneface.facenormal)
                #if dotp >=0.0:
                self.updatelist.append([dotp,oneface])

            #sort the list by dot product decreasing
            if self.updatelist <>[]:
                self.updatelist.sort(key=lambda el:el[0], reverse=True)
            
        else: # the are updates to complete from previous cycles
            curr_face = self.updatelist[0][1] #get the second element (face pointer) of the first element of the update list
            normalized_surface_height = GlobalSignals.read('height:')* self.PlanetDescriptor.height/self.PlanetDescriptor.radius
            if curr_face.tessellate_by_distance(campostr,normalized_surface_height,self.kdiv,self.kred)>0: #check the tessellation by distance
                    RequestManager.add_request(curr_face.do_triangles,[])
                    self.VBO_need_update[self.face.index(curr_face)]=2
            del self.updatelist[0]
        GlobalSignals.set('Nodes',self.face[0].NodesStats['Nodes'])
        GlobalSignals.set('Triangles',self.face[0].NodesStats['Triangles'])

            #debug code
        t2 = time.time()*1000-t1
        GlobalSignals.set('tessel ms', t2)
        

    
    def VBOupdate(self,vboindex):
        nact = 1-self.activeVBO[vboindex]
        if self.VBO_need_update[vboindex] == 2 and self.face[vboindex].VBO_update[nact]:
            #update the nact vbo and reschedule an update
            self.vertexVBO[nact][vboindex].set_array(self.face[vboindex].vertici)
            self.indexVBO[nact][vboindex].set_array(self.face[vboindex].indici)
            self.VBO_need_update[vboindex] = self.activeVBO[vboindex]
        if self.VBO_need_update[vboindex] == nact and self.face[vboindex].VBO_update[nact]:
            #update the vbo and it's over
            self.vertexVBO[nact][vboindex].set_array(self.face[vboindex].vertici)
            self.indexVBO[nact][vboindex].set_array(self.face[vboindex].indici)
            self.VBO_need_update[vboindex] = 3
        if (self.VBO_need_update[vboindex] == self.activeVBO[vboindex]) or (self.face[vboindex].VBO_update[nact]==False):
            #cannot update now, reschedule the update
            RequestManager.add_request(self.VBOupdate,[vboindex])
        

                    
    def GenHeightMapTex(self,SceneMgr):
        #draft code to generate the height map
        SceneMgr.set_fbo_scene()
        for i in range(0,6):
            tid = SceneMgr.draw_fbo_cube(self.PlanetDescriptor,i,'pass_1',0,0,0,0)
            tid = SceneMgr.draw_fbo_cube(self.PlanetDescriptor,i,'pass_2',0,0,0,tid)
            idx = self.TexAtlas.fill_slot(tid,self,True)
            self.face[i].Assign_TexAtlas_Layer(idx)
            self.face[i].texture_baked = True
            print('cube face '+str(i)+' done')
        SceneMgr.set_base_scene()
        self.state = 0
        
    def CheckLevelZeroTexComplete(self):
        if self.state <> 0:
            incomplete = False
            print 'checking completeness'
            for i in range(0,6):
                if not(self.face[i].texture_baked): 
                    incomplete = True
            if incomplete:
                print 'not complete, rescheduling'
                RequestManager.add_request(self.CheckLevelZeroTexComplete,[],'default',None,True)
            else: 
                self.state = 0
                #  TODO 2017 - do not work - self.TexAtlas.save_texture_atlas_bmp("test2017")
                print 'complete now'
        
    def GetProjectedSurfaceHeight(self,position):
        #given inputvector position in world space, retrieve the heighmap value 
        #for the intersection between the ray position - planetcenter and the planetsurface
        pass
    
    
    def draw_fbo_refraction(self):
        glFinish()
        self.helpfbo.pre_FBO_rendering()
        


        glBlendFunc (GL_ONE, GL_ZERO)               
        #draw the planet 
        MaterialManager.use_material('underwater')
        mat = MaterialManager.get_material('underwater')
        
        glEnableVertexAttribArray(glGetAttribLocation(mat,'position'))
        glEnableVertexAttribArray(glGetAttribLocation(mat,'texcoord'))
        glEnableVertexAttribArray(glGetAttribLocation(mat,'nodescale'))
        glEnableVertexAttribArray(glGetAttribLocation(mat,'texcoord2'))
        
        glUniformMatrix4fv(glGetUniformLocation(mat,'u_model'),1,GL_TRUE,self.model)
        glUniformMatrix4fv(glGetUniformLocation(mat,'u_view'),1,GL_FALSE,self.ActiveCamera.view) 
        glUniformMatrix4fv(glGetUniformLocation(mat,'u_normal'),1,GL_FALSE,np.transpose(np.linalg.inv(np.dot(np.transpose(self.model),self.ActiveCamera.view))))
        glUniformMatrix4fv(glGetUniformLocation(mat,'u_proj'),1,GL_FALSE,self.ActiveCamera.proj) 
        
        glUniform3fv(glGetUniformLocation(mat,'u_lposition3'),1,self.light.get_pos())
        glUniform3fv(glGetUniformLocation(mat,'u_lintensity3'),1,self.light.get_intensity())
        
        glUniform1f(glGetUniformLocation(mat,'planet_radius'),self.PlanetDescriptor.radius)
        glUniform1f(glGetUniformLocation(mat,'planet_height'),self.PlanetDescriptor.height) 
        glUniform1f(glGetUniformLocation(mat,'sea_level'),self.PlanetDescriptor.sea_level)
        glUniform1f(glGetUniformLocation(mat,'camdist'),self.cam_distance)     
         
        glEnable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.PlanetDescriptor.mixmap)
        glUniform1i(glGetUniformLocation(mat,'surfacecolor'),0)
        #bind the texture (from texture atlas array) for heightmap / normals
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.TexAtlas.get_tex_id())
        glUniform1i(glGetUniformLocation(mat,'heightmap'),1)
        
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.PlanetDescriptor.surface_textures.get_tex_id())
        glUniform1i(glGetUniformLocation(mat,'surface'),2)
        #draw pass of the 6 VBOs
        for index in range(0,6):
        
            #bind the VBO
            act = self.activeVBO[index]
            self.vertexVBO[act][index].bind()
            self.indexVBO[act][index].bind()
            #draw
            glVertexAttribPointer(self.attrib_position,3,GL_FLOAT,GL_FALSE,36,self.vertexVBO[act][index])
            glVertexAttribPointer(self.attrib_texcoord,3,GL_FLOAT,GL_FALSE,36,self.vertexVBO[act][index]+(3*4))
            glVertexAttribPointer(self.attrib_scale,1,GL_FLOAT,GL_FALSE,36,self.vertexVBO[act][index]+(6*4))
            glVertexAttribPointer(self.attrib_texcoord2,2,GL_FLOAT,GL_FALSE,36,self.vertexVBO[act][index]+(7*4))
            nb_elements = self.indexVBO[act][index].shape[0]
            glDrawElements(GL_TRIANGLES,nb_elements,GL_UNSIGNED_INT,self.indexVBO[act][index])
            # disable/unbind the arrays
            self.vertexVBO[act][index].unbind()
            self.indexVBO[act][index].unbind()
            
            
        glDisableVertexAttribArray(glGetAttribLocation(self.program,'position'))
        glDisableVertexAttribArray(glGetAttribLocation(self.program,'texcoord'))
        glDisableVertexAttribArray(glGetAttribLocation(self.program,'nodescale')) 
        glDisableVertexAttribArray(glGetAttribLocation(self.program,'texcoord2'))
        glUseProgram(0)
        #glFlush()
        
        if GlobalSettings.read('snapshot') == True:
            self.helpfbo.save_snapshot('RTTsnapshot'+str(time.time())+'.png')
            GlobalSettings.set('snapshot',False)
        
        self.helpfbo.post_FBO_rendering()
        self.SceneMgr.set_base_scene()
        
    def draw_fbo_reflection(self,viewmatrix):
        glFinish()
        self.helpfbo2.pre_FBO_rendering()
        
        glCullFace(GL_FRONT)
        self.sky.draw_inner_sky(self.ActiveCamera.proj,self.ActiveCamera.view,self.model)
        glCullFace(GL_BACK)
        
        glFrontFace(GL_CW)
        #glCullFace(GL_FRONT)
 
        glBlendFunc (GL_ONE, GL_ZERO)               
        #draw the planet 
        MaterialManager.use_material('planetmat1')
        mat = MaterialManager.get_material('planetmat1')
         
        glEnableVertexAttribArray(glGetAttribLocation(mat,'position'))
        glEnableVertexAttribArray(glGetAttribLocation(mat,'texcoord'))
        glEnableVertexAttribArray(glGetAttribLocation(mat,'nodescale'))
        glEnableVertexAttribArray(glGetAttribLocation(mat,'texcoord2'))
         
        glUniformMatrix4fv(glGetUniformLocation(mat,'u_model'),1,GL_TRUE,self.model)
        glUniformMatrix4fv(glGetUniformLocation(mat,'u_view'),1,GL_FALSE,viewmatrix) 
        glUniformMatrix4fv(glGetUniformLocation(mat,'u_normal'),1,GL_FALSE,np.transpose(np.linalg.inv(np.dot(np.transpose(self.model),viewmatrix))))
        glUniformMatrix4fv(glGetUniformLocation(mat,'u_proj'),1,GL_FALSE,self.ActiveCamera.proj) 
         
        glUniform3fv(glGetUniformLocation(mat,'u_lposition3'),1,self.light.get_pos())
        glUniform3fv(glGetUniformLocation(mat,'u_lintensity3'),1,self.light.get_intensity())
         
        glUniform1f(glGetUniformLocation(mat,'planet_radius'),self.PlanetDescriptor.radius)
        glUniform1f(glGetUniformLocation(mat,'planet_height'),self.PlanetDescriptor.height) 
        glUniform1f(glGetUniformLocation(mat,'sea_level'),self.PlanetDescriptor.sea_level)
        glUniform1f(glGetUniformLocation(mat,'camdist'),self.cam_distance)     
        glUniform1f(glGetUniformLocation(self.program,'skirt_off'),1.0)
        glUniform1f(glGetUniformLocation(self.program,'verse'),-1.0)
          
        glEnable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.PlanetDescriptor.mixmap)
        glUniform1i(glGetUniformLocation(mat,'surfacecolor'),0)
        #bind the texture (from texture atlas array) for heightmap / normals
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.TexAtlas.get_tex_id())
        glUniform1i(glGetUniformLocation(mat,'heightmap'),1)
         
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.PlanetDescriptor.surface_textures.get_tex_id())
        glUniform1i(glGetUniformLocation(mat,'surface'),2)
        #draw pass of the 6 VBOs
        for index in range(0,6):
         
            #bind the VBO
            act = self.activeVBO[index]
            self.vertexVBO[act][index].bind()
            self.indexVBO[act][index].bind()
            #draw
            glVertexAttribPointer(self.attrib_position,3,GL_FLOAT,GL_FALSE,36,self.vertexVBO[act][index])
            glVertexAttribPointer(self.attrib_texcoord,3,GL_FLOAT,GL_FALSE,36,self.vertexVBO[act][index]+(3*4))
            glVertexAttribPointer(self.attrib_scale,1,GL_FLOAT,GL_FALSE,36,self.vertexVBO[act][index]+(6*4))
            glVertexAttribPointer(self.attrib_texcoord2,2,GL_FLOAT,GL_FALSE,36,self.vertexVBO[act][index]+(7*4))
            nb_elements = self.indexVBO[act][index].shape[0]
            glDrawElements(GL_TRIANGLES,nb_elements,GL_UNSIGNED_INT,self.indexVBO[act][index])
            # disable/unbind the arrays
            self.vertexVBO[act][index].unbind()
            self.indexVBO[act][index].unbind()
             
             
        glDisableVertexAttribArray(glGetAttribLocation(self.program,'position'))
        glDisableVertexAttribArray(glGetAttribLocation(self.program,'texcoord'))
        glDisableVertexAttribArray(glGetAttribLocation(self.program,'nodescale')) 
        glDisableVertexAttribArray(glGetAttribLocation(self.program,'texcoord2'))
        glFrontFace(GL_CCW)
        glCullFace(GL_BACK)
        glUseProgram(0)
        #glFlush()
        
        
        self.helpfbo2.post_FBO_rendering()
        self.SceneMgr.set_base_scene()

    def GetHeightFieldValue(self,pos):
        #given a position in object space,
        #project the position to the planet sphere surface
        #and retrieve the heightmap value at the projction point
        pos_sphere = pos/np.linalg.norm(pos)
        (pos_cube,face) = sphere2cube(pos_sphere)
        #1 project pos onto the surface, determine: cube face and position on the cube in -1 <= u <= 1 and -1 <= v <= 1 format
        #print("CS: ",pos_sphere)
        #print("CC: ",pos_cube)
        if face == 0: u,v = pos_cube[0],pos_cube[1]
        if face == 1: u,v = pos_cube[2],pos_cube[1]
        if face == 2: u,v = -pos_cube[0],pos_cube[1]
        if face == 3: u,v = -pos_cube[2],pos_cube[1]
        if face == 4: u,v = pos_cube[0],pos_cube[2]
        if face == 5: u,v = pos_cube[0],-pos_cube[2]
        #access iteratively the nodes until the deepest node with a unique (<>than the parent) texture is found
        GlobalSignals.set('uv coords:',(u,v))
        #read the texture value at u, v, coords
        (level,height) = self.face[face].NodeTexValue(u,v)
        GlobalSignals.set('level:',level)
        GlobalSignals.set('height:',height)
        #process and ouput the texture value
        
                    