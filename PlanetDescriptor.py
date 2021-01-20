

from scipy.interpolate import griddata
import numpy as np
import OpenGL 
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from TextureAtlasArray import *


def testgenSeaTexture(size):
    #define size
    
    #new test with texture2d array
     
    id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D_ARRAY,id)
    #glTexStorage3D(GL_TEXTURE_2D_ARRAY, 1, GL_RGBA, elementw,elementh,layerscount) # test
    glTexImage3D(GL_TEXTURE_2D_ARRAY,0,GL_RGBA32F,size,size,3,0,GL_RGBA,GL_FLOAT,None)
    glTexParameterf(GL_TEXTURE_2D_ARRAY,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D_ARRAY,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_LINEAR) 
    
#     cw = np.array([[4,0],
#                    [0,4],
#                    [1,1]])
#     
#     for k in range(0,3):
#         text = np.zeros([size,size,4])
#         for i in range(0,size):
#             for j in range(0,size):
#                 text[i,j,2] = (np.sin(float(i)*cw[k,0]/float(size-1)*6.2831+float(j)*cw[k,1]/float(size-1)*6.2831)**5+1)/2.0
#                 text[i,j,0] = cw[k,0]*3.14/float(size-1)*5*(np.sin(float(i)*cw[k,0]/float(size-1)*6.2831+float(j)*cw[k,1]/float(size-1)*6.2831)**4)*np.cos(float(i)*cw[k,0]/float(size-1)*6.2831+float(j)*cw[k,1]/float(size-1)*6.2831)
#                 text[i,j,1] = cw[k,1]*3.14/float(size-1)*5*(np.sin(float(i)*cw[k,0]/float(size-1)*6.2831+float(j)*cw[k,1]/float(size-1)*6.2831)**4)*np.cos(float(i)*cw[k,0]/float(size-1)*6.2831+float(j)*cw[k,1]/float(size-1)*6.2831)
#         glTexSubImage3D(GL_TEXTURE_2D_ARRAY,0,0,0,k,size,size,1,GL_RGBA,GL_FLOAT,np.ravel(text))
#     glBindTexture(GL_TEXTURE_2D, 0) 
    
    
    d_samples = size
    t_samples = size
    for k in range(0,3):
        text = np.zeros([size,size,4])
        for d in range(0,d_samples):
            for t in range(0,size):
                text[d,t,2] = (np.sin(float(d)/float(d_samples-1)*6.2831+float(t)/float(t_samples-1)*6.2831)**5+1)/2.0
                text[d,t,0] = 3.14/float(size-1)*5*(np.sin(float(d)/float(d_samples-1)*6.2831+float(t)/float(t_samples-1)*6.2831)**4)*np.cos(float(d)/float(d_samples-1)*6.2831+float(t)/float(t_samples-1)*6.2831)
                text[d,t,1] = 0.0
        glTexSubImage3D(GL_TEXTURE_2D_ARRAY,0,0,0,k,d_samples,t_samples,1,GL_RGBA,GL_FLOAT,np.ravel(text))
    glBindTexture(GL_TEXTURE_2D, 0) 
    
#     text = np.zeros([size,size,4])
#     #loop thru array and generate the texture
#     cw = np.array([[0.5,5,3],
#                   [0.3,9,-7],
#                   [0.2,-12,10],
#                   [0.1,-19,16]])
#     
#     
#     for i in range(0,size):
#         for j in range(0,size):
#             text[i,j,0] = 0.0
#             text[i,j,1] = 0.0
#             text[i,j,2] = 0.0
#             for k in range(0,np.size(cw,1)):
#                 text[i,j,2] += cw[k,0]*(np.sin(float(i)*cw[k,1]/float(size-1)*6.2831+float(j)*cw[k,2]/float(size-1)*6.2831)**5+1)/2.0
#                 text[i,j,0] += cw[k,0]*cw[k,1]*3.14/float(size-1)*5*(np.sin(float(i)*cw[k,1]/float(size-1)*6.2831+float(j)*cw[k,2]/float(size-1)*6.2831)**4)*np.cos(float(i)*cw[k,1]/float(size-1)*6.2831+float(j)*cw[k,2]/float(size-1)*6.2831)
#                 text[i,j,1] += cw[k,0]*cw[k,2]*3.14/float(size-1)*5*(np.sin(float(i)*cw[k,1]/float(size-1)*6.2831+float(j)*cw[k,2]/float(size-1)*6.2831)**4)*np.cos(float(i)*cw[k,1]/float(size-1)*6.2831+float(j)*cw[k,2]/float(size-1)*6.2831)
#         
#     
                
    #save as gl texture, to be returned
#     id = glGenTextures(1)
#     glPixelStorei(GL_UNPACK_ALIGNMENT,1)
#     glBindTexture(GL_TEXTURE_2D,id)
#     glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
#     glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
#     glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER, GL_LINEAR)
#     glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER, GL_LINEAR)
#     glTexImage2D(GL_TEXTURE_2D,0, GL_RGB, size,size,0,GL_RGBA,GL_FLOAT,np.ravel(text))
#     glBindTexture(GL_TEXTURE_2D,0)
    return id

class PlanetDescriptor:
    

    
    def __init__(self,name,r,h,sealevel,hm,nm,mm):
        self.name = name
        self.radius = r
        self.height = h
        self.sea_level = sealevel
        self.height_material = hm
        self.normal_material = nm
        self.main_material = mm
        self.mixmap = self.GenerateTexture()
        self.wavetext = testgenSeaTexture(256)
        self.surface_textures = TextureAtlasArray(8,2048,2048,True,GL_RGB,GL_RGB,GL_UNSIGNED_BYTE)
        self.surface_textures.load_texture_image('Media/Textures/1.jpg')
        self.surface_textures.load_texture_image('Media/Textures/SeamlessMixedStone0003.jpg')
        
        
    def GenerateTexture(self):
        
        x,y = np.mgrid[0:1:0.1,0:1:0.1]
        #p = np.random.rand(1,2)
        p = np.array([[0,0],[0,0.9],[0.9,0],[0.9,0.9]])
        val = [np.array([1,1,1,1.0]), # flat high
               np.array([0.3,0.2,0.2,1.0]), # steep high
               np.array([0.1,0.3,0.0,1.0]), # flat low
               np.array([0.3,0.3,0.1,1.0])] # steep low
        
        #add arid high desert
        #p = np.append(p, [[0.2,0]], 0)
        #val.append(np.array([0.5,0.5,0.4,1.0]))
        
        #add beach
#         p = np.append(p, [[0.0,0.5]], 0)
#         val.append(np.array([0.9,0.9,0.5,1.0]))
#         p = np.append(p, [[0.9,0.5]], 0)
#         val.append(np.array([0.2,0.4,0.0,1.0]))
#         
#         p = np.append(p, [[0.3,0.0]], 0)
#         val.append(np.array([0.1,0.2,0.0,1.0]))
#         
#         p = np.append(p, [[0.3,0.9]], 0)
#         val.append(np.array([0.3,0.2,0.1,1.0]))
#         
        z = griddata(p,val,(x,y), method = 'cubic')
        zflat = np.ravel(z)
        
        id = glGenTextures(1)
        glPixelStorei(GL_UNPACK_ALIGNMENT,1)
        glBindTexture(GL_TEXTURE_2D,id)
        glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D,0, GL_RGB, 10,10,0,GL_RGBA,GL_FLOAT,zflat)
        glBindTexture(GL_TEXTURE_2D,0)
        
        return id
    