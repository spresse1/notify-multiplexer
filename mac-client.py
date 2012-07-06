#!/usr/bin/env python

import socket
import libnotifymultiplex
import subprocess

def imageConvert(text):
    text=text.lower()
    if text=='im':
        return 'notification-message-im'
    return text

sock = libnotifymultiplex.NotifyMultiplexReciever('hawking.pressers.name', 9012)

while True:
    data = sock.recv()
    if data!=None:
        subprocess.call(['growlnotify','-t',data['title'],'-m',data['text']])