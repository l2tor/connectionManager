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
                        level=logging.INFO, 
                        format='%(levelname)s %(asctime)-15s %(threadName)s %(message)s (%(module)s.%(lineno)d)',
                        datefmt='%H.%M.%S',
                        filemode='w')
    logFormatter = lf.LogFormatter(strLogFile,level=lf.DEBUG)
    logFormatter.start()

    logging.info("start the test script of the client")

    ip   = "127.0.0.1"
    if len(sys.argv) == 2:
        ip = sys.argv[1]
    port = 1111

    logging.info("Attempt to connect to: " + ip)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server_address = (ip, 1111)
    sock.connect(server_address) 
    
    aMessages = []
    logging.info("exit without previous registration")
    sendMessage(sock,"exit")
    time.sleep(2)
    sock.close()
    logFormatter.stopReadingLogs()


if __name__ == "__main__":
    main()
