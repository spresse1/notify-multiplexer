#!/usr/bin/env python3

import socket, re, threading, select, queue
import ssl, logging, sys, configparser
from time import sleep
from uuid import getnode as get_mac
from re import sub

def fetchConfig(config,section,name, default=None):
	try:
		return config[section][name]
	except KeyError:
		return default

def makeSSLContext(config,conffile):
	context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
			
	sslcontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
	rootdir=fetchConfig(config, "general", "rootdir", "/etc/notify-multiplexer/")
	logging.info("rootdir is: %s" % (repr(rootdir)))
	keyfile=fetchConfig(config, "client", "privkey", None)
	logging.info("pubkey is: %s" % (rootdir + str(keyfile)))
	certfile=fetchConfig(config, "client", "pubkey", None)
	logging.info("privkey is: %s" % (rootdir + str(certfile)))
	cafile=rootdir + fetchConfig(config, "general", "cacertificate",
					   "ca.crt")
	logging.info("CA Cert is: %s" % (repr(cafile)))
			
	if (keyfile is None):
		logging.fatal("You must set the pubkey option in the [client] \
section of %s" % (conf))
		raise NotifyMultiplexReciever.ConfigurationError("You must set \
the pubkey option in the [client] section of %s" % (conffile))
	keyfile = rootdir + keyfile
	if (certfile is None):
		logging.fatal("You must set the privkey option in the [client] \
section of %s" % (conf))
		raise NotifyMultiplexReciever.ConfigurationError("You must set \
the privkey option in the [client] section of %s" % (conffile))
	certfile = rootdir + certfile
			
	try:
		context.load_cert_chain(keyfile=keyfile, certfile=certfile)
	except (IOError) as e:
		if e.errno==2:
			if e.filename is not None:
				logging.fatal("Couldnt find the file %s." % (e.filename))
			else:
				logging.fatal("Couldnt find the client keys.  Youve set\
 them to %s and %s. If you need to generate them, use the make_certs.sh script.\
 If you have already generated them under a different name, you need to set the\
 pubkey and privkey options in the [client] section of %s" %
				( keyfile, certfile, conffile ))
		else:
			logging.fatal(e.strerror)
			
	try:
		context.load_verify_locations(cafile)
	except (IOError) as e:
		if e.errno==2:
			if e.filename is not None:
				logging.fatal("Couldnt find the file %s." % (e.filename))
			else:
				logging.fatal("Couldnt find the certificate authority \
file. You've configured it to be %s.  If you have named it something different,\
 you'll have to set the cacert option in the [general] section of %s" %
				( cafile, conffile ))
		else:
			logging.fatal(e.strerror)
		raise NotifyMultiplexReciever.ConfigurationError("You must set \
the cacart option in %s" % (conffile))
			
	context.verify_mode = ssl.CERT_REQUIRED
			
	return context
		
if __name__=='__main__':
	conffile="/etc/notify-multiplexer/notify-multiplexer.conf"
	partial=""
	conf = configparser.ConfigParser()
	try:
		conf.read(conffile)
	except (IOError) as e:
		logging.fatal(("Couldn't find your configuration file (%s)." %
			   (conffile)))
		raise e
	host = fetchConfig(conf, "client", "server", None)
	port = int(fetchConfig(conf, "client", "port", 9012))
	timeout = int(fetchConfig(conf, "client", "timeout", 60))
	if host is None:
		raise NotifyMultiplexReciever.ConfigurationError("For proper client\
use, you MUST set the server configuration option in the [client] section of %s"
			% (conffile))
	logging.basicConfig(level=logging.DEBUG)
	logging.info("Debugging on; initalized")
		
	#read config into object
	try:
		conf.read(conffile)
	except IOError as e:
		logging.fatal("Issues loading config file: " + conf + ": " +
					  repr(e.strerror) + ", bailing.")
		exit(1)
	
	logging.info("Initalized")
		
	inSecSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	sock = makeSSLContext(conf,conffile).wrap_socket(inSecSock)
	logging.debug("connecting...")
	try:
		sock.connect((host, port))
	except socket.error:
		logging.warn("Failed to (re)connect!")
		sleep(timeout)
	except Exception as e:
		logging.error("Error connecting: %s" % (repr(e)))
	logging.info("Connected!")
		
	while True:
		reads = select.select([sock], [],[], timeout)[0]
		logging.debug("select got something, or timed out")
		if len(reads)>0:
			logging.debug("got something")
			try:
				data = sock.recv(1024).decode('UTF-8')
				#data = bufferedSocket.recv()
				logging.debug("Socket got: %s" %
						  (sub("\0", "!", data)))
			except IOError as e:
				logging.debug("Got IOError: %s" % (repr(e)))
				data=""
			except Exception as e:
				logging.debug("Failed to recieve data, reconnecting: %s"
					  % (repr(e)))
				data=""
	
