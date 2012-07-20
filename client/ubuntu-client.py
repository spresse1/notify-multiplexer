#!/usr/bin/env python

import socket
import pynotify
import libnotifymultiplex.libnotifymultiplex as libnotifymultiplex

def imageConvert(text):
    text=text.lower()
    if text=='im':
        return 'notification-message-im'
    return text

pynotify.init("notify-multiplexer")

conf = "/etc/notify-multiplexer/notify-multiplexer.conf"

if (len(sys.argv)>1):
    conf = sys.argv[1]

sock = libnotifymultiplex.NotifyMultiplexReciever(conf)

while True:
    data = sock.recv()
    if data!=None:
        n = pynotify.Notification(data['title'],data['text'],imageConvert(data['image']))
        n.set_hint_string("x-canonical-append","true")
        n.show()
