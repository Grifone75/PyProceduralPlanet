'''
Created on 26 August 2015

@author: Fabrizio
'''
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
# PyOpenGL 3.0.1 introduces this convenience module...
from OpenGL.GL.shaders import *
import numpy as np
from OpenGL.arrays import vbo  
from OpenGL.raw.GL.VERSION.GL_1_5 import GL_STATIC_DRAW, GL_ELEMENT_ARRAY_BUFFER
from MaterialManager import MaterialManager
from OpenGL.raw.GL.VERSION.GL_2_0 import glUseProgram

def switch(axis,v3):
    [d1,d2,d3] = v3
    if axis == 0:
        return [d1,d2,d3]
    elif axis == 1:
        return [d2,d3,d1]
    else: return [d3,d1,d2]


class RenderableSkydome:
    '''
    classdocs
    '''


    def __init__(self, gridsize):
        '''
        Constructor
        '''
        self.vertex = []
        self.index = []
        self.triangles = 0
        baseindex = 0
        hgrid = gridsize/2
        hgridf = gridsize/2.0
        for axis in range(0,3):
            for d1 in range (-1,2,2):
                for d2 in range (-hgrid,hgrid):
                    for d3 in range (-hgrid,hgrid): 
                        v1 = switch(axis,[d1/1.0,d2/hgridf,d3/hgridf])
                        v2 = switch(axis,[d1/1.0,(d2+1)/hgridf,d3/hgridf])
                        v3 = switch(axis,[d1/1.0,d2/hgridf,(d3+1)/hgridf])
                        v4 = switch(axis,[d1/1.0,(d2+1)/hgridf,(d3+1)/hgridf])
                        self.vertex.append([v1,v2,v3,v4])
                        if d1 > 0:
                            self.index.append([baseindex,baseindex+1,baseindex+2])
                            self.index.append([baseindex+1,baseindex+3,baseindex+2])
                        else:
                            self.index.append([baseindex,baseindex+2,baseindex+1])
                            self.index.append([baseindex+1,baseindex+2,baseindex+3])
                        self.triangles += 2
                        baseindex += 4
                        
        self.vbo = vbo.VBO(data=np.array(self.vertex,dtype='float32'), usage=GL_STATIC_DRAW, target=GL_ARRAY_BUFFER)
        self.ibo = vbo.VBO(data=np.array(self.index, dtype='uint32'), usage= GL_STATIC_DRAW, target=GL_ELEMENT_ARRAY_BUFFER)       
                
        #material loading
        self.program = MaterialManager.Materials['skybox_inside']
        
    def attach_light(self,light): #to be removed once light are managed with a scene manager
        self.light = light
        
    def draw_inner_sky(self,proj,view,model):
        
        glUseProgram(self.program)
        glEnableVertexAttribArray(glGetAttribLocation(self.program,'position'))
        glUniformMatrix4fv(glGetUniformLocation(self.program,'u_model'),1,GL_TRUE,model)
        glUniformMatrix4fv(glGetUniformLocation(self.program,'u_view'),1,GL_FALSE,view) 
        glUniformMatrix4fv(glGetUniformLocation(self.program,'u_proj'),1,GL_FALSE,proj) 
        glUniformMatrix4fv(glGetUniformLocation(self.program,'u_normal'),1,GL_FALSE,np.transpose(np.linalg.inv(np.dot(np.transpose(model),view))))
        glUniform3fv(glGetUniformLocation(self.program,'u_lposition3'),1,self.light.get_pos())
        glUniform3fv(glGetUniformLocation(self.program,'u_lintensity3'),1,self.light.get_intensity())
        glUniform1f(glGetUniformLocation(self.program,'sky_norm_radius'),1.1)
    
    
        self.vbo.bind()
        self.ibo.bind()
        glVertexAttribPointer(glGetAttribLocation(self.program,'position'),3,GL_FLOAT,GL_FALSE,12,self.vbo)
        glDrawElements(GL_TRIANGLES,self.triangles*3,GL_UNSIGNED_INT,self.ibo)
        self.vbo.unbind()
        self.ibo.unbind()
         
        
        glDisableVertexAttribArray(glGetAttribLocation(self.program,'position'))
        
        
        
        pass
    
    def update(self):
        pass

