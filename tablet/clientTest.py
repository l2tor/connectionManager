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

class Test:
    def __init__(self):
        pass

    def test(self,params):
        logging.info("test method called with: " + params)

    def test_underscore(self,params):
        logging.info("test_underscore method called with: " + params)

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
                rawString = sock.recv(1024)
                if rawString == "":
                    logging.info("Empty string received. Ask to the server to stop")
                    runningReading = False
                    break
                else:
                    completeString += rawString

        except socket.error, e:
            logging.debug("error on socket: " + str(e))
            runningReading = False
            pass

        if completeString != "":
            if completeString[-1] != "#":
                index = completeString.rfind("#")
                aMessages += completeString[:index].split("#")
                remainingString = completeString[index+1:]
            else:
                aMessages += completeString.split("#")

        time.sleep(1)


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

    logging.info("Attempt to connect to: " + ip)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server_address = (ip, 1111)
    sock.connect(server_address) 
    
    aMessages = []
    t = threading.Thread(target=readMessages, args=(sock, aMessages))
    t.start()

    logging.info("register test")
    sendMessage(sock,"register:test")
    myTest = Test()

    try:
        while True:
            for strMessage in aMessages:
                if strMessage != "":
                    fields = strMessage.split("|")
                    logging.debug("received message from " + str(fields[0])) 
                    method = fields[1]
                    params = fields[2]
                    getattr(myTest,method)(params)
            del aMessages[:]

            logging.debug("send message")
            time.sleep(1)

    except KeyboardInterrupt:
        global runningReading
        logging.info("Stop the client")
        runningReading = False
        t.join()
        sock.close()
        logFormatter.stopReadingLogs()


if __name__ == "__main__":
    main()
