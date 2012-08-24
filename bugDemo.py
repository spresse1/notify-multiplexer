#!/usr/bin/env python3

import threading
import select
import logging
import sys
import socket, ssl

class client(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.name="Client"
        self.setDaemon(True)
    
    def run(self):
        inSecSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        sock = ssl.wrap_socket(inSecSock,server_side=False)
        sock.connect(("localhost",8888))
        while True:
            (rlist, wlist, xlist) = select.select([sock], [], [])
            logging.info("Read something...")
            print(rlist[0].read(1024))

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.info("Logging enabled")
    client().start()
    try:
        mainSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        mainSock.bind(("localhost", 8888))
        mainSock.listen(1)
    except socket.error as err:
        logging.fatal("Couldnt bind socket!")
        logging.fatal(err)
        exit(2)
    logging.debug("Initalized main socket")
    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    (inSecSock, addr)=mainSock.accept()
    logging.debug("Got a client")
    sock = ssl.wrap_socket(inSecSock,
                       "privateKey.key", "certificate.crt",
                       server_side=True)
    while True:
        logging.info("Ready to read data")
        (reads, writes, other) = select.select([sys.stdin],[],[])
        logging.info("Have some data to read")
        sock.sendall(bytes(sys.stdin.readline(),'UTF-8'))
        logging.info("sent data")