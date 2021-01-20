
import time
import numpy as np
import math as mt

def smoothstepexp(x,offset,min,max,slope):
    ecr = mt.exp(offset*slope)
    erx = mt.exp(slope*x)
    return (min*ecr+max*erx)/(ecr+erx)

def clamp(x,lo,hi):
    if x > hi: return hi
    elif x < lo: return lo
    else: return x

def smoothstep(ed0,ed1,x):
    #scale bias and saturate in 0..1 
    x = clamp((x-ed0)/(ed1-ed0),0.0,1.0)
    #eval polynomial
    return (x**2)*(3-2*x)
    
def smoothstephilo(lo,hi,ed0,ed1,x):
    return lo+smoothstep(ed0, ed1, x)*(hi-lo)


def sphere2cube(position):

    [x,y,z] = [xc,yc,zc] = position
    [fx,fy,fz] = np.abs(position)

    inverseSqrt2 = 0.70710676908493042

    if (fy >= fx) and (fy >= fz):
        a2 = (x**2)*2.0
        b2 = (z**2)*2.0
        inner = -a2+b2-3
        innersqrt = -mt.sqrt(inner**2-12.0*a2)

        if (x == 0.0) or (x==-0.0):
            xc = 0.0
        else:
            xc = mt.sqrt(innersqrt+a2-b2+3.0)*inverseSqrt2

        if (z == 0.0) or (z==-0.0):
            zc = 0.0
        else:
            zc = mt.sqrt(innersqrt-a2+b2+3.0)*inverseSqrt2

        if (xc > 1.0): xc = 1.0
        if (zc > 1.0): zc = 1.0

        if (x < 0): xc = -xc;
        if( z < 0): zc = -zc;

        if (y>0): 
            yc =1.0 #top face
            f = 5
        else: 
            yc = -1.0 #bottom face
            f = 4

    elif ((fx >= fy) and (fx >= fz)):

        a2 = (y**2)*2.0
        b2 = (z**2)*2.0
        inner = -a2+b2-3
        innersqrt = -mt.sqrt(inner**2-12.0*a2)

        if (y == 0.0) or (y==-0.0):
            yc = 0.0
        else:
            yc = mt.sqrt(innersqrt+a2-b2+3.0)*inverseSqrt2

        if (z == 0.0) or (z==-0.0):
            zc = 0.0
        else:
            zc = mt.sqrt(innersqrt-a2+b2+3.0)*inverseSqrt2

        if (yc > 1.0): yc = 1.0
        if (zc > 1.0): zc = 1.0

        if (y < 0): yc = -yc;
        if( z < 0): zc = -zc;

        if (x>0): 
            xc = 1.0 #right face
            f = 3
        else: 
            xc = -1.0 #left face
            f = 1

    else:

        a2 = (x**2)*2.0
        b2 = (y**2)*2.0
        inner = -a2+b2-3
        innersqrt = -mt.sqrt(inner**2-12.0*a2)

        if (x == 0.0) or (x==-0.0):
            xc = 0.0
        else:
            xc = mt.sqrt(innersqrt+a2-b2+3.0)*inverseSqrt2

        if (y == 0.0) or (y==-0.0):
            yc = 0.0
        else:
            yc = mt.sqrt(innersqrt-a2+b2+3.0)*inverseSqrt2

        if (xc > 1.0): xc = 1.0
        if (yc > 1.0): yc = 1.0

        if (x < 0): xc = -xc;
        if( y < 0): yc = -yc;

        if (z>0): 
            zc =1.0 #front face
            f = 0
        else: 
            zc = -1.0 #back face
            f = 2

    return ([xc,yc,zc],f)
    
def cube2sphere(p):
    x2 = p[0]**2
    y2 = p[1]**2
    z2 = p[2]**2
    # sphericize
    xs = p[0] * mt.sqrt(1.0-(y2*0.5)-(z2*0.5)+(y2*z2/3.0))
    ys = p[1] * mt.sqrt(1.0-(z2*0.5)-(x2*0.5)+(z2*x2/3.0))
    zs = p[2] * mt.sqrt(1.0-(x2*0.5)-(y2*0.5)+(x2*y2/3.0))
    return np.array([xs,ys,zs])   





