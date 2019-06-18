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

class Stuff:
    def __init__(self):
        pass

    def stuff(self,params):
        logging.info("stuff method called with: " + params)

    def paf(self,params):
        logging.info("paf method called with: " + params)

    def pif(self,params):
        logging.info("pif method called with: " + params)

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
    strLogFile = "logs/client-stuff.log"
    logging.basicConfig(filename=strLogFile, level=logging.DEBUG, format='%(levelname)s %(relativeCreated)6d %(threadName)s %(message)s (%(module)s.%(lineno)d)',filemode='w')
    logFormatter = lf.LogFormatter(strLogFile)
    logFormatter.start()

    logging.info("start the test script of the client")

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

    logging.info("register stuff")
    sendMessage(sock,"register:stuff")

    myStuff = Stuff()

    nCpt = 0
    try:
        while True:

            logging.debug("send message")
            sendMessage(sock,"call:tablet.test.test 1.0")
            sendMessage(sock,"call:tablet.test.test 2.0")
            sendMessage(sock,"call:tablet.test.test 3.0")

            for strMessage in aMessages:
                if strMessage != "":
                    fields = strMessage.split("|")
                    logging.info("received message from " + str(fields[0])) 
                    method = fields[1]
                    params = fields[2]
                    getattr(myStuff,method)(params)
            del aMessages[:]
            #if nCpt % 7 == 0:
            #    sendMessage(sock,"call:nao.ALTextToSpeech.say 'it's time to do a test. So we are going to put a pretty long text, and see what's happening'")
            #    nCpt = 0
            #nCpt += 1
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
