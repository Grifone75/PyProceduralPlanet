#-------------------------------------------------------------------------------
# Name:        PyPlanet
# Purpose:     create a procedural planet/universe generator
#
# Author:      Fabrizio
#
# Created:     01/04/2015
# Copyright:   (c) Fabrizio 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import OpenGL 

import numpy as np
import quaternions as qts
from quaternions import Quat
from OpenGL.arrays import vbo
import RendObject
import RendObjectVBO
import RenderablePlanet
import random
import time
import transformations
import PIL as pl
from PIL import Image
from SceneManager import SceneManager
from MaterialManager import MaterialManager
from RequestManager import RequestManager
from SceneMaster import SceneMaster
from LightObj import LightObj
from TextureAtlas import TextureAtlas
from PlanetDescriptor import PlanetDescriptor
import glFreetype
from HudFont import HudFont
#from pyglet.gl.glext_arb import GL_NV_depth_buffer_float




OpenGL.ERROR_ON_COPY = True 
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# PyOpenGL 3.0.1 introduces this convenience module...
from OpenGL.GL.shaders import *

import time, sys

from Utils import *


programs = None

        
def loadTexture(name):
    img = pl.Image.open(name)
    img_data = np.array(list(img.getdata()),np.short)
     
    id = glGenTextures(1)
    glPixelStorei(GL_UNPACK_ALIGNMENT,1)
    glBindTexture(GL_TEXTURE_2D,id)
    glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D,0, GL_RGB, img.size[0],img.size[1],0,GL_RGBA,GL_UNSIGNED_BYTE,img_data)
    glBindTexture(GL_TEXTURE_2D,0)
    return id




