
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GL.framebufferobjects import *

class TextureAtlas:

    def __init__(self,gridw,gridh,elementw,elementh, format):
        #reserve a opengl texture of gridw*elementw x gridh*elementh pixels, of specified format
        #create internal pointers and data
        self.map = {}
        self.gridw = gridw
        self.gridh = gridh
        self.elementw = elementw
        self.elementh = elementh
        for col in range(0,gridw):
            for row in range (0,gridh):
                self.map[(col,row)]=0
        self.free_count = len(self.map)
        #create the texture in opengl
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D,texture)
        glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_BASE_LEVEL, 0)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, 0)
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,gridw*elementw,gridh*elementh,0,GL_RGBA,GL_FLOAT,None)
        glBindTexture(GL_TEXTURE_2D, 0)
        self.tex_atlas_id = texture
    
    def count_free_slots(self):
        #returns the number of free elements in the atlas
        return self.free_count
    
    def fill_slot(self,tid):
        #copy the texture pointed by data in the first next free slot
        (offw,offh) = [address for address,value in self.map.items() if value == 0][0]
        #code for the texture

        
        glBindTexture(GL_TEXTURE_2D,tid)
        OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING = False
        data = glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_FLOAT, outputType = 'str' )
        glBindTexture(GL_TEXTURE_2D, 0)

        glBindTexture(GL_TEXTURE_2D,self.tex_atlas_id)
        glTexSubImage2D(GL_TEXTURE_2D,0,offw*self.elementw,offh*self.elementh,self.elementw,self.elementh,GL_RGBA,GL_FLOAT,data)
        glBindTexture(GL_TEXTURE_2D,0)
        
        #update internal data and exit returning the adress
        self.map[offw,offh] = 1
        self.free_count -=1
        return (offw,offh)
     
    def empty_slot(self,offh,offv):
        #modify internal data structure to free the pointed slot (do not erase data)
        self.map[offh,offv]=0
        self.free_count +=1
        
    def get_texture_coords(self,idx,idy):
        return (float(idx)/float(self.gridw), float(idy)/float(self.gridh), 1.0/float(self.gridw), 1.0/float(self.gridh))
        
    def get_tex_id(self):
        return self.tex_atlas_id   
    
    def save_texture_atlas_bmp(self,stri):
        glBindTexture(GL_TEXTURE_2D,self.tex_atlas_id)      
        OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING = True
        data = glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE, outputType = 'str' )
        glBindTexture(GL_TEXTURE_2D, 0)
        from PIL import Image
        image = Image.frombytes('RGBA', (self.gridw*self.elementw,self.gridh*self.elementh), data, 'raw')
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.save ('Media/Textures/TexAtlas'+stri+'.png')
        