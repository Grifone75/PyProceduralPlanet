
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GL.framebufferobjects import *
from MaterialManager import MaterialManager
from FBO_RTT import FBO_RTT
import numpy as np
import time as time
from OpenGL.arrays import vbo
import PIL as pl
from SurfaceNode import SurfaceNode


class TexEvaluator:
    #helper class used to get a sample of the texture surface at a given u-v coordinates and index
    
    def __init__(self,output_size,in_tex_array_id):
        self.texsize = output_size
        self.tex_array_id = in_tex_array_id
        self.fbo = FBO_RTT(output_size,output_size)
        self.data = np.zeros([output_size,output_size],dtype='float32')
        self.shader = MaterialManager.Materials['surfacemeasure']
        self.posattr = glGetAttribLocation(self.shader,'positions')
        self.texattr = glGetAttribLocation(self.shader,'texcoords')
        self.vertexbuffer = np.array([-1.0,-1.0,0.0,0.0,1.0,
                                      -1.0,1.0,0.0,1.0,1.0,
                                      1.0,1.0,1.0,1.0,1.0,
                                      1.0,-1.0,1.0,0.0,1.0],dtype='float32')
        self.vbo = vbo.VBO(data=self.vertexbuffer,usage=GL_DYNAMIC_DRAW,target=GL_ARRAY_BUFFER)
        self.ibo = vbo.VBO(data=np.array([0,2,3,0,1,2],dtype='uint32'),usage=GL_DYNAMIC_DRAW,target=GL_ELEMENT_ARRAY_BUFFER)
        self.out_data = np.zeros([output_size,output_size], dtype = 'float32')
        
        
    def GetTexValue(self,u0,u1,v0,v1,idx):
        self.fbo.pre_FBO_rendering()
        glUseProgram(self.shader)
        
        #set up rendering 
        #no need to set up matrixes, the shader will directly map to clip space
        glEnable(GL_TEXTURE_2D)
        glDisable(GL_CULL_FACE)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.tex_array_id)
        
        glViewport(0,0,self.texsize,self.texsize)
        glClearColor(0.0,1.0,0.0,1.0)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
        glBlendFunc (GL_ONE, GL_ZERO) 
        #update texture coordinates for the part of the map to render and 
        self.vertexbuffer[2:5] = [u0,v0,idx]
        self.vertexbuffer[7:10] = [u0,v1,idx]
        self.vertexbuffer[12:15] = [u1,v1,idx]
        self.vertexbuffer[17:20] = [u1,v0,idx]
        #update the vbo accordingly
        self.vbo.set_array(self.vertexbuffer)
        #drawing code
        self.vbo.bind()
        self.ibo.bind()
        
        glEnableVertexAttribArray(self.posattr)
        glEnableVertexAttribArray(self.texattr)
        
        glVertexAttribPointer(self.posattr,2,GL_FLOAT,GL_FALSE,4*(2+3),self.vbo)
        glVertexAttribPointer(self.texattr,3,GL_FLOAT,GL_FALSE,4*(2+3),self.vbo+8)
        glDrawElements(GL_TRIANGLES,6,GL_UNSIGNED_INT,self.ibo)

        glDisableVertexAttribArray(self.posattr)
        glDisableVertexAttribArray(self.texattr)

        self.vbo.unbind()
        self.ibo.unbind()
        glClampColor(GL_CLAMP_READ_COLOR, GL_FALSE)
        glClampColor(GL_CLAMP_VERTEX_COLOR, GL_FALSE)
        glClampColor(GL_CLAMP_FRAGMENT_COLOR, GL_FALSE)
        data = glReadPixels(0,0,self.texsize, self.texsize, GL_ALPHA,GL_FLOAT)
        
        glBindTexture(GL_TEXTURE_2D_ARRAY, 0)
        glUseProgram(0)
        
        
        
        self.fbo.post_FBO_rendering()
        return data