def translate(M, x, y=None, z=None):
    """
    translate produces a translation by (x, y, z) . 
    
    Parameters
    ----------
    x, y, z
        Specify the x, y, and z coordinates of a translation vector.
    """
    if y is None: y = x
    if z is None: z = x
    T = [[ 1, 0, 0, x],
         [ 0, 1, 0, y],
         [ 0, 0, 1, z],
         [ 0, 0, 0, 1]]
    T = np.array(T, dtype=np.float32)
    M[...] = np.dot(M,T).T


def scale(M, x, y=None, z=None):
    """
    scale produces a non uniform scaling along the x, y, and z axes. The three
    parameters indicate the desired scale factor along each of the three axes.

    Parameters
    ----------
    x, y, z
        Specify scale factors along the x, y, and z axes, respectively.
    """
    if y is None: y = x
    if z is None: z = x
    S = [[ x, 0, 0, 0],
         [ 0, y, 0, 0],
         [ 0, 0, z, 0],
         [ 0, 0, 0, 1]]
    S = np.array(S,dtype=np.float32).T
    M[...] = np.dot(M,S)


def xrotate(M,theta):
    t = mt.pi*theta/180
    cosT = mt.cos( t )
    sinT = mt.sin( t )
    R = np.array(
        [[ 1.0,  0.0,  0.0, 0.0 ],
         [ 0.0, cosT,-sinT, 0.0 ],
         [ 0.0, sinT, cosT, 0.0 ],
         [ 0.0,  0.0,  0.0, 1.0 ]], dtype=np.float32)
    M[...] = np.dot(M,R)

def yrotate(M,theta):
    t = mt.pi*theta/180
    cosT = mt.cos( t )
    sinT = mt.sin( t )
    R = np.array(
        [[ cosT,  0.0, sinT, 0.0 ],
         [ 0.0,   1.0,  0.0, 0.0 ],
         [-sinT,  0.0, cosT, 0.0 ],
         [ 0.0,  0.0,  0.0, 1.0 ]], dtype=np.float32)
    M[...] = np.dot(M,R)

def zrotate(M,theta):
    t = mt.pi*theta/180
    cosT = mt.cos( t )
    sinT = mt.sin( t )
    R = np.array(
        [[ cosT,-sinT, 0.0, 0.0 ],
         [ sinT, cosT, 0.0, 0.0 ],
         [ 0.0,  0.0,  1.0, 0.0 ],
         [ 0.0,  0.0,  0.0, 1.0 ]], dtype=np.float32)
    M[...] = np.dot(M,R)


def rotate(M, angle, x, y, z, point=None):
    """
    rotate produces a rotation of angle degrees around the vector (x, y, z).
    
    Parameters
    ----------
    M
       Current transformation as a np array

    angle
       Specifies the angle of rotation, in degrees.

    x, y, z
        Specify the x, y, and z coordinates of a vector, respectively.
    """
    angle = mt.pi*angle/180
    c,s = mt.cos(angle), mt.sin(angle)
    n = mt.sqrt(x*x+y*y+z*z)
    x /= n
    y /= n
    z /= n
    cx,cy,cz = (1-c)*x, (1-c)*y, (1-c)*z
    R = np.array([[ cx*x + c  , cy*x - z*s, cz*x + y*s, 0],
                     [ cx*y + z*s, cy*y + c  , cz*y - x*s, 0],
                     [ cx*z - y*s, cy*z + x*s, cz*z + c,   0],
                     [          0,          0,        0,   1]]).T
    M[...] = np.dot(M,R)


