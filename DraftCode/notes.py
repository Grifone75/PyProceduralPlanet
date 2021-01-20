


pseudo code

DRAW:

get time ref
all initialization not depending by VBO (attribs, matrix rotations, etc)

for each of the 6 VBOs
	draw the active VBO
	switch the active VBO
	
compute drawtime
compute accumulated free time += (frame target time - buffer time - drawtime)
	
	
UPDATE:
	
	STUFF TO DO EACH TIME
		usual object roto translation ,
		camera projection in object space
	STUFF TO DO IN TIME RESOURCED:
	if all VBO updated, set to zero the update flag
	if
	determine VBO update priority
			(not updated, sorted by distance, unflag (set updated) the ones not facing the camera)
	if acc free time > 0
		update one unactive VBO, set it updated (note, this step can also be done in two pass, 1)tessellation and 2)update
		deduct update time from acc free time
	

note:	
calculation of cube faces not facing the camera
	store for each face the normal in object space (to be done at each face, init phase)
	compute the dot product between this normal and the projected camera pos in object space 
	
	
	
	
	#this is the traditional methos
	angle = acos(dotProduct(Va.normalize(), Vb.normalize()));
	cross = crossProduct(Va, Vb);
	if (dotProduct(Vn, cross) < 0) { // Or > 0
		angle = -angle;
	}
	#but in order just to give priority or inhibite the update of a face tessellation we can use a rougher and faster method
	get the normalized/cubized camera pos
	one of its dimensions must be 1 or -1 --> this allow to check the 1 side to update
	if the other dimensions are near zero, we are near the center of a cube face - no need to update the rest
	otherwise, update the cube faces with the higher component (in plus or minus)
	ex: [1, 0.1, 0.2] --> only update right face (positive 1 in X) (in cube space)
	[-1,0.8,0.3] --> update first left face then upper face (in cube space)
	[1, 0.2,-0.9] --> update first right face, then back face (in cube space)
	

	
normal calculation in vertex shader
		
		before sphere transformation
		- determine 2 points with du and dv from the face cube (code to determine the face cube, etc)
		transform the 3 points (p, pdu, pdv)
		
		pdu = p
		pdv = p
		if x = 1 then {
			pdu.y+=0.1
			pdv.z+=0.1
			}
		if x = -1 then {
			pdu.y+=0.1
			pdv.z-=0.1
			}
		if y = 1 then {
			pdu.x -=0.1
			pdv.z +=0.1
			}
		if y = -1 then {
			pdu.x +=0.1
			pdv.z +=0.1
			}
		if z = 1 then {
			pdu.y +=0.1
			pdv.x -=0.1
			}
		if z = -1 then {
			pdu.y +=0.1
			pdv.x +=0.1
			}
			
		
		
		
		evaluate noise function for the 3 points (p, pdu, pdv)
		
		now considering the 3 points:
			
		calculate the normal (pdu is the first vector, pdv is the second vector)
		
		
		
	
	
	
	
	
	