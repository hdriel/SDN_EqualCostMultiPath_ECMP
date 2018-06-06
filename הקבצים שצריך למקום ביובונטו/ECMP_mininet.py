#!/usr/bin/python
 
from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
from mininet.topo import Topo
import simplejson as json
import sys


FILE_NAME_ECMP_GRAPH = 'ECMP_graph.py'
create_random_graph = True

# arguments for ECMP_graph.py file
n 		= 10
p 		= 0.2
MIN_HOSTS 	= 2
FILE_NAME_IMG 	= 'graph'
printResult 	= False


def getData(file_name):
   dictjson = {}
   with open(file_name + '.txt') as handle:
     dictjson = json.loads(handle.read())
   return dictjson

def showNetPic(file_name):
   try:
     pass
     #webbrowser.open(file_name + '.png')
   except:
     print "Unable to load image of graph"
   




setLogLevel( 'info' )
info( '*** Init mininet Network\n' )
class AssingmentTopology(Topo):
   def __init__(self):
     Topo.__init__(self)
     
   def build(self):
     if(create_random_graph): 
       sys.argv = [str(n), str(p), str(MIN_HOSTS), FILE_NAME_IMG,str(printResult)]
       execfile(FILE_NAME_ECMP_GRAPH)
     "Create a simulated network"
     showNetPic(FILE_NAME_IMG)
     data = getData(FILE_NAME_IMG);
     links = data['links']
     data = data['attrs']
     hostsAndSwitch = []

     info( '*** Adding hosts and Switches...\n' )
     for i in data:
       h = None
       if   (data[i]['kind'] == 'host'):h = self.addHost(data[i]['name']  , ip = data[i]['ip'], mac = data[i]['mac'])
       else:                            h = self.addSwitch(data[i]['name'], dpid = data[i]['dpid'])
       if h is not None:                hostsAndSwitch.append([h,data[i]['name']])
       
     #c1 = self.addHost('c1', ip='10.0.0.1', mac='00:00:00:00:00:01')
     #srv = self.addSwitch( 'sr', dpid='1')
     
     info( '*** Creating links...\n' )
     for key_index in links:
       h1 = links[key_index]['h_src']
       h2 = links[key_index]['h_dst']
       p1 = links[key_index]['port_src'] 
       p2 = links[key_index]['port_dst']
       for i in range(len(hostsAndSwitch)):
         if(hostsAndSwitch[i][1] == h1): h1 = hostsAndSwitch[i][0]
         if(hostsAndSwitch[i][1] == h2): h2 = hostsAndSwitch[i][0]
       self.addLink(h1,h2, port1 = p1, port2 = p2)


topo = AssingmentTopology()
net = Mininet(topo=topo, controller=lambda name: RemoteController(name, ip='127.0.0.1', protocol='tcp', port = 6633), link=TCLink)


info( '*** Starting network\n')
net.start()
info( '*** Running CLI\n' )
CLI( net )
info( '*** Stopping network' )
net.stop()

