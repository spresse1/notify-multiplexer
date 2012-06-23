#!/usr/bin/env python

import socket, re
import pynotify

pynotify.init("notify-multiplexer")

while True:
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.connect(('hawking.pressers.name', 9012))
    
    while True:
        data = sock.recv(1024)
        #print data
        if data!="":
            dparts = re.split("\0",data)
            print '0: ' + dparts[0]
            print '1: ' + dparts[1]
            n = pynotify.Notification(dparts[0],dparts[1],
                                      "notification-message-im")
            n.set_hint_string("x-canonical-append","true")
            n.show()