def ortho( left, right, bottom, top, znear, zfar ):
    assert( right  != left )
    assert( bottom != top  )
    assert( znear  != zfar )
    
    M = np.zeros((4,4), dtype=np.float32)
    M[0,0] = +2.0/(right-left)
    M[3,0] = -(right+left)/float(right-left)
    M[1,1] = +2.0/(top-bottom)
    M[3,1] = -(top+bottom)/float(top-bottom)
    M[2,2] = -2.0/(zfar-znear)
    M[3,2] = -(zfar+znear)/float(zfar-znear)
    M[3,3] = 1.0
    return M
        
def frustum( left, right, bottom, top, znear, zfar ):
    assert( right  != left )
    assert( bottom != top  )
    assert( znear  != zfar )

    M = np.zeros((4,4), dtype=np.float32)
    M[0,0] = +2.0*znear/(right-left)
    M[2,0] = (right+left)/(right-left)
    M[1,1] = +2.0*znear/(top-bottom)
    M[3,1] = (top+bottom)/(top-bottom)
    M[2,2] = -(zfar+znear)/(zfar-znear)
    M[3,2] = -2.0*znear*zfar/(zfar-znear)
    M[2,3] = -1.0
    return M

def perspective(fovy, aspect, znear, zfar):
    assert( znear != zfar )
    h = np.tan(fovy / 360.0 * np.pi) * znear
    w = h * aspect
    return frustum( -w, w, -h, h, znear, zfar )




class ReadableSignal:
    def __init__(self,name,value, samples = 1):
        self.name = name
        self.value = value
        self.samples = samples
        self.sample_queue = []
        self.max_in_history = -999999999
        self.min_in_history = 99999999
        

    def getname(self):
        return self.name

    def getvalue(self):
        if self.samples == 1: return self.value
        else:
            v = 0.0
            for el in self.sample_queue:
                v += el
            return v/len(self.sample_queue)
        
    def getmax(self):
        return self.max_in_history
    
    def getmin(self):
        return self.min_in_history

    def setvalue(self,value):
        self.value = value
        self.sample_queue.append(value)
        if len(self.sample_queue)>self.samples:
            del self.sample_queue[0]
        try:
            if value > self.max_in_history: self.max_in_history = value
            if value < self.min_in_history: self.min_in_history = value
        except:
            pass

        
    


class UtilTimer:
    def __init__(self, count):
        self.t0 = 0
        self.t1 = 0
        self.t0delta = 0;
        self.deltat = 0;
        self.counter = self.count = count
        self.fpssignal = ReadableSignal('fps',0)

    def update(self):
        if self.t0 == 0:
            self.t0 = self.t0delta = time.time()
        else:
            self.t1 = self.t0
            self.t0 = time.time()
            self.counter -=1
            if self.counter == -1:
                self.deltat = self.t0 - self.t0delta
                self.t0delta = self.t0
                self.fpssignal.setvalue(self.count / (self.deltat))
                self.counter = self.count
                
    def start(self):
        self.laptime = time.time()
        
    def stop(self):
        t1 = self.laptime
        self.laptime = time.time()
        return self.laptime - t1

    
class GlobalSettings:
    
    Settings={}
    
    @classmethod
    def init(cls):
        cls.Settings['version'] = 0.1
        
    @classmethod    
    def set(cls,attr,value):
        cls.Settings[attr]=value
        
    @classmethod
    def read(cls,attr):
        try:
            return cls.Settings[attr]
        except:
            return False
        
    
class GlobalSignals:
    
    Signals = {}
    
    @classmethod
    def init(cls):
        pass
        
    @classmethod    
    def set(cls,attr,value):
        if attr in cls.Signals:
            cls.Signals[attr].setvalue(value)
        else:
            cls.Signals[attr]=ReadableSignal(attr,value)
        
    @classmethod
    def read(cls,attr):
        try:
            return cls.Signals[attr].getvalue()
        except:
            return -1
        
    @classmethod
    def get_signals(cls):
        try:
            return cls.Signals
        except:
            return -1   
    
