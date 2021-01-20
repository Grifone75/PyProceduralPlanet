from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

class LightObj:

	def __init__(self,gl_number,pos,scenemaster):
		self.position = pos
		self.gl_number = gl_number
		glLightfv(self.gl_number,GL_POSITION,self.position)
		#scenemaster to be implemented
		
	def draw(self):
		pass
		#glLightfv(self.gl_number,GL_POSITION,self.position)
		
	def update(self):
		pass