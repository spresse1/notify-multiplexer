import threading

class BaseSink(threading.Thread):
	_initiated=False	
	
	def __init__(self):
		super(BaseSink, self).__init__()
		self._initiated=True

	def _send(self,category, tags):
		if _initiated == False:
			raise Exception("super(" + self.__class__.__name__ + 
				", self).__init__() not called!")
		self.send()
		
	def send(self, category, tags):
		pass
