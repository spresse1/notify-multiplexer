#! /usr/bin/env python3

import socket

sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM,0)
sock.connect("\0notify-multiplexer")
sock.sendall(bytes("length: 36\ncategory: test\ndata-length: 0\ndata:\n",'UTF-8'));
sock.close()

print("test sent")

