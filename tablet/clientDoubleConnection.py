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

def sendMessage(socket,strMessage):
    #send the message in parameter
    socket.sendall(strMessage + "#")

def main():
    #example of client in python
    #connectin to the server and receving the messages
    strLogFile = "logs/client-test.log"
    logging.basicConfig(filename=strLogFile, 
                        level=logging.DEBUG, 
                        format='%(levelname)s %(asctime)-15s %(threadName)s %(message)s (%(module)s.%(lineno)d)',
                        datefmt='%H.%M.%S',
                        filemode='w')
    logFormatter = lf.LogFormatter(strLogFile,level=lf.INFO)
    logFormatter.start()

    logging.info("start the test script of the client")

    ip   = "127.0.0.1"
    if len(sys.argv) == 2:
        ip = sys.argv[1]
    port = 1111
    server_address = (ip, 1111)

    logging.info("Attempt to connect to: " + ip)
    sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    sock1.connect(server_address) 

    logging.info("register first time")
    sendMessage(sock1,"register:double")
    time.sleep(2)

    logging.info("Attempt to connect to: " + ip)
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    sock2.connect(server_address) 

    logging.info("register second time")
    sendMessage(sock2,"register:double")
    time.sleep(2)

    logging.info("close first connection")
    sendMessage(sock1,"exit")
    time.sleep(2)
    sock1.close()
    time.sleep(2)
    
    logging.info("close second connection")
    sendMessage(sock2,"exit")
    time.sleep(2)
    sock1.close()
    time.sleep(2)


    logFormatter.stopReadingLogs()
    sys.exit()


if __name__ == "__main__":
    main()
