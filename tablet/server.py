#!/usr/bin/env python
# coding: utf-8 
import SocketServer
import threading
import socket
import os
import errno 
import select
from websocket_server import WebsocketServer
from threading import Thread
from threading import Lock

import re
import time
import sys
import argparse
from Queue import Queue
import netifaces as ni
if os.name == "nt":
    import _winreg as wr
from pprint import pprint

import logging
import log_formatter as lf

from naoqi import ALProxy

# Stores the calls to send to registered modules
aRegistered = {}
registeredLock = Lock()
msgsForWeb = Queue()

# Stores access (through ALProxy) to the modules installed on NAO
aRegisteredNao = {}
registeredLockNao = Lock()

robotIP = ""
runningAllServer = True

class websocketclass():
    

    def __init__(self):
        PORT=9014


        self.callSingle   = re.compile("call:([a-zA-Z]+)\.([a-zA-Z]+)\.([a-zA-Z_]+)[|]?(.*)")
        self.callMultiple = re.compile("call:([a-zA-Z]+)\.\[([a-zA-Z,]+)\]\.([a-zA-Z_]+)[|]?(.*)")
        self.callAll      = re.compile("call:([a-zA-Z]+)\.\*\.([a-zA-Z_]+)[|]?(.*)")
        
        self.server = WebsocketServer(PORT)
        self.server.set_fn_new_client(self.new_client)
        self.server.set_fn_client_left(self.client_left)
        self.server.set_fn_message_received(self.message_received)
        threading.Thread(target=self.run).start()
        self.server.run_forever()

    def analyzeMessage(self,strMessage):
        # If the module wants to call a method, analyze the call (for tablet or nao)
        # and dispached it accordingly
        matchCallSingle = self.callSingle.match(strMessage)
        if matchCallSingle:
            strDestDevice = matchCallSingle.group(1)
            strDestModule = matchCallSingle.group(2)
            strCallMethod = matchCallSingle.group(3)
            strCallParams = matchCallSingle.group(4)
            self.handleCallSingle(strDestDevice,strDestModule,strCallMethod,strCallParams)
            return

        # If the module wants to call a method in multiple mudules, get the name of the
        # modules and dispached it accordingly
        matchCallMultiple = self.callMultiple.match(strMessage)
        if matchCallMultiple:
            strDestDevice = matchCallMultiple.group(1)
            aDestModule   = matchCallMultiple.group(2).split(",")
            strCallMethod = matchCallMultiple.group(3)
            strCallParams = matchCallMultiple.group(4)

            for strDestModule in aDestModule:
                self.handleCallSingle(strDestDevice,strDestModule,strCallMethod,strCallParams)
            return
            
        # If the module wants to call a method in all known mudules, go through all modules
        # and send according message
        matchCallAll = self.callAll.match(strMessage)
        if matchCallAll:
            strDestDevice = matchCallAll.group(1)
            strCallMethod = matchCallAll.group(2)
            strCallParams = matchCallAll.group(3)

            for strDestModule in aRegistered:
                self.handleCallSingle(strDestDevice,strDestModule,strCallMethod,strCallParams)
            return

    def handleCallSingle(self,strDestDevice,strDestModule,strCallMethod,strCallParams):
        logging.debug("handle call: " + strDestDevice + " " + strDestModule + " " +  strCallMethod + " " + strCallParams)

        # If the called module is on tablet, store the call in aRegistered
        if strDestDevice == "tablet": 
            if strDestModule in aRegistered:
                registeredLock.acquire()
                aRegistered[strDestModule].append(("TabletGame",strCallMethod,strCallParams))
                registeredLock.release()

        # If the called module is on Nao, call the method through ALProxy
        if strDestDevice == "nao":
            # If the called module is yet yet in aRegisteredNao creates and stores
            # a new instantiation
            try:
                registeredLockNao.acquire()
                if not strDestModule in aRegisteredNao: 
                    aRegisteredNao[strDestModule] = ALProxy(strDestModule,robotIP,9559)
                registeredLockNao.release()
            except RuntimeError:
                registeredLockNao.release()
                logging.error("Could not obtain module " + strDestModule + " on Nao")
                return

            # Call the method of the instantiated called module
            try:
                t = None
                if(strCallParams!=""):
                    t = threading.Thread(target=getattr(aRegisteredNao[strDestModule],strCallMethod),args=(strCallParams,))
                else:
                    t = threading.Thread(target=getattr(aRegisteredNao[strDestModule],strCallMethod))
                t.start()
            except RuntimeError:
                logging.error("Could not call method " + strCallMethod + " on Nao")

    def new_client(self,client, server):
        logging.info("New client connected and was given id %d" % client['id'])
        registeredLock.acquire()
        aRegistered["tabletgame"] = []
        registeredLock.release()
	    #server.send_message_to_all("Hey all, a new client has joined us")

    def message_received(self, client, server, message):
        logging.info("Text message received:" + message)
        self.analyzeMessage(message)

    def run(self):
            global msgsForWeb
            while 1:          
                if not msgsForWeb.empty():
                    self.tosend=msgsForWeb.get()
                    logging.info("Message to send from Webscoket thread:" + self.tosend)
                    try:
                        self.server.send_message_to_all(self.tosend)
                    except:
                        logging.erro("Unexpected error:", sys.exc_info()[0])
                time.sleep(0.1)

    def client_left(self, client, server):
        logging.info("Client(%d) disconnected" % client['id'])
        registeredLock.acquire()
        del aRegistered["tabletgame"]
        registeredLock.release()
        

