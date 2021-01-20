


import OpenGL 

import numpy as np
from OpenGL.arrays import vbo
import random
import time
import PIL as pl
from PIL import Image
from __builtin__ import str

OpenGL.ERROR_ON_COPY = True 
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GL.framebufferobjects import *
from Utils import *
from MaterialManager import MaterialManager

# PyOpenGL 3.0.1 introduces this convenience module...
from OpenGL.GL.shaders import *

import time, sys

class SceneManager:
    SceneList = []
    
    
    def __init__(self,fbo_tex_size,activecamera):
        self.scenes = 0 #useless, to be replaced
        self.timer = UtilTimer(60)
        self.activecamera = activecamera
        
        self.matcube = {}
        #declare cube rotation matrixes for the height shader 
        self.matcube['height'] = []
        self.matcube['height'].append(np.array([[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,-1.0]])) #2 - to invert
        self.matcube['height'].append(np.array([[0.0,0.0,-1.0],[0.0,1.0,0.0],[-1.0,0.0,0.0]])) #1
        self.matcube['height'].append(np.array([[-1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]])) #0 - to invert
        self.matcube['height'].append(np.array([[0.0,0.0,1.0],[0.0,1.0,0.0],[1.0,0.0,0.0]])) #3
        self.matcube['height'].append(np.array([[1.0,0.0,0.0],[0.0,0.0,-1.0],[0.0,-1.0,0.0]])) #4 Bottom
        self.matcube['height'].append(np.array([[1.0,0.0,0.0],[0.0,0.0,1.0],[0.0,1.0,0.0]])) #5 Top
        
        #declare cube rotation matrixes for the normal shader 
        self.matcube['normal'] = []
        self.matcube['normal'].append(np.array([[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]])) # front ok
        self.matcube['normal'].append(np.array([[0.0,0.0,1.0],[0.0,1.0,0.0],[-1.0,0.0,0.0]])) #1
        self.matcube['normal'].append(np.array([[-1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,-1.0]])) #0 - to invert
        self.matcube['normal'].append(np.array([[0.0,0.0,-1.0],[0.0,1.0,0.0],[1.0,0.0,0.0]])) #3
        self.matcube['normal'].append(np.array([[1.0,0.0,0.0],[0.0,0.0,1.0],[0.0,-1.0,0.0]])) #4 Bottom ok 
        self.matcube['normal'].append(np.array([[1.0,0.0,0.0],[0.0,0.0,-1.0],[0.0,1.0,0.0]])) #5 Top ok 

        self.fbo_tex_size = fbo_tex_size
        GlobalSettings.set('drawmode', GL_FRONT)
        GlobalSettings.set('linemode', GL_FILL)

    
    def set_base_scene(self):
        
        glDrawBuffer(GL_BACK)
        glClearColor(0.0, 0.0, 0.0, 0.0)    # This Will Clear The Background Color To Black
        glClearDepth(1.0)                    # Enables Clearing Of The Depth Buffer
        glEnable(GL_CULL_FACE)
        glDepthFunc(GL_LESS)                # The Type Of Depth Test To Do
        glEnable(GL_DEPTH_TEST)                # Enables Depth Testing
        glCullFace(GL_BACK)
        glPolygonMode(GlobalSettings.read('drawmode'),GlobalSettings.read('linemode'))
        
        glFrontFace(GL_CCW)
        glShadeModel(GL_SMOOTH) 
        glEnable (GL_BLEND)
        glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()                    # Reset The Projection Matrix
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if hasattr(self, 'w'):
            glViewport(0,0,self.w,self.h)
            self.activecamera.set_aspect(float(self.w)/float(self.h))
        else:
            glViewport(0,0,640,480)
            self.activecamera.set_aspect(float(640)/float(480))
        glMatrixMode(GL_MODELVIEW)
        
    def set_base_w_h(self,w,h):
        self.w = w
        self.h = h
        glViewport(0,0,w,h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, float(w)/float(h), 10.0, 10000.0)
        self.activecamera.set_aspect(float(self.w)/float(self.h))
        glMatrixMode(GL_MODELVIEW)
        
    def set_fbo_scene(self):
        
        #disable face culling since we are rendering from the inside
        glDisable(GL_CULL_FACE)
        glDisable (GL_BLEND)

        self.ds = 1.0
        ds = self.ds

        if not hasattr(self, 'fbo_created'):
            self.hfbo = glGenFramebuffers(1)
            self.nfbo = glGenFramebuffers(1)
            self.fbo_created = True
        
        if not hasattr(self, 'ibo'):
            self.p1vbo = vbo.VBO(data=np.array([-ds,-ds,-ds,-ds,ds,-ds,ds,ds,-ds,ds,-ds,-ds],dtype='float32'),usage=GL_DYNAMIC_DRAW,target=GL_ARRAY_BUFFER)
            self.p2vbo = vbo.VBO(data=np.array([-ds,-ds,-ds,0.0,0.0,-ds,ds,-ds,0.0,ds,ds,ds,-ds,ds,ds,ds,-ds,-ds,ds,0.0],dtype='float32'),usage=GL_DYNAMIC_DRAW,target=GL_ARRAY_BUFFER)
            self.ibo = vbo.VBO(data=np.array([0,2,3,0,1,2],dtype='uint32'),usage=GL_DYNAMIC_DRAW,target=GL_ELEMENT_ARRAY_BUFFER)


        
    def draw_fbo_cube(self,planetdescriptor,face,synth_pass,facex,facey,level,tex_in):
        #debug code
        self.timer.start()
        
        w = h = self.fbo_tex_size
        
        ds_exp = 0
        bord = 0         
        if synth_pass == 'pass_1': #setup for heightmap rendering
            #1 pixel border
            h += 2
            w += 2
            ds_exp = 1.0/float(w) 
            material =  MaterialManager.Materials[planetdescriptor.height_material]
        else: 
            material =  MaterialManager.Materials[planetdescriptor.normal_material]
        
        #define rendering target: the texture to create
        texture = glGenTextures(1)
        glActiveTexture(GL_TEXTURE5)
        glBindTexture(GL_TEXTURE_2D,texture)
        glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_BASE_LEVEL, 0)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, 0)
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA32F,w,h,0,GL_RGBA,GL_FLOAT,None)
        glBindTexture(GL_TEXTURE_2D, 0)
        
        #activate the rendering program
        glUseProgram(material)
        
        #standard dimensions for the scene cube
        ds = self.ds 
        dz = np.cos(np.radians(45.0))/np.sin(np.radians(45.0))*ds
        
        
 
        #specific setup depending on pass (heightmap or normal)
             
        if synth_pass == 'pass_1': #setup for heightmap rendering 
            #fov adapted to level 
            glBindTexture(GL_TEXTURE_2D, 0) 
            glDisable(GL_TEXTURE_2D)   
            fov = 90.0
            txindex = -1 #won't use texture coords
            matpass = 'height'
            posattr = glGetAttribLocation(material,'position')
            glEnableVertexAttribArray(posattr)
            glUniform1f(glGetUniformLocation(material,'hmap_border_factor'),ds_exp/(2.0**level))
            glUniform1f(glGetUniformLocation(material,'hmap_dx'),facex*ds)
            glUniform1f(glGetUniformLocation(material,'hmap_dy'),facey*ds)
            glUniform1f(glGetUniformLocation(material,'patchscale'),1.0/(2.0**level))
            glUniform1i(glGetUniformLocation(material,'level'),level)
            fbo = self.hfbo
            vbo = self.p1vbo
            ibo = self.ibo
            stride = 4*3
            
        if synth_pass == 'pass_2':
            glEnable(GL_TEXTURE_2D)
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, tex_in)
            fov = 90.0
            txindex = 1 #will use texture coords
            #glGetAttribLocation(material,'texturecoord') 
            faceindexlocation = glGetUniformLocation(material,'cubefacedebug') 
            glUniform1i(faceindexlocation,face)  
            matpass = 'normal'
            posattr = glGetAttribLocation(material,'position')
            texattr = glGetAttribLocation(material,'texcoord')
            glEnableVertexAttribArray(posattr)
            glEnableVertexAttribArray(texattr)
            glUniform1f(glGetUniformLocation(material,'planet_radius'),planetdescriptor.radius)
            glUniform1f(glGetUniformLocation(material,'planet_height'),planetdescriptor.height)   
            glUniform2f(glGetUniformLocation(material,'patchcenter'),facex,facey)
            glUniform1f(glGetUniformLocation(material,'patchscale'),1.0/(2.0**level))
            glUniform1i(glGetUniformLocation(material,'level'),level)
            fbo = self.nfbo 
            vbo = self.p2vbo
            ibo = self.ibo
            stride = 4*(2+3)
            
         
        #bind fbo and set render target
        glBindFramebuffer(GL_FRAMEBUFFER,fbo)
        glDrawBuffer(GL_COLOR_ATTACHMENT0)
        glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D, texture,0)   
        #set up virtual camera fov (position will be set up just before draw)
        glClearColor(1.0,0.0,0.0,1.0)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glShadeModel(GL_SMOOTH)
        
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(fov,float(w)/float(h),0.001,100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        #set up rotation matrix for the cube face
        matrotlocation = glGetUniformLocation(material,'rotcubev')
        glUniformMatrix3fv(matrotlocation,1,False,self.matcube[matpass][face])

        
        glViewport(0,0,w,h)
        glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
        glClearColor(0.0,1.0,0.0,1.0)

        vbo.bind()
        ibo.bind()
        glVertexAttribPointer(posattr,3,GL_FLOAT,GL_FALSE,stride,vbo)
        if txindex <>-1: glVertexAttribPointer(texattr,2,GL_FLOAT,GL_FALSE,stride,vbo+(3*4))
        glDrawElements(GL_TRIANGLES,6,GL_UNSIGNED_INT,ibo)
        vbo.unbind()
        ibo.unbind()
        


        glFinish()
        #disable FBO
        
        st = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        
        #ALternative 1 (works)
#         glReadBuffer(GL_COLOR_ATTACHMENT0)
#         data = None
#         data = glReadPixels(0,0,w, h, GL_RGBA,  GL_UNSIGNED_BYTE)
        glBindTexture(GL_TEXTURE_2D, 0)
        glBindFramebuffer(GL_FRAMEBUFFER,0)
        glUseProgram(0)

        #glDeleteFramebuffers([fbo])
        #Alternative 2 (works, and the output type is not necessary)
#         if level == 4:

        if level == 99:
            glBindTexture(GL_TEXTURE_2D,texture)
            OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING = False
            data = glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_FLOAT, outputType = 'str' )
            min= 99999
            max= -99999
            for row in data:
                for el in row:
                    if el[3]>max: max = el[3]
                    if el[3]<min: min = el[3]
            print min
            print max
            glBindTexture(GL_TEXTURE_2D,texture)
        #debug code
        #print 'fbo '+synth_pass+str(face)+' '+str(self.timer.stop()*1000)+' ms'
        #self.timer.start()
        #debug code: save textures
#         from PIL import Image
#         image = Image.frombytes('RGBA', (w,h), data, 'raw')
#         image = image.transpose(Image.FLIP_TOP_BOTTOM)
#         image.save ('Media/Textures/f'+str(face)+' x'+str(facex)+' y'+str(facey)+' l'+str(level)+' m'+str(material)+' fv'+str(fov)+' fb'+str(fbo)+' '+synth_pass+'.png')
#         #debug code
        #print 'fbo save txt '+synth_pass+str(face)+' '+str(self.timer.stop()*1000)+' ms'

        if synth_pass == 'pass_1':
            return texture
        else:
            return texture
        
        
        
        