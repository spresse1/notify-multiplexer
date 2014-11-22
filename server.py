#!/usr/bin/env python3

class Server():
	import configparser, logging
	
	def __init__(self, settings):
		import importlib
		
		self.conf = self.configparser.ConfigParser()
		self.conf.read(settings)
		
		self.sourcestr=["UnixSocketSource"] #self.conf['main']['modules'].split(',')
		self.sourcemods = []
		
		self.logger = self.logging.getLogger(__name__)
		self.logger.setLevel(self.logging.DEBUG)
		
		for mod in self.sourcestr:
			imod = importlib.import_module(mod)
			tclass = getattr(imod, mod.split(".")[-1])			
			iclass = tclass(self)
			self.sourcemods.append(iclass)
			iclass.start()
		
		self.sinkstr=['BaseSink', 'HTTPSSink']
		self.sinkmods = []
		
		for mod in self.sinkstr:
			imod = importlib.import_module(mod)
			tclass = getattr(imod, mod.split(".")[-1])
			iclass = tclass()
			self.sinkmods.append(iclass)
			iclass.start()
	
	def send(self, category, tags):
		self.logger.debug("Mesage Category: %s" % category)
		self.logger.debug("Tags: %s" % str(tags))
		for mod in self.sinkmods:
			mod.send(category, tags)


from time import sleep

if __name__ == "__main__":
	s = Server("/etc/notify-multiplexer/server.conf")
	
	while True:
		sleep(120)