class ServerReceiver(Thread):
    """
    Thread used by the server to retreive data. One thread per module.
    """

    def __init__(self, request, server):
        """
        Constructor

        Parameters :
            request - The request of the BaseRequestHandler object
        """

        Thread.__init__(self)
        
        self.threadIsAlive = True
        self.request       = request
        self.server        = server
        self.strModule     = ""
        self.peername      = self.request.getpeername()

        # Patterns to be matched to the modules connected
        self.register     = re.compile("register:([a-zA-Z]+)")
        self.exit         = re.compile("exit")
        self.callSingle   = re.compile("call:([a-zA-Z]+)\.([a-zA-Z]+)\.([a-zA-Z_]+)[|]?(.*)")
        self.callMultiple = re.compile("call:([a-zA-Z]+)\.\[([a-zA-Z,]+)\]\.([a-zA-Z_]+)[|]?(.*)")
        self.callAll      = re.compile("call:([a-zA-Z]+)\.\*\.([a-zA-Z_]+)[|]?(.*)")

    
    def handleCallSingle(self,strDestDevice,strDestModule,strCallMethod,strCallParams):
        logging.debug("handle call: " + strDestDevice + " " + strDestModule + " " +  strCallMethod + " " + strCallParams)

        # If the called module is on tablet, store the call in aRegistered
        if strDestDevice == "tablet": 
            if strDestModule == "WebSocket": #forward the message to the websocket immediately
                logging.debug("Filling Queue with:" + strCallMethod + " " + strCallParams)
                msgsForWeb.put(strCallMethod + "|" + strCallParams)
                #the module is not registered so it wont go below
            if strDestModule in aRegistered:
                registeredLock.acquire()
                aRegistered[strDestModule].append((self.strModule,strCallMethod,strCallParams))
                registeredLock.release()

        # If the called module is on Nao, call the method through ALProxy
        if strDestDevice == "nao":
            # If the called module is yet yet in aRegisteredNao creates and stores
            # a new instantiation
            try:
                registeredLockNao.acquire()
                if not strDestModule in aRegisteredNao: 
                    aRegisteredNao[strDestModule] = ALProxy(strDestModule,robotIP,9559)
                registeredLockNao.release()
            except RuntimeError:
                registeredLockNao.release()
                logging.error("Could not obtain module " + strDestModule + " on Nao")
                return

            # Call the method of the instantiated called module
            try:
                t = None
                if(strCallParams!=""):
                    t = threading.Thread(target=getattr(aRegisteredNao[strDestModule],strCallMethod),args=(strCallParams,))
                else:
                    t = threading.Thread(target=getattr(aRegisteredNao[strDestModule],strCallMethod))
                t.start()
            except RuntimeError:
                logging.error("Could not call method " + strCallMethod + " on Nao")

    def analyzeMessage(self,strMessage):
        # If a new module send a register message, create an entry in aRegistered.
        # This entry is a list that stores the call to be send to the module
        matchRegister = self.register.match(strMessage)
        if matchRegister:
            strModule = matchRegister.group(1)
            if strModule not in aRegistered:
                logging.info("Register: " + strModule + " on " + str(self.server.peername))
                registeredLock.acquire()
                aRegistered[strModule] = []
                registeredLock.release()
            else:
                logging.warning("Module already registered. Will register anyway")
            # Makes sure that the instantiation of ServerReceiver knows the name
            # of the corresponding module. Used by Server
            self.strModule = strModule
            return
        
        # If a module send an exit message, close the corresponding receivers
        matchExit = self.exit.match(strMessage)
        if matchExit:
            logging.info("Exit message received. Ask to the server to stop")
            self.server.runningServer = False
            return

        # If the module wants to call a method, analyze the call (for tablet or nao)
        # and dispached it accordingly
        matchCallSingle = self.callSingle.match(strMessage)
        if matchCallSingle:
            strDestDevice = matchCallSingle.group(1)
            strDestModule = matchCallSingle.group(2)
            strCallMethod = matchCallSingle.group(3)
            strCallParams = matchCallSingle.group(4)
            self.handleCallSingle(strDestDevice,strDestModule,strCallMethod,strCallParams)
            return

        # If the module wants to call a method in multiple mudules, get the name of the
        # modules and dispached it accordingly
        matchCallMultiple = self.callMultiple.match(strMessage)
        if matchCallMultiple:
            strDestDevice = matchCallMultiple.group(1)
            aDestModule   = matchCallMultiple.group(2).split(",")
            strCallMethod = matchCallMultiple.group(3)
            strCallParams = matchCallMultiple.group(4)

            for strDestModule in aDestModule:
                self.handleCallSingle(strDestDevice,strDestModule,strCallMethod,strCallParams)
            return
            
        # If the module wants to call a method in all known mudules, go through all modules
        # and send according message
        matchCallAll = self.callAll.match(strMessage)
        if matchCallAll:
            strDestDevice = matchCallAll.group(1)
            strCallMethod = matchCallAll.group(2)
            strCallParams = matchCallAll.group(3)

            for strDestModule in aRegistered:
                self.handleCallSingle(strDestDevice,strDestModule,strCallMethod,strCallParams)
            return

    def run(self):
        """
        Main loop for the thread
        """

        remainingString = ""

        while self.threadIsAlive:
            rawString = ""
            completeString = remainingString #Get what was left of the last reception
            remainingString = ""

            try:
                while not "#" in completeString:
                    rawString = self.request.recv(1024)

                    if rawString == "":
                        logging.info("Empty string received. Ask to the server to stop")
                        self.threadIsAlive = False
                        self.server.runningServer = False
                        break
                    else:
                        rawStringCpt = 0
                        logging.debug("message received from " + str(self.peername) + " : " + str(rawString))
                        completeString += rawString

            except socket.error as error:
                if os.name == "nt":
                    if error.errno == errno.WSAECONNRESET:
                        logging.error("Client %s disconnected by force"  % self.strModule) 
                        self.threadIsAlive = False
                        #registeredLock.acquire()
                        #del aRegistered[strModule]
                        #registeredLock.release()
                        #self.killThread()
                        break
                else:
                    if error.errno == errno.ECONNREFUSED:
                        logging.error("Client %s disconnected by force"  % self.strModule) 
                        self.threadIsAlive = False
                        #registeredLock.acquire()
                        #del aRegistered[strModule]
                        #registeredLock.release()
                        #self.killThread()
                        break
            except:
                logging.error("Unexpected error" + str(sys.exc_info()[0]))
                raise


            aMessages = []
            if completeString != "":
                if completeString[-1] != "#":
                    index = completeString.rfind("#")
                    aMessages = completeString[:index].split("#")
                    remainingString = completeString[index+1:]
                else:
                    aMessages = completeString.split("#")

            for strMessage in aMessages:
                logging.debug("analyze : " + strMessage)
                self.analyzeMessage(strMessage)


        registeredLock.acquire()
        logging.info("Ending module " + self.strModule + " on  " + str(self.server.peername))
        if self.strModule in aRegistered:
            del aRegistered[self.strModule]
        registeredLock.release()
        self.server.runningServer = False


    def killThread(self):
        """
        Stop the thread's loop
        """

        logging.info("Stop the receiver on " + str(self.peername))
        self.threadIsAlive = False




