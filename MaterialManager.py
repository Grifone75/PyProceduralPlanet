

import OpenGL 
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# PyOpenGL 3.0.1 introduces this convenience module...
from OpenGL.GL.shaders import *


class MaterialManager:
    Materials = {}
    
    def __init__(self):
        pass
    
    @classmethod   
    def load_material(cls,vertexfile,fragmentfile,materialname):
        if not glUseProgram:
            print 'Missing Shader Objects!'
            sys.exit(1)
    
        with open(vertexfile) as myfile:
            vertexstring = myfile.read()

        with open(fragmentfile) as myfile:
            fragmentstring = myfile.read()
               
        program = compileProgram( 
            compileShader(vertexstring,GL_VERTEX_SHADER),
            compileShader(fragmentstring,GL_FRAGMENT_SHADER),)
        
        cls.Materials[materialname]=program

        #cls.material_count +=1
        
    @classmethod 
    def get_material(cls,materialname):
        return cls.Materials[materialname]
    
    @classmethod 
    def use_material(cls,materialname):
        glUseProgram(cls.Materials[materialname])
        
    
