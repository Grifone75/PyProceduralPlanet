

 
import OpenGL 

import numpy as np
import quaternions as qts
from quaternions import Quat
from OpenGL.arrays import vbo  
import random
import time
import RendObject

OpenGL.ERROR_ON_COPY = True 
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# PyOpenGL 3.0.1 introduces this convenience module...
from OpenGL.GL.shaders import *

import time, sys
  
  
class RendLight():
    
    def __init__(self, pos = (0.0,0.0,0.0),intensity = (1.0,1.0,1.0)):
        self.position = np.array(list(pos))
        self.intensity = np.array(list(intensity))
        
    def get_pos(self):
        return self.position
    
    def get_intensity(self):
        return self.intensity