#class for a HUD object (to be improved)
class HUDObject:
    def __init__(self):
        self.test = True
        self.displaylist = []
        self.font = HudFont('Media/Fonts/VeraMono.ttf',16) 
        
    def registersignal(self,signal):
        self.displaylist.append(signal)

    def draw(self):

        glUseProgram(0)
        global frametimer
        #set up the matrixes for ortho projection
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, 640, 0, 400,-1,1)
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glTexEnvf( GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE )
        glEnable( GL_BLEND )
        glEnable( GL_COLOR_MATERIAL )
        glColorMaterial( GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE )
        glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA )
        glEnable( GL_TEXTURE_2D )
        #set up the matrixes for screen coordinates
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        

        glTranslated(20,400,0)

        glPushMatrix()
        #glScalef(0.05,0.05,0.05)
        glColor3f(0.9, 0.9, 0.9)
        self.font.drawtext("This is a test")
        glPopMatrix()
        glTranslated(0,-10,0)
        glPushMatrix()
        glScalef(0.05,0.05,0.05)
        text1 = "framerate is "+str(frametimer.fpssignal.getvalue())
        glutStrokeString(GLUT_STROKE_MONO_ROMAN,text1)
        glPopMatrix()
        glPushMatrix()
        signals = GlobalSignals.get_signals()
        for key,element in signals.iteritems():
            glColor3f(0.9, 0.9, 0.9)
            glTranslated(0,-10,0)
            glPushMatrix()
            glScalef(0.05,0.05,0.05)
            try:
                stringa = element.getname()+' {0:.2f}'.format(element.getvalue()) #+' (max:'+str(element.getmax())+')'
            except:
                stringa = element.getname()+' '+str(element.getvalue())
            glutStrokeString(GLUT_STROKE_MONO_ROMAN,stringa)
            glPopMatrix()
        glPopMatrix()
        #reset the matrixes and flags for 3d drawing
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)

     
class CameraObj:
    #constants for camera initialisation
    POSITION = [7500.0,7500.0,-10000.0]
    
    def __init__(self):
        #code for camera initialisation
        self.orientation = transformations.quaternion_from_euler(0.0,0.0,0.0)
        self.input_orientation = transformations.quaternion_from_euler(0.0,0.0,0.0)
        self.position = np.array(self.POSITION)
        self.velocity = np.zeros(3)
        self.c_acceleration = np.zeros(3)
        self.t_last_update = time.time()
        self.set_cam_properties(75, 1.0, 1.0, 200000.0)
        #self.FOVangle = CameraObj.FOVY
        self.view = np.eye(4,dtype=np.float32)

        
    def look(self):
        #code for visual transformation
        #glLoadIdentity()  
        # create a 4x4 rot matrix based on the quaternion orientation. nb, transpose required for opengl multmatrix
        t = transformations.quaternion_matrix(self.orientation)
        selfrot = np.ascontiguousarray(np.transpose(transformations.quaternion_matrix(self.orientation)))
        #glMultMatrixd(selfrot)
        #glTranslatef(*-self.position)
        #tt = glGetFloatv(GL_MODELVIEW_MATRIX)

        #NEW CODE MODERN
        R = selfrot
        T = transformations.translation_matrix(-self.position)
        self.view = np.dot(R,T).T

    def move_rotate(self,alfax,alfay,alfaz, ax, ay, az):


        if alfax <> 0:
            qr = transformations.quaternion_from_euler(0.0, -alfax, 0.0 )
            self.input_orientation = transformations.quaternion_multiply(self.input_orientation, qr)
            #add code to renormalize the quat
 
        if alfay <> 0:
            qr = transformations.quaternion_from_euler( -alfay,0.0, 0.0)
            self.input_orientation = transformations.quaternion_multiply(self.input_orientation, qr)
            #add code to renormalize the quat
  
        if alfaz <> 0:
            qr = transformations.quaternion_from_euler( 0.0, 0.0, -alfaz)
            self.input_orientation = transformations.quaternion_multiply(self.input_orientation, qr)
            #add code to renormalize the quat
            
        self.c_acceleration[:]=[ax,ay,az]
 
    def update(self):

        new_time = time.time()
        dt = new_time - self.t_last_update
        self.t_last_update = new_time
        
        
        self.orientation = transformations.quaternion_slerp(self.orientation, self.input_orientation, 0.1)

        
        mmv = self.view
        dleft = np.array([mmv[0,0],mmv[1,0],mmv[2,0]]) # delta along the left camera axis
        dup = np.array([mmv[0,1],mmv[1,1],mmv[2,1]]) # delta along the up camera axis
        dpoint = np.array([mmv[0,2],mmv[1,2],mmv[2,2]]) # delta along the pointer camera axis
        
        vleft = np.dot(self.velocity,dleft)
        vup = np.dot(self.velocity,dup)
        vpoint = np.dot(self.velocity,dpoint)
        velocity_norm = np.linalg.norm(self.velocity)
        
        acceleration = dleft*self.c_acceleration[0]+dup*self.c_acceleration[1]+dpoint*self.c_acceleration[2]
        
        if GlobalSettings.read('killspeed'):
            GlobalSignals.set('speed killing: ','On')
            self.velocity *=0.95
            if velocity_norm < 0.05:
                GlobalSettings.set('killspeed', False)
                GlobalSignals.set('speed killing: ','Off')
        else: 
            GlobalSignals.set('speed killing: ','Off') 
            
            
        if GlobalSettings.read('alignspeed'):
            GlobalSignals.set('speed aligning: ','On')
            self.velocity = dleft*vleft*0.95+dup*vup*0.95
            self.velocity += -dpoint*np.sqrt(velocity_norm**2-(vleft*0.95)**2-(vup*0.95)**2)
            if (vup<0.05 and vleft<0.05):
                GlobalSettings.set('alignspeed', False)
                GlobalSignals.set('speed aligning: ','Off')
        else:
            GlobalSignals.set('speed aligning: ','Off')   

            
        self.velocity = self.velocity+acceleration*dt
        self.position = self.position+self.velocity*dt
        
        self.c_acceleration[:]=[0,0,0]
        
        GlobalSignals.set('velocity: ',[vpoint,vleft,vup])

        
    def set_near_far(self,near,far):
        self.near = near
        self.far = far
        self.proj = perspective(self.fov, self.aspect, self.near, self.far)
    
    def set_cam_properties(self,fov,aspect,near,far):
        self.aspect = aspect
        self.fov = fov
        self.near = near
        self.far = far
        self.proj = perspective(self.fov, self.aspect, self.near, self.far)
        
    def set_fov(self,fov):
        self.fov = fov
        self.proj = perspective(self.fov, self.aspect, self.near, self.far)
        
    def set_aspect(self,aspect):
        self.aspect = aspect
        self.proj = perspective(self.fov, self.aspect, self.near, self.far)
        

def InitGL(SceneMgr, Width, Height):  # We call this right after our OpenGL window is created.
    
    SceneMgr.set_base_scene()

    
    
