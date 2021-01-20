

import numpy as np
from SurfaceNode import SurfaceNode



c00 = np.array([0.0,0.0,0.0])
c01 = np.array([0.0,1.0,0.0])
c11 = np.array([1.0,1.0,0.0])
c10 = np.array([1.0,0.0,0.0])

t1 = [c00,c01,c00]
t1.append(c11)
t2=np.array(t1)


test = SurfaceNode(0,c00,c01,c11,c10)

datad = {'vertex': [], 'index':[]}

test.get_triangles(datad, 0)

print datad

test.divide()

print 'after divide'

datad = {'vertex': [], 'index':[]}

test.get_triangles(datad, 0)

arridx = np.array(datad['index'])
arrvx = np.array(datad['vertex'])

print arridx
print arrvx



