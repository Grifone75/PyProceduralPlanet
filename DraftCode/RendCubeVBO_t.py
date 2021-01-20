  
import OpenGL 

import numpy as np
import math as mt
import quaternions as qts
from quaternions import Quat
from OpenGL.arrays import vbo  
import RendObject
import random
import time
from PCube_Element import PCube_Element


OpenGL.ERROR_ON_COPY = True 
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# PyOpenGL 3.0.1 introduces this convenience module...
from OpenGL.GL.shaders import *

import time, sys

from Utils import ReadableSignal
 
def cubize(pos3):
    isqrt2 = 0.70710676908493042
    
    xx2 = pos3[0]*pos3[0]*2.0
    yy2 = pos3[1]*pos3[1]*2.0
    
    v = np.array([xx2-yy2,yy2-xx2])
    
    ii = v[1]-3.0
    ii *=ii
    
    #check
    if (ii-12.0*xx2)<0:
        t=1
        
    
    isqrt = -mt.sqrt(ii-12.0*xx2)+3.0
    v = np.sqrt(v+isqrt)
    v *=isqrt2
    
    return np.sign(pos3) * np.append(v, 1.0)
        
        
def sphere2cube(sphere3):  
    f = np.abs(sphere3)
    
    if f[1]>=f[0] and f[1]>=f[2]:
        a = np.array([sphere3[0],sphere3[2],sphere3[1]])
        b = cubize(a)
        return np.array([b[0],b[2],b[1]])
    elif f[0]>=f[2]:
        a = np.array([sphere3[1],sphere3[2],sphere3[0]])
        b = cubize(a)
        return np.array([b[2],b[0],b[1]])
    else:
        return cubize(sphere3)

    
    
    
    
       
