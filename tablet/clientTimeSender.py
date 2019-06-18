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
import random

def sendMessage(socket,strMessage):
    #send the message in parameter
    sendTime = time.time()
    socket.sendall(strMessage + "#")
    logging.info("Sent: " + strMessage + " at " + str(sendTime))


def main():
    #example of client in python
    #connectin to the server and receving the messages
    strLogFile = "logs/client-timeSender.log"
    logging.basicConfig(filename=strLogFile, 
                        level=logging.DEBUG, 
                        format='%(levelname)s %(asctime)-15s %(threadName)s %(message)s (%(module)s.%(lineno)d)',
                        datefmt='%H.%M.%S',
                        filemode='w')
    logFormatter = lf.LogFormatter(strLogFile,level=lf.INFO)
    logFormatter.start()

    logging.info("start the test for time measure (send)")

    ip   = "127.0.0.1"
    if len(sys.argv) == 2:
        ip = sys.argv[1]
    port = 1111

    logging.info("Attempt to connect to: " + ip + ":" + str(port))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server_address = (ip, port)
    sock.connect(server_address) 
    sock.settimeout(1)

    logging.info("register timeSend")
    sendMessage(sock,"register:timeSend")

    try:
        while True:
            logging.info("send call")
            sendMessage(sock,"call:tablet.timeReceiver.recv|" + str(random.random()))
            time.sleep(5)

    except KeyboardInterrupt:
        global runningReading
        logging.info("Stop the client")
        sendMessage(sock,"exit")
        sock.close()
        logFormatter.stopReadingLogs()


if __name__ == "__main__":
    main()
