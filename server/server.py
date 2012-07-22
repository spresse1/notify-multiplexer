#!/usr/bin/env python3

import socket, sys, threading, queue, configparser
from re import split, sub, match
from time import sleep
import ssl, logging

class SingleMessageSocketWrapper:
    def __init__(self, socket):
        self.socket = socket
        self.recvBuffer = ""
        
    def recv(self):
        logging.debug("called recv")
        while (match("(.*?[\0]{2,})", self.recvBuffer) is None):
            #logging.debug("Match was... %s" %
            #              (match("(.*?[\0]{2,})", self.recvBuffer)))
            read = self.socket.recv(1024)
            if len(read)>0:
                self.recvBuffer = self.recvBuffer + read.decode('UTF-8')
            #logging.debug("recvBuffer now is %s" %
            #              (sub("\0","!",self.recvBuffer)))
        logging.debug("Busy(ish) wait done")
        msg = match("(.*?[\0]{2,})", self.recvBuffer).group(0)
        logging.debug("Message is %s" % (sub("\0","!",msg)))
        logging.debug("recvBuffer was %s" % (sub("\0","!",self.recvBuffer)))
        self.recvBuffer = self.recvBuffer[len(msg):]
        logging.debug("recvBuffer now is %s" % (sub("\0","!",self.recvBuffer)))
        return msg
    #print "Using delimited recv"
    #peek = msocket.recv(1024,socket.MSG_PEEK)
    #msg = match("(.*?[\0]{2,})", peek)
    #print('peek is %s' % (sub("\0","!",peek)))
    #if msg is not None:
        #print msg.group(0)
        #print 'msg is {0}'.format(sub("\0","!",msg.group(0)))
        #this ought to pull exactly the length of the first message....
    #    return msocket.recv(len(msg.group(0)))
    #return msocket.recv(1024)
    
    def updateSocket(self, socket):
        self.socket = socket

class localListener(threading.Thread):
    def __init__(self,queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.sock = socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
        self.sock.bind("\0notify-multiplexer")
        self.daemon = True
    
    def run(self):
        #self.sock.listen(1)
        while True:
            #we dont use delimited recv becasue these dont get processed
            raw = self.sock.recv(4096)
            logging.info("Got message: %s" % (sub("\0", "!", str(raw))))
            self.queue.put(raw.decode('UTF-8'))

class singleConnSender(threading.Thread):
    def __init__(self,socket,queue, uid=None):
        threading.Thread.__init__(self)
        self.uid = uid
        self.daemon = True
        self.socket = socket
        self.queue = queue
    
    def run(self):
        while True:
            try:
                if len(self.queue)>0:
                    logging.debug("%s: There is something in the send queue!" %
                                  (self.uid))
                    self.socket.sendall(bytes(self.queue[0],'UTF-8'))
                    if self.uid is not None:
                        logging.debug(self.uid + ": Successfully sent the \
                                      message %s" % (sub("\0", "!",
                                                         self.queue.pop(0)))
                        )
                else:
                    sleep(1)
            except:
                sleep(1) #nothing to do, we want to retry sending this one
            
    def updateSocket(self, socket):
        self.socket = socket

class singleConnManager(threading.Thread):
    def __init__(self, socket, uid):
        threading.Thread.__init__(self)
        self.socket = socket
        self.bufferedSocket = SingleMessageSocketWrapper(self.socket)
        self.daemon = True
        self.uid = uid
        self.queue = []
        self.socketQueue = []
        self.sendT = singleConnSender(self.socket, self.queue, uid=self.uid)
        self.sendT.start()
    
    def run(self):
        while True:
            read = self.bufferedSocket.recv().strip()
            if read.upper()[:4] == "PING":
                logging.debug("{0}: Ping!".format(self.uid))
                self.socket.sendall(bytes("PONG\0\0\0\0\n",'UTF-8'))
                logging.debug("%s: Sent PONG" % (self.uid))
            if read.upper()[:4] == "UID":
                logging.info("Unreq'd UID: " + read[4:])
                self.uid = read[4:]
    
    def send(self, message):
        logging.debug("%s: singleConnManager recieved send()" % self.uid)
        self.queue.append(message)
        
    def updateSocket(self, socket):
        logging.debug("%s: Updating socket to %s" % (self.uid, repr(socket)))
        self.socket = socket
        self.sendT.updateSocket(socket)
        self.bufferedSocket.updateSocket(socket)
        logging.info("%s: Socket updated" % (self.uid))

class allConnsSender(threading.Thread):
    def __init__(self,queue,connsList):
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue = queue
        self.conns = connsList
    
    def run(self):
        while True:
            message = queue.get()
            logging.info("Main server recieved: %s" % (sub("\0", "!",
                                                       message)))
            for con in self.conns:
                con.send(message)

class setupSecureSocket(threading.Thread):
    """
    Wraps openssl's initalization procedure, since openssl is dumb and
    terminates the process"""
    def __init__(self, socket):
        threading.Thread.__init__(self)
        self.socket = socket
    
    def run(self):
        try:
            sock = context.wrap_socket(self.socket,
                           server_side=True,
                           )
            self.bufferedSocket = SingleMessageSocketWrapper(sock)
        except Exception as e:
            logging.info("Couldnt start ssl socket: %s" % (e.strerror))
            self.socket.close()
            exit(4)
        logging.debug("set up a new secure socket")
        clientsLock.acquire()
        logging.debug("Waiting on UID...")
        read = self.bufferedSocket.recv().strip()
        logging.debug("Got a message: %s" % (read))
        if read.upper()[:4] == "UID:":
            uid = read[4:]
            found = False
            for client in clients:
                #print "Client UID is " + client.uid
                if client.uid==uid:
                    logging.info("Reconnected UID: " + uid)
                    client.updateSocket(sock)
                    found=True
            if found==False:
                logging.info("New socket UID not found!: " + uid)
                scp = singleConnManager(sock, uid)
                scp.start()
                clients.append(scp)
        else:
            #.. noncompliant...
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        clientsLock.release()

def fetchConfig(config,section,name, default=None):
    try:
        return config[section][name]
    except KeyError:
        return default

#input args:
# [1] config file, defaults to /etc/notify-multiplexer/notify-multiplexer.conf

conf = "/etc/notify-multiplexer/notify-multiplexer.conf"

for sys.argv[1:] as arg:
    if arg!="--debug":
        conf = arg
    else:
        logging.basicConfig(level=logging.DEBUG)
        logging.info("Logging enabled")

#lets deal with config files
config = configparser.SafeConfigParser()
logging.info("using config file %s" % (conf))
try:
    config.read(conf)
except IOError as e:
    logging.fatal("Issues loading config file: " + conf + ": " + repr(e.strerror) +
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
queue = queue.Queue()

acs = allConnsSender(queue, clients)
#acs.daemon=True
acs.start()

ll = localListener(queue)
#ll.daemon=True
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
        setup.start()
        
except KeyboardInterrupt:
    mainSock.shutdown(socket.SHUT_RDWR)
    mainSock.close()