# lets define a basic structure for a renderable object
class RendCubeVBO(RendObject.RendObject):
    Timer = 0
    
    
    def __init__(self,type, size, x, y, z, shadprog,hud):

        #create the cube face object
        # - define corners
        c000 = np.array([-1.0,-1.0,1.0])
        c010 = np.array([-1.0,1.0,1.0])
        c110 = np.array([1.0,1.0,1.0])
        c100 = np.array([1.0,-1.0,1.0])
        c001 = np.array([-1.0,-1.0,-1.0])
        c011 = np.array([-1.0,1.0,-1.0])
        c111 = np.array([1.0,1.0,-1.0])
        c101 = np.array([1.0,-1.0,-1.0])
        # - create faces
        self.face = []
        self.face.append(PCube_Element(0,c000,c010,c110,c100))
        self.face.append(PCube_Element(0,c010,c011,c111,c110))
        self.face.append(PCube_Element(0,c100,c110,c111,c101))
        self.face.append(PCube_Element(0,c000,c100,c101,c001))
        self.face.append(PCube_Element(0,c000,c001,c011,c010))
        self.face.append(PCube_Element(0,c101,c111,c011,c001))
        # this is a test
        self.face[0].tessellate_all_to_level(3)
        self.face[1].tessellate_all_to_level(3)
        self.face[2].tessellate_all_to_level(3)
        self.face[3].tessellate_all_to_level(3)
        self.face[4].tessellate_all_to_level(3)
        self.face[5].tessellate_all_to_level(3)
        # - get vettex data
        self.face[0].do_triangles()
        self.face[1].do_triangles()
        self.face[2].do_triangles()
        self.face[3].do_triangles()
        self.face[4].do_triangles()
        self.face[5].do_triangles()
        #create the vbo and ibo 
        tvert = np.array([[]])
        tind= np.array([[]])
        leng = 0
		
		self.activeVBO = [0,0,0,0,0,0]  #implementing doublevbo
        self.VBOneedupdate = [0,0,0,0,0,0] # to check
		
		self.vertexVBO = [[]]
        self.indexVBO = [[]]
		slef.vertexVBO.append([])
		slef.indexVBO.append([])
        for i in self.face:
            vertici = np.array(np.array(i.facedata['vertex'],dtype='float32')))
			self.vertexVBO[0].append(vbo.VBO(data=vertici, usage=GL_DYNAMIC_DRAW, target=GL_ARRAY_BUFFER))
			self.vertexVBO[1].append(vbo.VBO(data=vertici, usage=GL_DYNAMIC_DRAW, target=GL_ARRAY_BUFFER))
			indici = np.array(np.array(i.facedata['index'],dtype='uint16'))
			
			self.indexVBO[0].append(vbo.VBO(data=indici, usage=GL_DYNAMIC_DRAW,target=GL_ELEMENT_ARRAY_BUFFER))
			self.indexVBO[1].append(vbo.VBO(data=indici, usage=GL_DYNAMIC_DRAW,target=GL_ELEMENT_ARRAY_BUFFER))
			
			
			
            if tvert.size == 0: tvert = np.array(vertici)
            else: tvert = np.append(tvert, vertici, 0)
            indici = np.array(i.facedata['index'])+leng
            if tind.size == 0: tind = np.array(indici)
            else: tind = np.append(tind, indici, 0)
            leng = tvert.shape[0]  
        self.vertices = np.array(np.array(tvert,dtype='float32'))
        self.indices = np.array(np.array(tind,dtype='uint16'))
        self.vertexVBO = []
        self.indexVBO = []
        self.activeVBO = 0  #implementing doublevbo
        self.VBOneedupdate = [0,0]
        self.vertexVBO.append(vbo.VBO(data=self.vertices, usage=GL_DYNAMIC_DRAW, target=GL_ARRAY_BUFFER))
        self.indexVBO.append(vbo.VBO(data=self.indices, usage=GL_DYNAMIC_DRAW,target=GL_ELEMENT_ARRAY_BUFFER))
        self.vertexVBO.append(vbo.VBO(data=self.vertices, usage=GL_DYNAMIC_DRAW, target=GL_ARRAY_BUFFER))
        self.indexVBO.append(vbo.VBO(data=self.indices, usage=GL_DYNAMIC_DRAW,target=GL_ELEMENT_ARRAY_BUFFER))
        # assign other object properties
        self.scale = size
        self.position = [x,y,z]
        self.orientation = qts.Quat([0.0,30.0,0.0])
        # assign the shader and get attribute indexes (pointers)
        self.program = shadprog
        self.attrib_position = glGetAttribLocation(self.program,'position')
        #self.attrib_color = glGetAttribLocation(self.program,'color')
        # inscribe the object in the static list of the parent object
        RendCubeVBO.ListRends.append(self)
        # funny test code
        rand_axis = np.array([random.random(),random.random(),random.random()])
        norma = np.linalg.norm(rand_axis)
        rand_axis /= norma
        #self.axis = np.array([0.0,1.0,0.0])
        self.axis = rand_axis
        self.rand_angle = 0.0002 * (random.uniform(0.0,20.0)-10)
        ##test signals for the hud
        self.triangle_count = ReadableSignal('Triangles', leng)
        hud.registersignal(self.triangle_count)
        self.camworld = ReadableSignal('cam world', 0)
        hud.registersignal(self.camworld)
        self.camobj = ReadableSignal('cam obj', 0)
        hud.registersignal(self.camobj)
        self.drawtime = ReadableSignal('draw ms', 0)
        hud.registersignal(self.drawtime)
        self.tesseltime = ReadableSignal('tessel ms', 0)
        hud.registersignal(self.tesseltime)
        
        
        
    def draw(self):
        t1 = time.time()*1000
        if self.program:
            glUseProgram(self.program)

        #bind VBOs

        self.vertexVBO[self.activeVBO].bind() 
        self.indexVBO[self.activeVBO].bind()
        # set a test rendering mode
        self.VBOupdate()
        #apply local transforms
        glPushMatrix()
        #right mult bt the T 
        glTranslatef (*self.position)
        selfrot = np.ascontiguousarray(np.transpose(np.append(np.append(self.orientation._get_transform(),[[0],[0],[0]],1),[[0,0,0,1]],0)))
        #right multyply by R
        glMultMatrixd(selfrot)
        #right mult by S
        glScale(self.scale,self.scale,self.scale)
        #enable attributes arrays, and draw
        glEnableVertexAttribArray(self.attrib_position)
        glVertexAttribPointer(self.attrib_position,3,GL_FLOAT,GL_FALSE,0,self.vertexVBO[self.activeVBO])  # FG-7-4 il secondo parametro deve essere 2 perche i vertici li ho definiti come v3 qui...lo shader dovrebbe adattarsi, al peggio aggiungere : vec4(position, 1.0) per fare il casting
        nb_elements = self.indexVBO[self.activeVBO].shape[1]*(self.indexVBO[self.activeVBO].shape[0])
        glDrawElements(GL_TRIANGLES,nb_elements,GL_UNSIGNED_SHORT,self.indexVBO[self.activeVBO])
        # disable/unbind the arrays
        glDisableVertexAttribArray(self.attrib_position)
        self.vertexVBO[self.activeVBO].unbind()
        self.indexVBO[self.activeVBO].unbind()
        glPopMatrix()

        #swap active VBO
        self.activeVBO = 1-self.activeVBO
        #debug code
        t2 = time.time()*1000-t1
        if t2 > self.drawtime.getvalue(): self.drawtime.setvalue(t2)

        
    def update(self):
        #funny test: rotate o fa fraction around the rand_axis
        ca = np.cos(self.rand_angle/2)
        sa = np.sin(self.rand_angle/2)
        v = np.append(self.axis*sa,ca)
        qr = qts.Quat(v)
        self.orientation = qr.__mul__(self.orientation)   
        #check if we tessellate
        if self.Timer <> 0:
            t1 = time.time()*1000
            if (self.ActiveCamera <> 0) and (self.Timer.count==self.Timer.counter):
                #project the camera position in objectspace 
                glPushMatrix()
                glLoadIdentity()
                
                glScale(1/self.scale,1/self.scale,1/self.scale)
                
                selfrot = np.ascontiguousarray(np.append(np.append(self.orientation._get_transform(),[[0],[0],[0]],1),[[0,0,0,1]],0))
                glMultMatrixd(selfrot)
                glTranslatef (-self.position[0],-self.position[1],-self.position[2])
                #now take this matrix and compute the product camerapos * matrix to get the camera in object space
                modelViewMatrix = np.transpose(np.matrix(glGetDoublev(GL_MODELVIEW_MATRIX)))
                campostr=np.ravel(np.dot(modelViewMatrix,np.append(self.ActiveCamera.position,1)))[0:3]
                distance_campostr = np.linalg.norm(campostr)
                campostr /= distance_campostr
                campostr=sphere2cube(campostr)*distance_campostr
                self.camobj.setvalue(campostr)
                self.camworld.setvalue(self.ActiveCamera.position)
                glPopMatrix()
                tessellated = 0
                for oneface in self.face:
                    if oneface.tessellate_by_distance(campostr,0.5*self.scale,0.8*self.scale)>0:
                        oneface.do_triangles()
                        tessellated +=1
                if tessellated>0:
                    tvert = np.array([[]])
                    tind= np.array([[]])
                    leng = 0
                    for i in self.face:
                        vertici = np.array(i.facedata['vertex'])
                        if tvert.size == 0: tvert = np.array(vertici)
                        else: tvert = np.append(tvert, vertici, 0)
                        indici = np.array(i.facedata['index'])+leng
                        if tind.size == 0: tind = np.array(indici)
                        else: tind = np.append(tind, indici, 0)
                        leng = tvert.shape[0]  
                    self.triangle_count.setvalue(leng)
                    self.vertices = np.array(np.array(tvert,dtype='float32'))
                    self.indices = np.array(np.array(tind,dtype='uint16'))
                    self.VBOneedupdate = [1,1]
            #debug code
            t2 = time.time()*1000-t1
            if t2 > self.tesseltime.getvalue(): self.tesseltime.setvalue(t2)


    
    def VBOupdate(self):
        if self.VBOneedupdate[1-self.activeVBO] == 1:
                    self.indexVBO[1-self.activeVBO].set_array(self.indices)
                    self.vertexVBO[1-self.activeVBO].set_array(self.vertices) 
                    self.VBOneedupdate[1-self.activeVBO] =0 
                    