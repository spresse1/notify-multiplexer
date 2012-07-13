#!/usr/bin/env python

import socket, sys, threading, queue, configparser
from re import split, sub, match
from time import sleep
from ssl import CERT_REQUIRED, wrap_socket

def delimitedRecv(msocket):
    #print "Using delimited recv"
    peek = msocket.recv(1024,socket.MSG_PEEK)
    msg = match("(.*?[\0]{2,})", peek)
    #print 'peek is {0}'.format(sub("\0","!",peek))
    if msg is not None:
        #print msg.group(0)
        #print 'msg is {0}'.format(sub("\0","!",msg.group(0)))
        #this ought to pull exactly the length of the first message....
        return msocket.recv(len(msg.group(0)))
    return msocket.recv(1024)

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
            self.queue.put(raw)

class singleConnSender(threading.Thread):
    def __init__(self,socket,queue, debug=False, uid=None):
        threading.Thread.__init__(self)
        self.debug=debug
        self.uid = uid
        self.daemon = True
        self.socket = socket
        self.queue = queue
    
    def run(self):
        while True:
            try:
                if len(self.queue)>0:
                    self.socket.sendall(self.queue[0])
                    if self.debug and self.uid is not None:
                        print(self.uid + "Successfully sent the message " + sub("\0",
                                                                 "!",
                                                                 self.queue.pop(0)))
                else:
                    sleep(1)
            except:
                sleep(1) #nothing to do, we want to retry sending this one
            
    def updateSocket(self, socket):
        self.socket = socket

class singleConnManager(threading.Thread):
    def __init__(self, socket, uid, debug = False):
        threading.Thread.__init__(self)
        self.socket = socket
        self.daemon = True
        self.debug = debug
        self.uid = uid
        self.queue = []
        self.socketQueue = []
        self.sendT = singleConnSender(self.socket, self.queue, debug=True, uid=self.uid)
        self.sendT.start()
    
    def run(self):
        while True:
            read = delimitedRecv(self.socket).strip()
            if read.upper()[:4] == "PING":
                if self.debug:
                    print("{0}: Ping!".format(self.uid))
                self.socket.sendall("PONG\0\0\0\0\n")
            if read.upper()[:4] == "UID":
                print("Unreq'd UID: " + read[4:])
                self.uid = read[4:]
    
    def send(self, message):
        self.queue.append(message)
        
    def updateSocket(self, socket):
        self.socket = socket
        self.sendT.updateSocket(socket)
        

class allConnsSender(threading.Thread):
    def __init__(self,queue,connsList):
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue = queue
        self.conns = connsList
    
    def run(self):
        while True:
            message = queue.get()
            print(sub("\0", "!", message))
            for con in self.conns:
                con.send(message)

def fetchConfig(config,section,name, default=None):
    try:
        return config.get(section,name).strip()
    except configparser.NoOptionError:
        return default

#set up defaults
addr = ('0.0.0.0', 9012)

#input args:
# [1] config file, defaults to /etc/notify-multiplexer/notify-multiplexer.conf

conf = "/etc/notify-multiplexer/notify-multiplexer.conf"

try:
    conffh = open(conf)
except IOError as e:
    print(e)
    e.printStackTrace()
    exit(1)

if (len(sys.argv)>1):
    conf = sys.argv[1]

#lets deal with config files
config = configparser.SafeConfigParser()

#lets start by setting up our server socket
try:
    mainSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    mainSock.bind(addr)
    mainSock.listen(1)
except socket.error as err:
    print("Couldnt bind socket!")
    print(err)
    exit(2)

clientsLock = threading.Lock()
clients=[]
queue = queue.Queue()

acs = allConnsSender(queue, clients)
#acs.daemon=True
acs.start()

ll = localListener(queue)
#ll.daemon=True
ll.start()

try:
    while True:
        (inSecSock, addr)=mainSock.accept()
        sock = wrap_socket(inSecSock,
                           keyfile=fetchConfig(config, "server", "keyfile", "/etc/notify-multiplexer/server.key"),
                           certfile=fetchConfig(config, "server", "keyfile", "/etc/notify-multiplexer/server.crt"),
                           server_side=True,
                           cert_reqs=CERT_REQUIRED,
                           )
        clientsLock.acquire()
        read = delimitedRecv(sock).strip()
        if read.upper()[:4] == "UID:":
            uid = read[4:]
            found = False
            for client in clients:
                #print "Client UID is " + client.uid
                if client.uid==uid:
                    print("Reconnected UID: " + uid)
                    client.updateSocket(sock)
                    found=True
            if found==False:
                print("New socket UID not found!: " + uid)
                scp = singleConnManager(sock, uid)
                scp.start()
                clients.append(scp)
        else:
            #.. noncompliant...
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        clientsLock.release()
except KeyboardInterrupt:
    mainSock.shutdown(socket.SHUT_RDWR)
    mainSock.close()