class Server(SocketServer.BaseRequestHandler):
    """
    The request handler class for the server.
    This class is instanciated once per connection to the server.
    """

    def setup(self):
        self.runningServer = True
        self.peername = self.request.getpeername()
        
        #variables usefull for communation to the control pannel
        self.updateFrequency = 5 #update frequency in seconds
        self.lastUpdateTime = time.time()

    def handle(self):
        """
        Override the handle() method to implement the communication with
        the client.
        """
        logging.info("Client connected on " + str(self.peername))

        self.receiver          = ServerReceiver(self.request,self)
        patternBrokenPipe = re.compile("\[Errno 32\] Broken pipe")
        
        self.receiver.start()
        logging.info("Receiver started")
        
        try:
            while runningAllServer == True and self.runningServer == True:
                logging.debug(self.receiver.strModule + " : " + str(aRegistered))

                #Update regularly ControlPanel on the modules connected
                if self.receiver.strModule == "ControlPanel":
                    if (time.time() - self.lastUpdateTime) > self.updateFrequency:
                        messageToSend = "call:connectionmanager|listActiveModules|["
                        registeredLock.acquire()
                        for modules in aRegistered:
                            messageToSend += modules + ","
                        registeredLock.release()
                        tmpList = list(messageToSend)
                        tmpList[-1] = "]"
                        messageToSend = ''.join(tmpList)
                        messageToSend += "#"
                        logging.debug("send: " + messageToSend)
                        self.request.sendall(messageToSend)
                        self.lastUpdateTime = time.time()

                # Send the messages to the module
                registeredLock.acquire()
                if self.receiver.strModule in aRegistered:
                    while len(aRegistered[self.receiver.strModule]) != 0:
                        aMessage = aRegistered[self.receiver.strModule].pop(0)
                        logging.info("send: " + str(aMessage))
                        self.request.sendall("call:" + aMessage[0] + "|" + aMessage[1] + "|" + aMessage[2] + "#")
                registeredLock.release()
                #TODO raise exception if strModule not in aRegistered
                time.sleep(0.01)

                        


        except socket.error, e:
            logging.warning("Exception happened while broadcasting the data : " + str(e))
            match = patternBrokenPipe.search(str(e))

            if match != None:
                logging.error("Connection to peer lost, server shutting down")

        finally:
            logging.info("Server closing on " + str(self.peername))
            self.receiver.killThread()

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

