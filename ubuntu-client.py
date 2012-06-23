#!/usr/bin/env python

import socket
import pynotify
import libnotifymultiplex

def imageConvert(text):
    text=text.lower()
    if text=='im':
        return 'notification-message-im'
    return text

pynotify.init("notify-multiplexer")


sock = libnotifymultiplex.NotifyMultiplexReciever()
sock.connect('hawking.pressers.name', 9012)

while True:
    data = sock.recv()
    if data!=False:
        n = pynotify.Notification(data['title'],data['text'],imageConvert(data['image']))
        n.set_hint_string("x-canonical-append","true")
        n.show()