class TextureAtlasArray:

    def __init__(self,layerscount,elementw,elementh, mipmaps = False, type = GL_RGBA, format = GL_RGBA32F, internal = GL_FLOAT):
        #reserve a opengl texture array of elementw x elementh x layerscount pixels, of specified format
        #create internal pointers and data
        self.map = []
        self.members = {}
        self.layers = layerscount
        self.elementw = elementw
        self.elementh = elementh
        for i in range(0,layerscount):
            self.map.append(0)
        self.free_count = len(self.map)
        self.type = type
        self.format = format
        self.internal = internal
        self.mipmaps = mipmaps
        #create the texture in opengl
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_ARRAY,texture)
        #glTexStorage3D(GL_TEXTURE_2D_ARRAY, 1, GL_RGBA, elementw,elementh,layerscount) # test
        glTexImage3D(GL_TEXTURE_2D_ARRAY,0,format,elementw,elementh,layerscount,0,type,internal,None)
        glTexParameterf(GL_TEXTURE_2D_ARRAY,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D_ARRAY,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        if mipmaps:
            glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_BASE_LEVEL, 0)
            glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAX_LEVEL, 1000)
            glGenerateMipmap(GL_TEXTURE_2D_ARRAY)
        glBindTexture(GL_TEXTURE_2D, 0)
        self.tex_atlas_id = texture
        self.Evaluator = TexEvaluator(25,self.tex_atlas_id)
    
    def count_free_slots(self):
        #returns the number of free elements in the atlas
        return self.free_count
    
    def reserve_slot(self,caller):
        #find the first next free slot
        index = [idx for idx in range(len(self.map)) if self.map[idx]==0][0]
        #update internal data and exit returning the address
        self.map[index] = 3 #reserved slot
        #check if caller has a texture already and change it
        self.members[caller] = index
        self.free_count -=1
        return index
        
    def fill_reserved_slot(self,tid,index):
        #check that the slot is reserved:
        if self.map[index] == 3:
            t = time.time()*1000
            glBindTexture(GL_TEXTURE_2D,tid)
            OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING = False
            data = glGetTexImage(GL_TEXTURE_2D,0,self.type,self.internal, outputType = 'str' )
            glBindTexture(GL_TEXTURE_2D, 0)
            glBindTexture(GL_TEXTURE_2D_ARRAY,self.tex_atlas_id)
            glTexSubImage3D(GL_TEXTURE_2D_ARRAY,0,0,0,index,self.elementw,self.elementh,1,self.type,self.internal,data)
            glBindTexture(GL_TEXTURE_2D,0)
            #update internal data and exit returning the address
            self.map[index] = 1 #dynamic texture
            #print 'free tex: '+str(self.free_count)
            print 'time filling: '+ str(time.time()*1000-t)
            return index
        else: return -1
            
    
    
    def fill_slot(self,tid,caller,permanent=False, texdata = None):
        #copy the texture pointed by data in the first next free slot
        index = [idx for idx in range(len(self.map)) if self.map[idx]==0][0]
        #code for the texture
        #check if we pass data or a gl texture id
        if texdata == None:
            glBindTexture(GL_TEXTURE_2D,tid)
            OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING = False
            data = glGetTexImage(GL_TEXTURE_2D,0,self.type,self.internal, outputType = 'str' )
            glBindTexture(GL_TEXTURE_2D, 0)
        else: 
            data = texdata
            
        glBindTexture(GL_TEXTURE_2D_ARRAY,self.tex_atlas_id)
        glTexSubImage3D(GL_TEXTURE_2D_ARRAY,0,0,0,index,self.elementw,self.elementh,1,self.type,self.internal,data)
        if self.mipmaps:
            glGenerateMipmap(GL_TEXTURE_2D_ARRAY)
        glBindTexture(GL_TEXTURE_2D,0)
        #update internal data and exit returning the adress
        if permanent: self.map[index] = 2 #permanent texture
        else: self.map[index] = 1 #dynamic texture
        self.members[caller] = index
        self.free_count -=1
        return index
    
    def remove_tex_user(self,index,caller):
        try:
            self.members.pop(caller)
        except:
            pass
        if not index in self.members.values():
            self.empty_slot(index) 

        
    def add_tex_user(self,index,caller):
        self.members[caller] = index
     
    def empty_slot(self,index):
        #modify internal data structure to free the pointed slot (do not erase data)
        if (self.map[index]==1 or self.map[index]==3) :
            self.map[index]=0
            self.free_count +=1
            return 0
        else: return -1
        
        
    def get_tex_id(self):
        return self.tex_atlas_id   
    
    def save_texture_atlas_bmp(self,stri):
        #to be rewritten
        glBindTexture(GL_TEXTURE_2D_ARRAY,self.tex_atlas_id)      
        OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING = True
        data = np.ndarray(shape=(self.elementw,self.elementh,self.layers), dtype='uint32')
        glGetTexImage(GL_TEXTURE_2D_ARRAY,0,GL_RGBA,GL_UNSIGNED_BYTE,data, outputType = 'str' )
        glBindTexture(GL_TEXTURE_2D, 0)
        from PIL import Image
        image = Image.frombytes('RGBA', (self.layers*self.elementw,self.elementh), data, 'raw')
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.save ('Media/Textures/TexAtlas'+stri+'.png')
        
    def load_texture_image(self,filename):
        #load a image file and fill one slot, returning the id to the caller
        if self.free_count > 0:
            img = pl.Image.open(filename)
            img_data = np.array(list(img.getdata()),np.short)
            slot =  self.fill_slot(0, 'self-load', True,img_data)
            return slot
        else: return -1
        
    def free_unused_slots(self,nr_cleanups = 0):
        list_to_free=[]
        t0 = time.time()
        for key in self.members: 
            if isinstance(key,SurfaceNode):
                if key.HaveAllChildrenTextures(): 
                    print '****** all children have textures to delete *****'
                    list_to_free.append(key)
        print 'time to check slots to free: '+str((time.time()-t0)*1000)
        for el in list_to_free:
                print 'freeing 1 texture slot'
                el.Free_texture()
                
    def free_below_level(self,level):
        #check if the texture array is near saturation
        if (float(self.free_count)/float(self.layers)) < level : return True
        else: return False
        
        
    def free_over_level(self,level):
        #check if the texture array is near saturation
        if (float(self.free_count)/float(self.layers)) > level : return True
        else: return False
        