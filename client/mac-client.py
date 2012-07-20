#!/usr/bin/env python

import socket
import libnotifymultiplex
import subprocess

def imageConvert(text):
    text=text.lower()
    if text=='im':
        return 'notification-message-im'
    return text

conf = "/etc/notify-multiplexer/notify-multiplexer.conf"

if (len(sys.argv)>1):
    conf = sys.argv[1]

sock = libnotifymultiplex.NotifyMultiplexReciever(conf)

while True:
    data = sock.recv()
    if data!=None:
        subprocess.call(['growlnotify','-t',data['title'],'-m',data['text']])