#!/usr/bin/env python

import socket, sys, threading, Queue
from re import split, sub

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
            raw = self.sock.recv(4096)
            self.queue.put(raw)

class singleConnSender(threading.Thread):
    def __init__(self,socket,message):
        threading.Thread.__init__(self)
        #self.daemon = True
        self.socket = socket
        self.message = message
    
    def run(self):
        #try:
        self.socket.sendall(self.message)
        #except Exception:
         #   clientsLock.acquire()
          #  clients.remove(self.socket)
           # clientsLock.release()

class singleConnPing(threading.Thread):
    def __init__(self, socket):
        threading.Thread.__init__(self)
        self.socket = socket
        self.daemon = True
        self.uid = None
    
    def run(self):
        while True:
            read = self.socket.recv(1024).strip()
            if read.upper()[:4] == "PING":
                #print "Ping!"
                self.socket.sendall("PONG\0\0\0\0\n")
            if read.upper()[:4] == "UID":
                self.uid = read[4:]

class allConnsSender(threading.Thread):
    def __init__(self,queue,connsList):
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue = queue
        self.conns = connsList
    
    def run(self):
        while True:
            message = queue.get()
            print sub("\0", "!", message)
            for con in self.conns:
                sendT = singleConnSender(con, message)
                sendT.start()

#set up defaults
addr = ('0.0.0.0', 9012)
if (len(sys.argv)>1):
    addr = sys.argv[1]

#lets start by setting up our server socket
mainSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
mainSock.bind(addr)
mainSock.listen(1)

clientsLock = threading.Lock()
clients=[]
queue = Queue.Queue()

acs = allConnsSender(queue, clients)
#acs.daemon=True
acs.start()

ll = localListener(queue)
#ll.daemon=True
ll.start()

while True:
    (sock, addr)=mainSock.accept()
    clientsLock.acquire()
    #clients.append(sock)
    scp = singleConnPing(sock)
    scp.start()
    clientsLock.release()