#!/usr/bin/env python

import socket, re, threading, select, Queue
from time import sleep
from uuid import getnode as get_mac

def send(subject, text, image):
    try:
        sock = socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
        sock.connect("\0notify-multiplexer")
        sock.send('{0}\0{1}\0{2}\0\0'.format(subject, text, image))
    except:
        return False
    return True

class NotifyMultiplexReciever:
    
    def __init__(self, host, port, timeout=60, debug=False):
        self.partial=""
        self.msgQueue = Queue.Queue()
        self.conMan = self._connManager(host, port, self.msgQueue, timeout, debug=debug)
        self.conMan.start()
        self.debug = debug
        if self.debug:
            print "Debugging on; initalized"
        
    
    def _toDict(self, data):
        pparts = re.split("\0", data[:-2])
        try:
            return {'title': pparts[0], 'text': pparts[1], 'image': pparts[2] }
        except KeyError:
            #mlformed message
            return False
    
    class _connManager(threading.Thread):
        
        def __init__(self, host, port, queue, timeout=60, debug=False):
            threading.Thread.__init__(self)
            self.host = host
            self.port = port
            self.uid = get_mac()
            self.connected = False
            self.pingWait = False
            self.daemon = True
            self.timeout = timeout
            self.queue = queue
            self.debug = debug
            if self.debug:
                print "Initalized"
        
        def connect(self):
            self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            if self.debug:
                print "connecting..."
            try:
                self.sock.connect((self.host, self.port))
                self.sock.sendall("UID:" + str(self.uid))
                self.connected = True
                if self.debug:
                    print "connected"
            except socket.error:
                if self.debug:
                    print "Failed to (re)connect!"
                sleep(self.timeout)
        
        def run(self):
            pingwait=False
            self.connect()
            while True:
                reads = select.select([self.sock], [],[], self.timeout)[0]
                if self.debug:
                    print "select got something, or timed out"
                if len(reads)>0:
                    if self.debug:
                        print "got something"
                    pingwait=False
                    try:
                        data = self.sock.recv(1024)
                    except:
                        if self.debug:
                            print "Failed to recieve data, reconnecting"
                        data=""
                    if (data[:4]!="PONG"):
                        #insert into queue
                        self.queue.put(data)
                    if (data==""):
                        self.connect()
                else:
                    if self.debug:
                        print "nope, just a timeout"
                    if pingwait:
                        self.connect()
                    #need to wrap this in a try
                    try:
                        self.sock.sendall("PING\0\0\0\0")
                    except:
                        #this is a fallthrough case and we'll reconnect the next time anyway
                        if self.debug:
                            print "Socket sending failed!"
                    if self.debug:
                        print "Ping!"
                    pingwait=True
    
    def recv(self):
        data=""
        if re.match('[^\0]*\0[^\0]*\0[^\0]*\0\0',self.partial) is None:
            data = None
            while data is None:
                #ugh, busywait.
                try:
                    data = self.msgQueue.get(False)
                except Queue.Empty:
                    sleep(1)
        if self.debug:
            print re.sub("\0","1",self.partial+data)
        packets = re.findall('[^\0]*\0[^\0]*\0[^\0]*\0\0',self.partial+data)
        if self.debug:
            print packets
        self.partial = ''.join(packets[1:])
        if len(packets)>0:
            return self._toDict(packets[0])
        
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
    
    sock = NotifyMultiplexReciever('hawking.pressers.name', 9012)
    
    data = True
    while data is not False:
        data = sock.recv()
        if data!=False:
            print data