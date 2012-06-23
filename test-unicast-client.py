#!/usr/bin/env python

import socket

sock = socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
sock.connect("\0notify-multiplexer")
sock.send("ten\0tests\0\0\0wen\0wests\0im\0\0")
#sock.send("twenty\ntests\n")
#sock.send("ten\ntests\n")