def get_network_guid(iface_guids,networkType):
    reg = wr.ConnectRegistry(None, wr.HKEY_LOCAL_MACHINE)
    reg_key = wr.OpenKey(reg, r'SYSTEM\ControlSet001\Control\Network\{4D36E972-E325-11CE-BFC1-08002BE10318}')
    for i in range(len(iface_guids)):
        try:
            reg_subkey = wr.OpenKey(reg_key, iface_guids[i] + r'\Connection')
            name = wr.QueryValueEx(reg_subkey, 'Name')[0]
            if networkType == "wifi":
                if "Wi-Fi" in name or "WiFi" in name or "sans fil" in name or "Wireless Network Connection" in name:
                    # [Jan] The problem here is that my laptop has an unused "Wireless Network Connection 2"
                    # which is now returned and does not have an IP assigned. So we need to see if a connection is actually present
                    addr = ni.ifaddresses(iface_guids[i])
                    if 2 in addr:
                        return iface_guids[i]
            else:
                if "Ethernet" in name :
                    # [Jan] The problem here is that my laptop has an unused "Wireless Network Connection 2"
                    # which is now returned and does not have an IP assigned. So we need to see if a connection is actually present
                    addr = ni.ifaddresses(iface_guids[i])
                    if 2 in addr:
                        return iface_guids[i]
        except OSError as e:
            pass
    return None

