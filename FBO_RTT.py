


from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GL.framebufferobjects import *

class FBO_RTT:
	def __init__(self,w,h):
		#this class define a FBO id and a Texture id to be used as RTT
		#define the fbo
		self.fbo = glGenFramebuffers(1)
		glBindFramebuffer(GL_FRAMEBUFFER,self.fbo)
		# 1st define rendering target
		self.size2 = (w,h)
		self.rtt = glGenTextures(1)
		glActiveTexture(GL_TEXTURE4)
		glBindTexture(GL_TEXTURE_2D,self.rtt)
		glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA32F,w,h,0,GL_RGBA,GL_FLOAT,None)
		glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE)
		glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_BASE_LEVEL, 0)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, 0)
		glBindTexture(GL_TEXTURE_2D,0)
		
		glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,self.rtt,0)
		glBindTexture(GL_TEXTURE_2D, 0)
		
		self.rbd = glGenRenderbuffers(1)
		glBindRenderbuffer(GL_RENDERBUFFER, self.rbd)
		glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT16,w,h)

		glFramebufferRenderbuffer(GL_FRAMEBUFFER,GL_DEPTH_ATTACHMENT,GL_RENDERBUFFER,self.rbd)
		st = glCheckFramebufferStatus(GL_FRAMEBUFFER)
		print (st)
		
		glBindFramebuffer(GL_FRAMEBUFFER,0)
		glBindRenderbuffer(GL_RENDERBUFFER, 0)
		glBindTexture(GL_TEXTURE_2D, 0)
		
		
		
	def pre_FBO_rendering(self):
		#this method set up all necessary before rendering
		#program to use?
		#bind fbo and texture
		#glBindTexture(GL_TEXTURE_2D,0)
		glBindFramebuffer(GL_FRAMEBUFFER,self.fbo)

		
		glClearColor(0.0,0.0,0.0,1.0)
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
		#add steps to clear the buffers as necessary
		glViewport(0,0,self.size2[0], self.size2[1])
		
		
	def post_FBO_rendering(self):
		glBindTexture(GL_TEXTURE_2D, 0)
		glBindFramebuffer(GL_FRAMEBUFFER,0)
		
	def get_rtt_id(self):
		return self.rtt
	
	def save_snapshot(self,filename):
		if hasattr(self, 'rtt'):
			#save picture
			glBindFramebuffer(GL_FRAMEBUFFER,self.fbo)
			data = glReadPixels(0,0,self.size2[0], self.size2[1], GL_RGBA,  GL_UNSIGNED_BYTE)
			#OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING = False
			#data = glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE, outputType = 'str' )
			from PIL import Image
			image = Image.frombytes('RGBA', self.size2, data, 'raw')
			image = image.transpose(Image.FLIP_TOP_BOTTOM)
			image.save ('Media/Textures/'+filename)
			glBindFramebuffer(GL_FRAMEBUFFER,0)
			return 1
		else: return -1
	
	