def ReSizeGLScene(Width, Height):
    
    global SceneMgr
    if Height == 0:                        # Prevent A Divide By Zero If The Window Is Too Small 
        Height = 1

    SceneMgr.set_base_w_h(Width,Height)

    
def DrawGLScene():
    global scene
    global camera
    global hud
    global frametimer
    global SceneMstr
    global Signals
 
    
    #update the scene
    frametimer.update()
    RequestManager.update()
    t0 = time.time()
    SceneMstr.update()
    Signals['update'].setvalue((time.time()-t0)*1000)
    # Clear The Screen And The Depth Buffer
    glFinish()
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    t0 = time.time()
    #draw all objects in the scene
    
    SceneMstr.draw()
    Signals['draw'].setvalue((time.time()-t0)*1000)
    #  since this is double buffered, swap the buffers to display what just got drawn. 
    glFinish()
    glutSwapBuffers()
            

            
 # The function called whenever a key is pressed. Note the use of Python tuples to pass in: (key, x, y)  
def keyPressed(*args):
    global SceneMgr
    global MaterialMgr
    global programs
    global scene
    global speed
    

    
    # If escape is pressed, kill everything.
    if args[0] == '\033': #ESC to exit
        sys.exit()
    elif args[0] == '\141': # a to wireframe
        GlobalSettings.set('drawmode', GL_FRONT_AND_BACK)
        GlobalSettings.set('linemode', GL_LINE)
        glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
    elif args[0] == '\145': # e to fill
        GlobalSettings.set('drawmode', GL_FRONT)
        GlobalSettings.set('linemode', GL_FILL)
        glPolygonMode(GL_FRONT,GL_FILL)
    elif args[0] == '\167': # w to special test
        #GlobalSettings.set('snapshot',True)
        if GlobalSettings.read('nosea'):
            GlobalSettings.set('nosea',False)
        else: 
            GlobalSettings.set('nosea',True)
    elif args[0] == '\053': # +
        if speed < 200: speed *=2.0
        GlobalSignals.set('acc', speed)
    elif args[0] == '\055': # -
        if speed > 0.01: speed /=2.0
        GlobalSignals.set('acc', speed)
    elif args[0] == '\052': # *
        if GlobalSettings.read('killspeed'):
            GlobalSettings.set('killspeed',False)
        else:
            GlobalSettings.set('killspeed',True)
            GlobalSettings.set('alignspeed',False) #also reset speed aligning
    elif args[0] == '\057': # /
        if GlobalSettings.read('alignspeed'):
            GlobalSettings.set('alignspeed',False)
        else:
            GlobalSettings.set('alignspeed',True)


 
def MouseButton(button, state, x, y):
    global mousex, mousey, action
    if (button==GLUT_LEFT_BUTTON) and (state==GLUT_DOWN):
        mousex=x 
        mousey=y
        action = 'ROTATE'
    if (button==GLUT_RIGHT_BUTTON) and (state==GLUT_DOWN):
        mousex=x 
        mousey=y
        action = 'TRANSLATE'
    if (button==GLUT_MIDDLE_BUTTON) and (state==GLUT_DOWN):
        mousex=x 
        mousey=y
        action = 'TRANSVERSE'   
    if state ==GLUT_UP: action = 'NONE'

        
def MouseMove(x, y):
    global mousex 
    global mousey
    global camera
    global action
    global speed
    
    if action == 'ROTATE':
        camera.move_rotate((x-mousex)/100.0,(y-mousey)/100.0,0,0,0,0)
        
    if action == 'TRANSLATE':
        camera.move_rotate(0,0,0,(x-mousex)*speed,-(y-mousey)*speed,0)
    
    if action == 'TRANSVERSE':
        camera.move_rotate(0,0,(x-mousex)/100.0,0,0,(y-mousey)*speed)
    
    mousex = x
    mousey = y
    
            
