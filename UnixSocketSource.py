import BaseSource, socket, threading, logging

class ConnectionHandler(threading.Thread):
	
	def __init__(self, socket, server):
		super(ConnectionHandler, self).__init__()
		self.socket = socket
		self.logger = logging.getLogger(__name__)
		#self.logger.setLevel(logging.DEBUG)
		self.server = server
		self.daemon=True
		
	
	def run(self):
		packet = ""
		while True:
			# Packet format:
			# length: int\n #this line not counted in length
			# key: value\n
			# ...
			# data-length: int\n
			# data:blob\n
			# \n illegal in all except data, data-length must appear before 
			recvd = self.socket.recv(4096).decode("UTF-8")
			if len(recvd)==0:
				break
			packet += recvd
			self.logger.debug("Packet: %s" % packet)
			while len(packet)>0:
				self.logger.debug("Packet: %s" % packet)
				length = int(packet.split("\n", 1)[0][7:].strip()) #from 8 to \n
				if not '\n' in packet:
					break
				packet = packet.split('\n',1)[1] # cut off length term
				self.logger.debug("Got message of length %d" % length)
				if length > len(packet):
					self.logger.debug("Not enough data, waiting")
					break
				tpacket = packet[:length]
				packet = packet[length:]
				
				parsed = {}
				category = None
				
				while len(tpacket.strip())>0:
					self.logger.debug("tpacket='%s'" % tpacket)
					(key, remainder) = tpacket.split(':',1)
					if key is "data":
						value=remainder[:parsed['data-length']]
						tpacket = remainder[parsed['data-length']+1:]
						self.logger.debug("Got data.")
						parsed[key] = value
					else:
						(value, tpacket) = remainder.split('\n',1)
						if key is 'category':
							self.logger.debug("Category: %s" % value)
							category = value.strip()
						else:
							self.logger.debug("key %s: %s" % (key, value))
							parsed[key] = value.strip()
				self.server.send(category, parsed)
					
				

class UnixSocketSource(BaseSource.BaseSource):
	import logging 
	conns = []

	def __init__(self, server):
		super(UnixSocketSource, self).__init__()
		self.server = server
		self.socket = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
		self.socket.bind("\0notify-multiplexer")
		self.socket.listen(2)
		self.logging.warn("Initialized")
		print("init")

	def run(self):
		while True:
			handler = ConnectionHandler(self.socket.accept()[0], self.server)
			handler.start()
			self.conns.append(handler)
