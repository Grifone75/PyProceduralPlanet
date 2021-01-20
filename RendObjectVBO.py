  
import OpenGL 

import numpy as np
import quaternions as qts
from quaternions import Quat
from OpenGL.arrays import vbo  
import RendObject
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
class RendObjectVBO(RendObject.RendObject):
    #ListRends = []
    
    def __init__(self,type, size, x, y, z, shadprog):


        #declare custom data - for the vbo test  
        vertices = np.array([[0.0,0.0,0.0],[0.0,15.0,0.0],[15.0,0.0,0.0],[0.0,0.0,-15]],'float32')
        indices = np.array([[0,1,2],[2,1,3],[0,3,1],[0,2,3]],dtype='uint16')
        self.vertexVBO = vbo.VBO(data=vertices, usage=GL_DYNAMIC_DRAW, target=GL_ARRAY_BUFFER)
        self.indexVBO = vbo.VBO(data=indices, usage=GL_DYNAMIC_DRAW,target=GL_ELEMENT_ARRAY_BUFFER)

        self.position = [x,y,z]
        self.orientation = qts.Quat([0.0,30.0,0.0])
        
        # here we set up the program. here we get the attributes indices
        self.program = shadprog
        self.attrib_position = glGetAttribLocation(self.program,'position')
        #self.attrib_color = glGetAttribLocation(self.program,'color')
        
        RendObjectVBO.ListRends.append(self)
        #funny test code
        rand_axis = np.array([random.random(),random.random(),random.random()])
        norma = np.linalg.norm(rand_axis)
        rand_axis /= norma
        #self.axis = np.array([0.0,1.0,0.0])
        self.axis = rand_axis
        self.rand_angle = 0.02 * (random.uniform(0.0,20.0)-10)
        
        
    def draw(self):
        if self.program:
            glUseProgram(self.program)
        # code to draw the object in OpenGL
        #bind VBOs
        self.vertexVBO.bind() 
        self.indexVBO.bind()
        #apply local transforms
        glPushMatrix()
        glTranslatef (*self.position)
        selfrot = np.ascontiguousarray(np.transpose(np.append(np.append(self.orientation._get_transform(),[[0],[0],[0]],1),[[0,0,0,1]],0)))
        glMultMatrixd(selfrot)
        #for the time being we don't consider rotations
        glEnableVertexAttribArray(self.attrib_position)
        #glBindBuffer(GL_ARRAY_BUFFER,self.vertexVBO)
        glVertexAttribPointer(self.attrib_position,3,GL_FLOAT,GL_FALSE,0,self.vertexVBO)  # FG-7-4 il secondo parametro deve essere 2 perche i vertici li ho definiti come v3 qui...lo shader dovrebbe adattarsi, al peggio aggiungere : vec4(position, 1.0) per fare il casting
        glDrawElements(GL_LINE_LOOP,12,GL_UNSIGNED_SHORT,self.indexVBO)
        # disable this rendering
        glDisableVertexAttribArray(self.attrib_position)
        self.vertexVBO.unbind()
        self.indexVBO.unbind()
        glPopMatrix()
        
    def update(self):
        #funny test: rotate o fa fraction around the rand_axis
        ca = np.cos(self.rand_angle/2)
        sa = np.sin(self.rand_angle/2)
        v = np.append(self.axis*sa,ca)
        qr = qts.Quat(v)
        self.orientation = qr.__mul__(self.orientation)
        