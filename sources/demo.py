#! /usr/bin/env python3

import socket

sock = socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM,0)
sock.connect("\0notify-multiplexer")
sock.sendall(bytes("Test\0test message\0im\0",'UTF-8'));
sock.close()

print("test sent")
