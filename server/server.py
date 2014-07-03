#!/usr/bin/env python3

import socket, sys, threading, queue, configparser, argparse
from re import split, sub, match
from time import sleep
import ssl, logging

class localListener(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.sock = socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind("\0notify-multiplexer")
		self.daemon = True
	
	def run(self):
		while True:
			#we dont use delimited recv becasue these dont get processed
			raw = self.sock.recv(4096)
			logging.info("Got message: %s" % (sub("\0", "!", str(raw))))
			for client in clients:
				logging.debug("Sending to client")
				logging.debug(client)
				client.sendall(raw)

def setupSecureSocket(socket):
	try:
		sock = context.wrap_socket(socket,
					   server_side=True,
					   )
	except Exception as e:
		logging.info("Couldnt start ssl socket: %s" % (e.strerror))
		self.socket.close()
		exit(4)
	logging.debug("set up a new secure socket")
	return sock

def fetchConfig(config,section,name, default=None):
	try:
		return config[section][name]
	except KeyError:
		return default

#input args:
# [1] config file, defaults to /etc/notify-multiplexer/notify-multiplexer.conf

parser = argparse.ArgumentParser(description='Server for notify-multiplexer')
parser.add_argument('conffile', metavar='ConfFile', type=str, nargs=1,
					default="/etc/notify-multiplexer/notify-multiplexer.conf")
parser.add_argument('--debug',
					choices=["debug","info","warning","critical"],
					type=str, default="warning", required=False)
parser.add_argument('--logfile', type=str, required=False)
parser=parser.parse_args()

numeric_level = getattr(logging, parser.debug.upper(), None)
if not isinstance(numeric_level, int):
	raise ValueError('Invalid log level: %s' % parser.debug)
if (parser.logfile is not None):
	logging.basicConfig(level=numeric_level, filename=parser.logfile)
else:
	logging.basicConfig(level=numeric_level, )

#lets deal with config files
config = configparser.SafeConfigParser()
logging.info("using config file %s" % (parser.conffile))
try:
	config.read(parser.conffile)
except IOError as e:
	logging.fatal("Issues loading config file: " + parser.conffile + ": " + repr(e.strerror) +
		  ", bailing.")
	#e.printStackTrace()
	exit(1)

addr = fetchConfig(config, "server", "address", '0.0.0.0')
port = int(fetchConfig(config, "server", "port", 9012))

#lets start by setting up our server socket
try:
	mainSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	mainSock.bind((addr, port))
	mainSock.listen(1)
except socket.error as err:
	logging.fatal("Couldnt bind socket!")
	logging.fatal(err)
	exit(2)
logging.debug("Initalized main socket")

clientsLock = threading.Lock()
clients=[]

#listens on the local socket
ll = localListener()
ll.start()

#set up the SSL context, yay!
context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)

rootdir=fetchConfig(config, "general", "rootdir", "/etc/notify-multiplexer/")
logging.debug("Root dir is %s" % (rootdir))

keyfile=rootdir + fetchConfig(config, "server", "pubkey", "server.key")
certfile=rootdir + fetchConfig(config, "server", "privkey", "server.crt")
cafile=rootdir + fetchConfig(config, "general", "cacertificate", "ca.crt")
try:
	context.load_cert_chain(keyfile=keyfile, certfile=certfile)
except (IOError) as e:
	if e.errno==2:
		if e.filename is not None:
			logging.fatal("Couldnt find the file %s." % (e.filename))
		else:
			logging.fatal("Couldnt find the server keys.  Youve set them to %s and %s. \
If you need to generate them, use the make_certs.sh script.  If you have \
already generated them under a different name, you need to set the pubkey and \
privkey options in the [server] section of  %s" % ( keyfile, certfile, conf ))
	else:
		logging.fatal(e.strerror)
	exit(3)

try:
	context.load_verify_locations(cafile)
except (IOError) as e:
	if e.errno==2:
		if e.filename is not None:
			logging.fatal("Couldnt find the file %s." % (e.filename))
		else:
			logging.fatal("Couldnt find the certificate authority file.  You've \
configured it to be %s.  If you have named it something \
different, you'll have to set the cacert option in the [general] section of \
%s" % ( cafile, conf ))
	else:
		logging.fatal(e.strerror)
	exit(3)

context.verify_mode = ssl.CERT_REQUIRED

logging.info("SSL context initalized, waiting on clients")

try:
	while True:
		(inSecSock, addr)=mainSock.accept()
		logging.debug("Got a client")
		setup = setupSecureSocket(inSecSock)
		clientsLock.acquire()
		logging.debug("Client added to client list")
		logging.debug(setup)
		clients.append(setup)
		clientsLock.release()
		
		
except KeyboardInterrupt:
	mainSock.shutdown(socket.SHUT_RDWR)
	mainSock.close()
