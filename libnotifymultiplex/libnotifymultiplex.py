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

def send(subject, text, image):
    try:
        sock = socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
        sock.connect("\0notify-multiplexer")
        sock.send('{0}\0{1}\0{2}\0\0'.format(subject, text, image))
    except:
        return False
    return True

class NotifyMultiplexReciever:
    
    def __init__(self, host, port, timeout=60, pingOnConnect=False,
                    conffile="/etc/notify-multiplexer/notify-multiplexer.conf"):
        self.partial=""
        self.msgQueue = queue.Queue()
        self.conMan = self._connManager(host, port, self.msgQueue, timeout,
                                        pingOnConnect)
        self.conMan.start()
        try:
            self.conf = open(conffile)
        except (IOError) as e:
            logging.fatal(("Couldn't find your configuration file (%s)." %
                           (conffile)))
            raise e
        logging.info("Debugging on; initalized")
        
    def _toDict(self, data):
        pparts = re.split("\0", data[:-2])
        try:
            return {'title': pparts[0], 'text': pparts[1], 'image': pparts[2] }
        except KeyError:
            #mlformed message
            return False
    
    class _connManager(threading.Thread):
        
        def __init__(self, host, port, queue, timeout=60, pingOnConnect=False,
                     conffile="/etc/notify-multiplexer/notify-multiplexer.conf"):
            threading.Thread.__init__(self)
            self.host = host
            self.port = port
            self.uid = get_mac()
            self.connected = False
            self.pingWait = False
            self.daemon = True
            self.timeout = timeout
            self.queue = queue
            self.config = configparser.SafeConfigParser()
            
            self.pingOnConnect = pingOnConnect
            
            #read config into object
            try:
                self.config.read(conffile)
            except IOError as e:
                logging.fatal("Issues loading config file: " + conf + ": " +
                              repr(e.strerror) + ", bailing.")
                exit(1)
            
            self.context = self.makeSSLContext()
            
            logging.info("Initalized")
        
        def makeSSLContext(self):
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            
            sslcontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            rootdir=fetchConfig(self.config, "general", "rootdir", "/etc/notify-multiplexer/")
            logging.info("rootdir is: %s" % (repr(rootdir)))
            keyfile=fetchConfig(self.config, "client", "pubkey", None)
            logging.info("pubkey is: %s" % (rootdir + str(keyfile)))
            certfile=fetchConfig(self.config, "client", "privkey", None)
            logging.info("privkey is: %s" % (rootdir + str(certfile)))
            cafile=rootdir + fetchConfig(self.config, "general", "cacertificate",
                               "ca.crt")
            logging.info("CA Cert is: %s" % (repr(cafile)))
            
            if (keyfile is None):
                logging.fatal("You must set the pubkey option in the [client] \
section of %s" % (conf))
                raise NotifyMultiplexReciever.ConfigurationError("You must set \
the pubkey option in the [client] section of %s" % (conf))
            keyfile = rootdir + keyfile
            if (certfile is None):
                logging.fatal("You must set the privkey option in the [client] \
section of %s" % (conf))
                raise NotifyMultiplexReciever.ConfigurationError("You must set \
the privkey option in the [client] section of %s" % (conf))
            certfile = rootdir + certfile
            
            try:
                context.load_cert_chain(keyfile=keyfile, certfile=certfile)
            except (IOError) as e:
                if e.errno==2:
                    if e.filename is not None:
                        logging.fatal("Couldnt find the file %s." % (e.filename))
                    else:
                        logging.fatal("Couldnt find the client keys.  Youve set \
    them to %s and %s. If you need to generate them, use the make_certs.sh script. \
    If you have already generated them under a different name, you need to set the \
    pubkey and privkey options in the [client] section of %s" %
                        ( keyfile, certfile, conf ))
                else:
                    logging.fatal(e.strerror)
            
            try:
                context.load_verify_locations(cafile)
            except (IOError) as e:
                if e.errno==2:
                    if e.filename is not None:
                        logging.fatal("Couldnt find the file %s." % (e.filename))
                    else:
                        logging.fatal("Couldnt find the certificate authority file. \
    You've configured it to be %s.  If you have named it something different, \
    you'll have to set the cacert option in the [general] section of %s" %
                        ( cafile, conf ))
                else:
                    logging.fatal(e.strerror)
                raise NotifyMultiplexReciever.ConfigurationError("You must set the \
    cacart option in %s" % (conf))
            
            context.verify_mode = ssl.CERT_REQUIRED
            
            return context
        
        def connect(self):
            inSecSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.sock = self.context.wrap_socket(inSecSock)
            self.bufferedSocket = NotifyMultiplexReciever.SingleMessageSocketWrapper(self.sock)
            logging.debug("connecting...")
            try:
                self.sock.connect((self.host, self.port))
                if self.pingOnConnect:
                    logging.debug("Sending initial UID+PING...")
                    self.sock.sendall(bytes("UID:%d\0\0PING\0\0\0\0" %
                                            (self.uid), 'UTF-8'))
                else:
                    logging.debug("Sending initial UID...")
                    self.sock.sendall(bytes("UID:%d\0\0" %
                                            (self.uid), 'UTF-8'))
                logging.debug("Sent UID (double-delimited)" + str(self.uid))
                self.connected = True
                logging.debug("connected")
            except socket.error:
                logging.warn("Failed to (re)connect!")
                sleep(self.timeout)
            except Exception as e:
                logging.error("Error connecting: %s" % (repr(e)))
            logging.info("Connected!")
        
        def run(self):
            pingwait=False
            self.connect()
            while True:
                reads = select.select([self.sock], [],[], self.timeout)[0]
                logging.debug("select got something, or timed out")
                if len(reads)>0:
                    logging.debug("got something")
                    pingwait=False
                    try:
                        data = self.sock.recv(1024).decode('UTF-8')
                        #data = self.bufferedSocket.recv()
                        logging.debug("Socket got: %s" %
                                  (sub("\0", "!", data)))
                    except IOError as e:
                        logging.debug("Got IOError: %s" % (repr(e)))
                        if e.errno==107:
                            self.connect()
                        data=""
                    except Exception as e:
                        logging.debug("Failed to recieve data, reconnecting: %s"
                                      % (repr(e)))
                        data=""
                    #logging.debug("Length of recieved string is: %s" % (ord(data)))
                    #if (len(data)==0):
                        #FUCK OpenSSL - It always returns as if theres something
                        #to read, therefore, we fake it...
                    #    logging.debug("Got zero length string, ignoring")
                    #    sleep(1)
                    #    continue
                    logging.debug("No exceptions...")
                    matches = re.match("(.*?[\0]{2,})",
                                               data)
                    logging.debug("Matches is: %s" % ((matches)))
                    if matches is not None:
                        logging.debug("Matches is non-None")
                        for packet in matches.groups():
                            if (packet[:4]!="PONG"):
                                #insert into queue
                                logging.debug("Dropping %s into queue" %
                                          (packet))
                                #oh fuckers.  Lets split messages...
                                self.queue.put(packet)
                            if (packet==""):
                                self.connect()
                else:
                    logging.debug("nope, just a timeout")
                    if pingwait:
                        self.connect()
                    #need to wrap this in a try
                    try:
                        self.sock.sendall(bytes("PING\0\0\0\0", 'UTF-8'))
                    except (Exception) as e:
                        #this is a fallthrough case and we'll reconnect the next time anyway
                        logging.debug("Socket sending failed!: %s" %
                                      (repr(e)))
                    logging.debug("Ping!")
                    pingwait=True
    
    def recv(self):
        data=""
        if re.match('[^\0]*\0[^\0]*\0[^\0]*\0\0',self.partial) is None:
            data = None
            while data is None:
                #ugh, busywait.
                try:
                    data = self.msgQueue.get(False)
                except queue.Empty:
                    sleep(1)
        logging.debug("Data got is: %s" % (re.sub("\0","1",self.partial+data)))
        packets = re.findall('[^\0]*\0[^\0]*\0[^\0]*\0\0',self.partial+data)
        logging.debug("Got packet data: %s" % (repr(packets)))
        self.partial = ''.join(packets[1:])
        if len(packets)>0:
            return self._toDict(packets[0])
        
    class ConfigurationError(Exception):
        def __init__(self, msg):
            self.msg = msg
        def __str__(self):
            return repr(self.msg)
            
    class SingleMessageSocketWrapper:
        def __init__(self, socket):
            self.socket = socket
            self.recvBuffer = ""
            
        def recv(self):
            logging.debug("called recv")
            while (re.match("(.*?[\0]{2,})", self.recvBuffer) is None):
                read = self.socket.recv(1024)
                logging.debug("Recv got: %s" % (read))
                if len(read)>0:
                    self.recvBuffer = self.recvBuffer + read.decode('UTF-8')
            logging.debug("Busy(ish) wait done")
            msg = re.match("(.*?[\0]{2,})", self.recvBuffer).group(0)
            logging.debug("Message is %s" % (sub("\0","!",msg)))
            logging.debug("recvBuffer was %s" % (sub("\0","!",self.recvBuffer)))
            self.recvBuffer = self.recvBuffer[len(msg):]
            logging.debug("recvBuffer now is %s" %
                          (sub("\0","!",self.recvBuffer)))
            return msg
        
        def updateSocket(self, socket):
            self.socket = socket

if __name__ == '__main__':
    #lets run some unit tests
    """sock = socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
    sock.bind("\0notify-multiplexer")
    send("Test","Test1","TestImage")
    read = sock.recv(1024)
    if read=="Test\0Test1\0TestImage\0\0":
        print "Test 1: Passed"
    else:
        print "Test 1: Failed"
    
    n = NotifyMultiplexReciever()
    if (n._toTuple(read)==("Test","Test1","TestImage")):
        print "Test 2: Passed"
    else:
        print "Test 2: Failed"""
    import socket
    
    conf = "/etc/notify-multiplexer/notify-multiplexer.conf"

    if (len(sys.argv)>1):
        conf = sys.argv[1]
    
    logging.basicConfig(level=logging.DEBUG)

    sock = NotifyMultiplexReciever('hawking.pressers.name', 9013, conffile=conf,
                                   timeout=1)
    
    data = True
    while data is not False:
        data = sock.recv()
        if data!=False:
            logging.debug("Got data (outer test loop): %s" % (data))