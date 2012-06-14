#!/usr/bin/env python

import socket, sys, threading

class message:
    self.title=None
    self.text=None
    
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
        while True:
            

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
                sendT.run()

#set up defaults
addr = '0.0.0.0'
if (len(sys.argv)>1):
    addr = sys.argv[1]

#lets start by setting up our server socket
mainSock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
mainSock.bind(addr)

clients=[]

while True:
    (sock, addr)=mainSock.accept()