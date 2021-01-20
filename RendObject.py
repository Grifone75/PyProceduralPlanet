  
import OpenGL 

import numpy as np
import quaternions as qts
from quaternions import Quat
from OpenGL.arrays import vbo  
import random
import time

OpenGL.ERROR_ON_COPY = True 
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# PyOpenGL 3.0.1 introduces this convenience module...
from OpenGL.GL.shaders import *

import time, sys
  
       
# lets define a basic structure for a renderable object
class RendObject:
    ListRends = []
    ActiveCamera = 0
    
    def __init__(self,type, size, x, y, z, shadprog):
        #code to define the object type, in the following we will generate here the vertex buffer data
        if type == 'Cube':
            self.type = 'Cube'
            self.size = size
        elif type == 'Sphere':
            self.type = 'Sphere'
            self.size = size
        elif type == 'Custom':
            self.type = 'Custom'
            #declare custom data - for the vbo test  
            vertices = np.array([[0,10,0],[-10,-10,0],[10,-10,0]],dtype='float32')
            indices = np.array([[0,1,2]],dtype='uint16')
            self.vertexVBO = vbo.VBO(data=vertices, usage=GL_DYNAMIC_DRAW, target=GL_ARRAY_BUFFER)
            self.indexVBO = vbo.VBO(data=indices, usage=GL_DYNAMIC_DRAW,target=GL_ELEMENT_ARRAY_BUFFER)
            self.vertexVBO.bind() #wrapper of glBindBuffer ... tocheck
            self.indexVBO.bind()
     
            
            #tocontinue.....  
        else :
            self.type = 'Cube'
            self.size = 1
        self.position = [x,y,z]
        self.orientation = qts.Quat([0.0,30.0,0.0])
        self.program = shadprog
        RendObject.ListRends.append(self)
        #funny test code
        rand_axis = np.array([random.random(),random.random(),random.random()])
        norma = np.linalg.norm(rand_axis)
        rand_axis /= norma
        self.axis = np.array([0.0,1.0,0.0])
        self.rand_angle = 0.02 * (random.uniform(0.0,20.0)-10)
        
        
    def draw(self):
        if self.program:
            glUseProgram(self.program)
        # code to draw the object in OpenGL
        glPushMatrix()
        glTranslatef (*self.position)
        selfrot = np.ascontiguousarray(np.transpose(np.append(np.append(self.orientation._get_transform(),[[0],[0],[0]],1),[[0,0,0,1]],0)))
        glMultMatrixd(selfrot)
        #for the time being we don't consider rotations
        if self.type == 'Cube':
            glutSolidCube(self.size)
        elif self.type == 'Sphere':
            glutSolidSphere(self.size,12,12)
        glPopMatrix()
        #glUseProgram(0)
        
    def update(self):
        #funny test: rotate o fa fraction around the rand_axis
        ca = np.cos(self.rand_angle/2)
        sa = np.sin(self.rand_angle/2)
        v = np.append(self.axis*sa,ca)
        qr = qts.Quat(v)
        self.orientation = qr.__mul__(self.orientation)
        