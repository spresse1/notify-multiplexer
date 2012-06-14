#!/usr/bin/env python

import socket, sys, threading, Queue
from re import split

class message:
    title=None
    text=None
    
    def __init__(self,title, text):
        self.title = title.strip()
        self.text = text.strip()

class localListener(threading.Thread):
    def __init__(self,queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.sock = socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
        self.sock.bind("\0notify-multiplexer")
    
    def run(self):
        #self.sock.listen(1)
        while True:
            raw = self.sock.recv(4096)
            parts = re.split("\n",raw, maxsplit=1)
            self.queue.add(message(parts[0],parts[1]))

class singleConnSender(threading.Thread):
    def __init__(self,socket,message):
        threading.Thread.__init__(self)
        self.socket = socket
        self.message = message
    
    def run(self):
        socket.sendall(message.title + "\n" + message.text + "\n")

class allConnsSender(threading.Thread):
    def __init__(self,queue,connsList):
        threading.Thread.__init__(self)
        self.queue = queue
        self.conns = connsList
    
    def run(self):
        while True:
            message = queue.get()
            for con in conns:
                sendT = singleConnSender(con, message)
                sendT.start()

#set up defaults
addr = ('0.0.0.0', 9012)
if (len(sys.argv)>1):
    addr = sys.argv[1]

#lets start by setting up our server socket
mainSock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
mainSock.bind(addr)

clients=[]
queue = Queue.Queue()

acs = allConnsSender(queue, clients)
acs.start()

ll = localListener(queue)
ll.start()

while True:
    (sock, addr)=mainSock.accept()
    clients.append(sock)