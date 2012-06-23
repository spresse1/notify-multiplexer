#!/usr/bin/env python

import socket, re, threading, select

def send(subject, text, image):
    try:
        sock = socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
        sock.connect("\0notify-multiplexer")
        sock.send('{0}\0{1}\0{2}\0\0'.format(subject, text, image))
    except:
        return False
    return True

class NotifyMultiplexReciever:
    
    def __init__(self):
        self.connected = False
        self.partial=""
    
    def _toDict(self, data):
        pparts = re.split("\0", data[:-2])
        try:
            return {'title': pparts[0], 'text': pparts[1], 'image': pparts[2] }
        except KeyError:
            #mlformed message
            return False
    
    def connect(self, server, port):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        #self.sock.settimeout(1)
        #self.sock.setblocking(True)
        self.server = server
        self.port = port
        try:
            self.sock.connect((server, port))
            self.connected = True
            #self.sock.setblocking(False)
        except socket.error:
            print "Failed to connect to the server!"
            return False
        return True
    
    def _ping(self):
        try:
            self.sock.sendall("PING\0");
        except:
            print "Error sending ping!"
            return False
        try:
            print "_ping"
            rdata = self.recv_timeout(1024)
            if rdata[:4].upper()!="PONG":
                #oops, we pulled in data
                return rdata
        except socket.timeout:
            print "Error reading from server!"
            return False
        return True
    
    def _checkPing(self):
        print "Running _checkPing"
        if self._ping() is False:
            if self.connect(self.server, self.port) is False:
                return False
            print "Successfully reconnected"
        return True
    
    def recv_timeout(self, size, timeout=60):
        print "using timeout recv"
        if not self.connected:
            return None
        self.sock.setblocking(True)
        ready = select.select([self.sock],[],[],timeout)
        print "ready: " + str(ready[0])
        if ready[0]:
            data = self.sock.recv(size)
            if data=="":
                raise socket.timeout()
            return data
        else:
            raise socket.timeout()
    
    def recv(self):
        if not self.connected:
            return False
        data=""
        if re.match('[^\0]*\0[^\0]*\0[^\0]*\0\0',self.partial) is None:
            try:
                print "main loop"
                data = self.recv_timeout(1024)
                if data=="":
                    print "Bombing becasue of null data"
                    return False
            except socket.timeout:
                print "Caught timeout!"
                pingres = self._checkPing()
                if pingres is False:
                    return False
                elif pingres is not True:
                    #ideally this means we got back data not equal to "PONG"
                    data = pingres
#                except:
#                    return False
        #the first is a full packet
        #we assume we got at least one full packet
        print re.sub("\0","1",self.partial+data)
        packets = re.findall('[^\0]*\0[^\0]*\0[^\0]*\0\0',self.partial+data)
        print packets
        self.partial = ''.join(packets[1:])
        if len(packets)>0:
            return self._toDict(packets[0])
        else:
            return self.recv()
        
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
    
    sock = NotifyMultiplexReciever()
    if sock.connect('hawking.pressers.name', 9012) is False:
        exit(1)
    
    data = True
    while data is not False:
        data = sock.recv()
        if data!=False:
            print data