def main():
    global window
    global scene
    global hud
    global camera
    global mousex
    global mousey
    global action
    global frametimer
    global SceneMgr
    global SceneMstr
    global Signals
    global speed
    
    
    speed = 10.0
    
    RequestManager.set_time_budget(10)
    
    GlobalSettings.set('snapshot',False)
    
    #define the scenemaster object for the main scene
    SceneMstr = SceneMaster('Main Scene')
    #create the camera object & attach to scenemaster
    camera = CameraObj()
    SceneMstr.camera = camera #to be replaced by a setter function
    #define the scene manager for the switching between main scene and fbos
    SceneMgr = SceneManager(128,camera)


    #initialise the globals for mouse control
    mousex = 0
    mousey = 0
    action = 'NONE'
    #init the timer object
    frametimer = UtilTimer(20)
    
    #init the graphic system and create a window
    glutInit(sys.argv)

    # Select type of Display mode: double buffer,RGBA color,Alpha components supported , Depth buffer
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)

    
    # get a 640 x 480 window 
    glutInitWindowSize(1024, 800) 
    # the window starts at the upper left corner of the screen 
    glutInitWindowPosition(0, 0)
    window = glutCreateWindow("GL Planet")

   
    
    print(glGetIntegerv(GL_DEPTH_BITS))
    
    # Register the drawing function with glut, BUT in Python land, at least using PyOpenGL, we need to
    # set the function pointer and invoke a function to actually register the callback, otherwise it
    # would be very much like the C version of the code.    
    glutDisplayFunc(DrawGLScene)
    
    # Uncomment this line to get full screen.
    #glutFullScreen()
   
    # When we are doing nothing, redraw the scene.
    glutIdleFunc(DrawGLScene)
    # Register the function called when our window is resized.
    glutReshapeFunc(ReSizeGLScene)
    
    #registra la funzione per il mouse
    glutMouseFunc(MouseButton)
    glutMotionFunc(MouseMove)
    
    # Register the function called when the keyboard is pressed.  
    glutKeyboardFunc(keyPressed)

    # Initialize our window. 
    InitGL(SceneMgr, 800, 480) 
    
    #create the HUD object & attach to scenemaster
    hud = HUDObject()
    SceneMstr.hud = hud  #to be replaced by a setter function
    
    #DEBUG: register some measurements
    Signals = {}
    r1 = ReadableSignal('update time: ',0,10)
    r2 = ReadableSignal('draw time: ',0,10)
    hud.registersignal(r1)
    hud.registersignal(r2)
    Signals['update'] = r1
    Signals['draw'] = r2 
    
    #planet_texture = loadTexture('Media/Textures/Planet2.png')

    SceneUtils = {}
    SceneUtils['fbo'] = SceneMgr
    SceneUtils['hud'] = hud
    SceneUtils['cam'] = camera
    
    #initialise materials
    MaterialManager.load_material('Media/Materials/heightmat1.glsv', 'Media/Materials/heightmat1.glsf', 'fbomatheight')
    MaterialManager.load_material('Media/Materials/terra_v1.glsv','Media/Materials/terra_v1.glsf','planetmat1')
    MaterialManager.load_material('Media/Materials/normmat2.glsv','Media/Materials/normmat2.glsf','fbomatnorm')
    MaterialManager.load_material('Media/Materials/ocean_v1.glsv','Media/Materials/ocean_v1.glsf','planetsea')
    MaterialManager.load_material('Media/Materials/surfmeasure.glsv','Media/Materials/surfmeasure.glsf','surfacemeasure')
    MaterialManager.load_material('Media/Materials/sky_int_v1.glsv','Media/Materials/sky_int_v1.glsf','skybox_inside')
    MaterialManager.load_material('Media/Materials/underwater_v1.glsv','Media/Materials/underwater_v1.glsf','underwater')

    
    GlobalSettings.set('nosea',True)
    
    #create the planet descriptor
    P1 = PlanetDescriptor('Primum',10000.0,30.0, 0.2,'fbomatheight','fbomatnorm','planetmat1')
    #P1.GenerateTexture()
    
      
    # create the cube & attach to scenemaster
    # TO CHANGE: all various methods to attach things to the rendcubevbo object camera, scenemgr, materialmgr, to be
    #            replaced by a SceneMaster pointer
    scene = RenderablePlanet.RenderablePlanet('facevbo',0,0,-1500,SceneUtils,P1)
    SceneMstr.drawables.append(scene) # to be replaced by a setter in scenemaster


    scene.Timer = frametimer

    


    # Start Event Processing Engine    
    glutMainLoop()

# Print message to console, and kick off the main to get it rolling.

if __name__ == "__main__":
    print "Hit ESC key to quit."
    main()         
            
            
        
