# Connection Manager

The purpose of this project is to provide the connection between the modules of the L2TOR project. This server opens two connections: one for the modules running on other devices, and one for modules running on the same device. 

## Installation:


Install the code to run on the tablet
```
tablet$ git clone git@protolab.aldebaran.com:l2tor/connectionManager.git
```
Install termcolor and netifaces using this command:
```
pip install termcolor netifaces
```
## Running:

Run the demo on the tablet. This relies on three terminal termed t1,t2 and t3:
```
tablet$ cd connectionManager/tablet
tablet.t1$ python server.py <robot_ip> #start the server
tablet.t2$ python clientTest.py  #start a client which register under the name test and show the received messages in a log
tablet.t3$ python clientContent.py  #start a client which register under the name content and send messages (through connectionManager) to the test client
```

You should see each the test client receive short and long messages from the other client. You can see how the message is analysed so that the corresponding method is called. 
