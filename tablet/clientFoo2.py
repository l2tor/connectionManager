#!/usr/bin/env python
# coding: utf-8 

import threading
import socket
from threading import Thread
import logging
import re
import time
import log_formatter as lf
import sys

runningReading = True

class Foo:
    def __init__(self):
        pass

    def foo(self,params):
        logging.info("foo method called with: " + params)


def readMessages(sock,aMessages):
    #while 1 loop, feeling aMessages
    while runningReading == True:
        try:
            strReceive = sock.recv(1024)
            strReceive = strReceive.split("#")
            aMessages += strReceive
            time.sleep(1)
        except socket.error, e:
            logging.debug("error on socket: " + str(e))
            pass

def sendMessage(socket,strMessage):
    #send the message in parameter
    socket.sendall(strMessage + "#")
    #time.sleep(0.1)


def main():
    #example of client in python
    #connectin to the server and receving the messages
    strLogFile = "logs/client-foo2.log"
    logging.basicConfig(filename=strLogFile, 
                        level=logging.DEBUG, 
                        format='%(levelname)s %(asctime)-15s %(threadName)s %(message)s (%(module)s.%(lineno)d)',
                        datefmt='%H.%M.%S',
                        filemode='w')
    logFormatter = lf.LogFormatter(strLogFile,level=lf.INFO)
    logFormatter.start()

    logging.info("start foo2")

    ip   = "127.0.0.1"
    if len(sys.argv) == 2:
        ip = sys.argv[1]
    port = 1111

    logging.info("Attempt to connect to: " + ip + ":" + str(port))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server_address = (ip, port)
    sock.connect(server_address) 
    sock.settimeout(1)
    
    aMessages = []
    t = threading.Thread(target=readMessages, args=(sock, aMessages))
    t.start()

    logging.info("register fooTwo")
    sendMessage(sock,"register:fooTwo")

    myFoo = Foo()

    nCpt = 0
    try:
        while True:

            logging.info("send message")
            sendMessage(sock,"call:tablet.fooOne.foo|2.0")

            for strMessage in aMessages:
                if strMessage != "":
                    fields = strMessage.split("|")
                    logging.info("received message from " + str(fields[0])) 
                    method = fields[1]
                    params = fields[2]
                    getattr(myFoo,method)(params)
            del aMessages[:]
            time.sleep(1)

    except KeyboardInterrupt:
        global runningReading
        logging.info("Stop the client")
        sendMessage(sock,"exit")
        runningReading = False
        t.join()
        sock.close()
        logFormatter.stopReadingLogs()


if __name__ == "__main__":
    main()
