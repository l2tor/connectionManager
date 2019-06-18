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

class TimeReceiver:
    def __init__(self):
        pass

    def recv(self,params):
        logging.info("reception at " + str(time.time()) + " of: " + params)

def sendMessage(socket,strMessage):
    #send the message in parameter
    socket.sendall(strMessage + "#")

def readMessages(sock,aMessages):
    #while 1 loop, feeling aMessages
    global runningReading
    remainingString = ""

    while runningReading == True:
        rawString = ""
        completeString = remainingString #Get what was left of the last reception
        remainingString = ""

        try:
            while not "#" in completeString:
                rawString = sock.recv(1)
                if rawString == "":
                    logging.info("Empty string received. Ask to the server to stop")
                    runningReading = False
                    break
                else:
                    completeString += rawString

        except socket.error, e:
            logging.debug("error on socket: " + str(e))
            pass

        if completeString != "":
            if completeString[-1] != "#":
                index = completeString.rfind("#")
                aMessages += completeString[:index].split("#")
                remainingString = completeString[index+1:]
            else:
                aMessages += completeString.split("#")

def main():
    #example of client in python
    #connectin to the server and receving the messages
    strLogFile = "logs/client-timeReceiver.log"
    logging.basicConfig(filename=strLogFile, 
                        level=logging.DEBUG, 
                        format='%(levelname)s %(asctime)-15s %(threadName)s %(message)s (%(module)s.%(lineno)d)',
                        datefmt='%H.%M.%S',
                        filemode='w')
    logFormatter = lf.LogFormatter(strLogFile,level=lf.INFO)
    logFormatter.start()

    logging.info("start the test for time measure (reception)")

    ip   = "127.0.0.1"
    if len(sys.argv) == 2:
        ip = sys.argv[1]
    port = 1111

    logging.info("Attempt to connect to: " + ip + ":" + str(port))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server_address = (ip, port)
    sock.connect(server_address) 
    
    aMessages = []
    t = threading.Thread(target=readMessages, args=(sock, aMessages))
    t.start()

    logging.info("register timeReceiver")
    sendMessage(sock,"register:timeReceiver")

    myReceiver = TimeReceiver()

    nCpt = 0
    try:
        while True:
            for strMessage in aMessages:
                if strMessage != "":
                    fields = strMessage.split("|")
                    method = fields[1]
                    params = fields[2]
                    getattr(myReceiver,method)(params)
            del aMessages[:]

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
