
class SceneMaster:
	Scenes = {}
	Materials = None

	def __init__(self,name):
		self.name = name
		self.Scenes[name] = self
		self.predrawables = [] # e.g. lights (in this order)
		self.drawables = [] # e.g. objects (in order of calling)
		self.postdrawables = [] # e.g.  other effects
		
	def attachmaterials(self, materials):
		if self.Materials == None:
			SceneMaster.Materials = materials
	
		
	def draw(self):
	
		try:
			self.camera.look()
		except:
			pass
	
		for element in self.predrawables:
			element.draw()
			
		for element in self.drawables:
			element.draw()
			
		for element in self.postdrawables:
			element.draw()
		
		try:
			self.hud.draw()
		except:
			pass
	
	def update(self):
	

		self.camera.update()

		
		for element in self.predrawables:
			element.update()
			
		for element in self.drawables:
			element.update()
			
		for element in self.postdrawables:
			element.update()	
   
 		try:
 			self.hud.update()
 		except:
 			pass
