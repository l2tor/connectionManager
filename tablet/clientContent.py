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
largeMessage ="call:tablet.test.test|{  \"ground\": \"grass.jpg\",  \"loadable_objects\": [    {    	\"id\": \"m_elephant_1\",    	\"filename\": \"elephant_big.babylon.json\",    	\"collisionEnabled\": true,    	\"position\": {    		\"x\": 271,    		\"z\": -97    	},     	\"rotation\": {    		\"y\": 1.57    	},    	\"scaling\": {    		\"x\": 1.8,    		\"y\": 1.8,    		\"z\": 1.8    	},    	\"hasShadow\": true    },    {    	\"id\": \"m_elephant_2\",    	\"filename\": \"elephant_big.babylon.json\",    	\"collisionEnabled\": true,    	\"position\": {    		\"x\": 196,    		\"z\": 55    	},     	\"rotation\": {    		\"x\": 0,    		\"y\": 1.57,    		\"z\": 0    	},    	\"scaling\": {    		\"x\": 1.8,    		\"y\": 1.8,    		\"z\": 1.8    	},    	\"hasShadow\": true    },    {    	\"id\": \"s_cage_1:box3d_w1\",    	\"filename\": \"cageside.babylon.json\",    	\"collisionEnabled\": true,    	\"position\": {    		\"x\": -95,    		\"y\": -261    	},    	\"rotation\": {    		\"x\": 0,    		\"y\": 1.57,    		\"z\": 0    	},    	\"scaling\": {    		\"x\": 30,    		\"y\": 50,    		\"z\": 20    	},    	\"hasShadow\": true    },    {    	\"id\": \"s_cage_1:box3d_w2\",    	\"filename\": \"cageside.babylon.json\",    	\"collisionEnabled\": true,    	\"position\": {    		\"x\": 32,    		\"y\": -127    	},    	\"rotation\": {    		\"x\": 0,    		\"y\": 0,    		\"z\": 0    	},    	\"scaling\": {    		\"x\": 30,    		\"y\": 50,    		\"z\": 20    	},    	\"hasShadow\": true    },    {    	\"id\": \"s_cage_1:box3d_w3\",    	\"filename\": \"cageside.babylon.json\",    	\"collisionEnabled\": true,    	\"position\": {    		\"x\": -93,    		\"y\": 6    	},    	\"rotation\": {    		\"x\": 0,    		\"y\": 1.57,    		\"z\": 0    	},    	\"scaling\": {    		\"x\": 30,    		\"y\": 50,    		\"z\": 20    	},    	\"hasShadow\": true    },    {    	\"id\": \"s_cage_1:box3d_w4\",    	\"filename\": \"cageside.babylon.json\",    	\"collisionEnabled\": true,    	\"position\": {    		\"x\": -222,    		\"y\": -128    	},    	\"rotation\": {    		\"x\": 0,    		\"y\": 0,    		\"z\": 0    	},    	\"scaling\": {    		\"x\": 30,    		\"y\": 50,    		\"z\": 20    	},    	\"hasShadow\": true    }  ],  \"creatable_objects\": [  	{  		\"type\": \"plane\",  		\"id\": \"s_ground\",  		\"color\": {  			\"diffuse\": {	  			\"r\": 0.83,	  			\"g\": 0.67,	  			\"b\": 0.215  				  			},  			\"specular\": {  				\"r\": 0.1,  				\"g\": 0.2,  				\"b\": 0.1  			}  		},  		\"movable\": false,  		\"position\": {  			\"x\": -95,  			\"z\": -130  		},  		\"rotation\": {  			\"x\": 1.57,  			\"y\": 0,  			\"z\": 0  		},  		\"size\": {  			\"width\": 260,  			\"height\": 260  		},  		\"collisionEnabled\": false,  		\"hasShadow\": false  	}  ]}"

class Content:
    def __init__(self):
        pass

    def test(self,params):
        logging.info("test method called with: " + params)


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


def main():
    #connection to the server and receving the messages
    strLogFile = "logs/client-content.log"
    logging.basicConfig(filename=strLogFile, 
                        level=logging.DEBUG, 
                        format='%(levelname)s %(asctime)-15s %(threadName)s %(message)s (%(module)s.%(lineno)d)',
                        datefmt='%H.%M.%S',
                        filemode='w')
    logFormatter = lf.LogFormatter(strLogFile,level=lf.INFO)
    logFormatter.start()

    logging.info("start the client content")

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

    logging.info("register content")
    sendMessage(sock,"register:content")

    myContent = Content()
    shortMessage = True

    try:
        while True:

            #send alternatively short and long messages
            if shortMessage == True:
                logging.info("send short message")
                sendMessage(sock,"call:tablet.test.test|short")
                shortMessage = False
            else:
                logging.info("send large message")
                sendMessage(sock,largeMessage)
                shortMessage = True

            for strMessage in aMessages:
                if strMessage != "":
                    fields = strMessage.split("|")
                    logging.info("received message from " + str(fields[0])) 
                    method = fields[1]
                    params = fields[2]
                    getattr(myStuff,method)(params)
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
