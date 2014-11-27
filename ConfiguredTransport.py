import threading
import socket
import logging
from time import sleep

class ConfiguredTransport(threading.Thread):
	"""An implemetation of the transport layer for the NetworkBus class, using direct TCP/TLS connections to a pre-specified set of other servers."""
	
	# Keeps track of active connections
	connections={}
	connectionsLock=threading.Lock()
	threads=[]
	
	def __init__(self,hosts, logger=None):
		"""Takes a list of hosts to connect to, establishes connections, if possible, and will attempt periodic reconnections otherwise."""
		if logger:
			self.logger = logger
			self.logger.info("Adopted passed in logger for %s" % __name__)
			print(self.logger.getEffectiveLevel())
		else:
			self.logger = logging.getLogger(__name__)
			self.logger.warning("Created logger for %s" % __name__)
		self.logger.info("Starting ConfiguredTransport...")
		
		for pair in hosts:
			self.connect(pair[0],pair[1])
		
	def connect(self,host, port):
		self.logger.debug("Initiating connection to %s:%d" % (host, int(port)))
		thread=ConnectionThread(host,int(port), self.connections, self.connectionsLock,self.logger)
		thread.start()
		self.threads.append(thread)
	
	def disconnect(self,host_port_pair):
		with self.connectionsLock:
			del connections[(host,port)]
	
	def send():
		pass
	
	def receive():
		pass
		
class ConnectionThread(threading.Thread):
	def __init__(self, host, port, connections, lock, logger=None):
		super(ConnectionThread, self).__init__()
		self.host=host
		self.port=port
		self.connections=connections
		self.lock=lock
		self.logger=logger
		
		self.logger.info("Starting attempting to conenct to %s:%d" % (host,int(port)))
		
		#set as a daemon thread so automaticly gets cleaned up
		self.daemon=True
		
	def run(self):
		self.logger.info("Connection attempt started for %s:%d" % (self.host,self.port))
		sock=socket.socket()
		while True:
			try:
				sock.connect((self.host, self.port))
			except:
				self.logger.debug("Connection attempt to %s:%d failed" % (self.host,self.port))
				sleep(10)
			else:
				with self.lock:
					self.logger.info("Connected to %s:%d" % (self.host,self.port))
					self.connections[(self.host,self.port)]=sock
					break
	
	def __del__(self):
		self.logger.info("Destroying connector for %s:%d" % (self.host, int(self.port)))

class ServerThread(threading.Thread):
	"""Manages incoming connection requests, passing received messages to notify_function"""
	def __init__(self, notify_function, port, logger=None):
		self.notify = notify_function
		if logger:
			self.logger = logger
			self.logger.info("Adopted passed in logger for %s" % __name__)
			print(self.logger.getEffectiveLevel())
		else:
			self.logger = logging.getLogger(__name__)
			self.logger.warning("Created logger for %s" % __name__)
		self.logger.info("ServerThread starting...")
		self.socket=socket.socket()
		self.socket.bind((socket.gethostname(),port))
		
			
	def run(self):
		while True:
			newConn=self.socket.accept()
			
	
	def __del__(self):
		pass
		
if __name__=="__main__":
	logging.basicConfig(level=logging.DEBUG)
	logger = logging.getLogger("Test")
	logger.setLevel(logging.DEBUG)
	trans = ConfiguredTransport((('localhost','6543'),('localhost','7543')),logger=logger)
	
	#Hack to keep running a non-daemon thread
	from time import sleep
	while True:
		sleep(120)
