import threading, logging

class BaseSource(threading.Thread):
	_initiated=False	
	
	def __init__(self):
		super(BaseSource, self).__init__()
		self._initiated=True
		self.daemon=True
		self.logger = logging.getLogger(__name__)

	def run(self):
		pass
