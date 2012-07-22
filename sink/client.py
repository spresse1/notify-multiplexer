#!/usr/bin/env python3

import socket, sys
import libnotifymultiplex as libnotifymultiplex

class BadNotifyMethod(Exception):
    def __init__(self,string):
        self.string=string
    def __str__(self):
        return self.string

class __pynotify:
    def __init__(self):
        try:
            import pynotify
        except ImportError:
            raise BadNotifyMethod("pynotify not installed")
        pynotify.init("notify-multiplexer")
    
    def imageConvert(self, text):
        text=text.lower()
        if text=='im':
            return 'notification-message-im'
        return text
    
    def send(self, data):
        n = pynotify.Notification(data['title'],data['text'],imageConvert(data['image']))
        n.set_hint_string("x-canonical-append","true")
        n.show()

class __growl12:
    def __init__(self):
        import subprocess
        try:
            subprocess.call(['growlnotify'])
        except:
            raise BadNotifyMethod("growl not installed")
    
    def imageConvert(self, text):
        text=text.lower()
        if text=='im':
            return 'notification-message-im'
        return text
    
    def send(self, data):
        subprocess.call(['growlnotify','-t',data['title'],'-m',data['text']])

conf = "/etc/notify-multiplexer/notify-multiplexer.conf"

if (len(sys.argv)>1):
    conf = sys.argv[1]

nclass=None
try:
    if nclass is None:
        nclass = __pynotify()
except BadNotifyMethod as e:
    print(e)

try:
    if nclass is None:
        nclass = __growl12()
except BadNotifyMethod as e:
    print(e)
    
if nclass is None:
    print("No suitable notification methods found")
    exit(1)
    
sock = libnotifymultiplex.NotifyMultiplexReciever(conf)
while True:
    data = sock.recv()
    if data!=None:
        nclass.send(data)