def main():
    global runningAllServer
    global robotIP

    # Parse the given arguments
    parser = argparse.ArgumentParser(description='Broker for communication between modules.')
    parser.add_argument('--robotIP',nargs=1,dest="robotIP",help="Pass the robot ip. The ip will be autimically stored for further use.")
    parser.add_argument('--ethernet',dest='networkType',default='wifi',action='store_const',const='ethernet',help='Use to rely on ethernet connection on the tablet. By default the wifi connection is used')
    parser.add_argument('--computerIP',nargs=1,dest="computerIP",default=None,help="Pass the ip of the computer. If not set, the program will try to deduce the ip automatically")
    args = parser.parse_args()

    logsdir="logs"
    #creates the logs folder if it doesnt exist
    if not os.path.exists(logsdir):
        os.makedirs(logsdir)
    
    logFile = 'logs/' + time.strftime('%Y%m%d-%H%M%S') + '-server.log'

    logging.basicConfig(filename=logFile, 
                        level=logging.DEBUG, 
                        format='%(levelname)s %(asctime)-15s %(threadName)s %(message)s (%(module)s.%(lineno)d)',
                        datefmt='%H.%M.%S',
                        filemode='w')
    logFormatter = lf.LogFormatter(filename=logFile,level=lf.WARNING)
    logFormatter.start()

    logging.info("start the ConnectionManager")

    #Find out the outside ip
    ip = ""
    if args.computerIP != None:
        ip = args.computerIP[0]
    else:
        logging.info("No ip set. Will try to deduce one")
        try:
            if os.name == "nt":
                guid    = get_network_guid(ni.interfaces(),args.networkType)
                ip      = ni.ifaddresses(guid)[2][0]['addr']
            else:
                if args.networkType == "ethernet":
                    ip      = ni.ifaddresses('eth0')[2][0]['addr']
                else:
                    ip      = ni.ifaddresses('wlan0')[2][0]['addr']
        except Exception, e:
            time.sleep(1)
            logging.error(str(e))
            print("Could not deduce automatically ip. Enter remote ip:")
            ip = raw_input()

    localIp     = "127.0.0.1"
    port        = 1111


    #Find out the ip of the robot
    fileIP      = "robotIP.txt"
    if args.robotIP == None:
        #if no arguments are given use stored IP from file
        #first check if file exists
        if(os.path.exists(fileIP)):
            with open(fileIP, 'r') as f:
                robotIP  = f.readline()
        else:
            logging.info("No IP was given and no previous session was saved on file. Terminating...")
            os._exit(1)
    else:
        #if an argument is given, use that IP and store it
        robotIP          = args.robotIP[0]
        with open(fileIP, "w") as text_file:
            text_file.write(robotIP)
    logging.info("IP of the robot: " + robotIP)


    #Create the two servers: for outside connections and conncection coming from modules running on the same computer
    try:
        SocketServer.TCPServer.allow_reuse_address = True
        tabletServerLocal = ThreadedTCPServer((localIp, port), Server)
        logging.info("Local server created with IP : " + localIp + " on the port " + str(port))
    except Exception, e:
        logging.critical("Exception occured during the creation of the server : " + str(e))

    try:
        SocketServer.TCPServer.allow_reuse_address = True
        tabletServerOut = ThreadedTCPServer((ip, port), Server)
        logging.info("Out server created with IP : " + ip + " on the port " + str(port))
    except Exception, e:
        logging.critical("Exception occured during the creation of the server : " + str(e))

    try:
        #Starting outside server
        tOut = threading.Thread(target=tabletServerOut.serve_forever)
        tOut.start()
        #Starting local server
        tLocal = threading.Thread(target=tabletServerLocal.serve_forever)
        tLocal.start()
        #starting websocket Server 
        threading.Thread(target=websocketclass).start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.debug("KeyBoard interrupt for the main thread")
        pass

    except Exception, e:
        logging.warning('Exception occured while running the server : ' + str(e))

    finally:
        logging.info("Stopping the server...")
        runningAllServer = False
        time.sleep(1)
        try:
            tabletServer.shutdown()
            tabletServer.server_close()
        except Exception, e:
            logging.warning("Forcing shutdown: " + str(e))
        logging.info("Server stopped")
        os._exit(1)
    logFormatter.stopReadingLogs()
    

if __name__ == "__main__":

    main()
    
    
    
    
