from pox.core import core
from pox.openflow import *
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.packet.arp import arp
from pox.lib.packet.ipv4 import ipv4
import time
import random
import json
from pprint import pprint
import simplejson as json
import sys

###############################################################################
## help functions
requestPaths = {}

attrsNodes = {} 
attrsLinks = {} 
FILE_NAME_JSON = "graph"
def getData(file_name):
	dictjson = {}
	with open(file_name + '.txt') as handle:
		dictjson = json.loads(handle.read())
	return dictjson

ipToMac = {}
macToIp = {}
def initData():
	global attrsNodes,attrsLinks, ipToMac, macToIp
	if (attrsNodes is None or attrsNodes == {}):
		data 	   = getData(FILE_NAME_JSON)
		attrsNodes = data["attrs"]
		attrsLinks = data["links"]
		ipToMac    = {}
		macToIp    = {}

	for i in attrsNodes:
		if attrsNodes[i]["kind"] == "host":
			ipToMac[attrsNodes[i]["ip" ]] = attrsNodes[i]["mac"]
			macToIp[attrsNodes[i]["mac"]] = attrsNodes[i]["ip" ]
				

def getRandomPath(mac_src, mac_dst):
	if requestPaths.get((mac_src, mac_dst), None) is not None:
		return requestPaths[(mac_src, mac_dst)]
	
	index_src , index_dst = -1, -1
	for i in attrsNodes:
		if(attrsNodes[i]["kind"] == "host" and attrsNodes[i]["mac"] == mac_src): index_src = i
		if(attrsNodes[i]["kind"] == "host" and attrsNodes[i]["mac"] == mac_dst): index_dst = i
	 
	if(index_src != -1 and index_dst != -1):
		paths = list(filter(lambda p: 
				True if p[0] == attrsNodes[index_src]["name"] and 
					p[len(p)-1] == attrsNodes[index_dst]["name"] else False , 
				attrsNodes[index_src]["paths"]))
		requestPaths[(mac_src, mac_dst)] = random.choice(paths)

	return requestPaths[(mac_src, mac_dst)]

###############################################################################
## functions for handling methods

def switch_routing(event):
	""" for now it like hub send packet to all links"""
	packet = event.parsed
	dpid 	= str(event.dpid)
	mac_src = str(packet.src)
	mac_dst = str(packet.dst)
	ip_src 	= str(packet.next.srcip)
	ip_dst 	= str(packet.next.dstip)
	outport = None
	switch 	= None
	h_dst  	= None
	
	#print "str(packet.next.srcip) : " , ip_src
	#print "str(packet.src)        : " , mac_src
 	#print "str(packet.next.dstip) : " , ip_dst
 	#print "str(packet.dst)        : " , mac_dst

 	path = requestPaths.get((mac_src, mac_dst), None)
	if path is None: path = getRandomPath(mac_src, mac_dst)

	for i in attrsNodes: 
		if (attrsNodes[i]["kind"] == "host"   and attrsNodes[i]["mac"] == mac_dst): h_dst = attrsNodes[i]["name"]
		if (attrsNodes[i]["kind"] == "switch" and attrsNodes[i]["dpid"] == dpid):   switch = attrsNodes[i]
		if h_dst is not None and switch is not None: break

	for p in range(len(path)-1): 
		if(path[p] == switch["name"]):
			if (p == 1): 
				print "[", path[0] ,
			outport     = switch["ports"][path[p+1]]
			print " -> ", path[p] ,
			if(path[p+1] == h_dst):				
				print "->", path[p+1] , " ]"
				print "----------------------------------------------------"
				del requestPaths[(mac_src, mac_dst)]
	
        if(outport is not None):
	    	e      		= ethernet()
	    	e.type 		= ethernet.IP_TYPE
	    	e.src  		= mac_src
	    	e.dst  		= ip_dst
	    	e.set_payload(packet.next)
	    	msg		= of.ofp_packet_out()
	    	msg.data      	= e.pack()
	    	msg.in_port   	= event.port
	    	msg.actions.append(of.ofp_action_dl_addr.set_src(mac_src))
	    	msg.actions.append(of.ofp_action_dl_addr.set_dst(mac_dst))
	    	msg.actions.append(of.ofp_action_nw_addr.set_src(IPAddr(ip_src)))
	    	msg.actions.append(of.ofp_action_nw_addr.set_dst(IPAddr(ip_dst)))
	    	msg.actions.append(of.ofp_action_output(port=outport))	
	    	event.connection.send(msg)


# handle ARP request and respond
def _arp(event):
	packet     = event.parsed
	arp_packet = packet.find('arp')  
	ip_src = str(arp_packet.protosrc)
	ip_dst = str(arp_packet.protodst)
	mac_src     = ipToMac[ip_src]
	mac_dst     = ipToMac[ip_dst]

	if arp_packet is not None:
		print "From  host  : ip = " , ip_src , ", mac = ", mac_src
		print "To    host  : ip = " , ip_dst , ", mac = ", mac_dst 

		if arp_packet.opcode == arp.REQUEST:      
			#print "arp.REQUEST"
			#create arp packet
			a           = arp()
			a.opcode    = arp.REPLY

			#if request from src, fake reply from dst
			if arp_packet.hwsrc == EthAddr(mac_src): 
				a.hwsrc = EthAddr(mac_dst)
				a.hwdst = EthAddr(mac_src) 
			elif arp_packet.hwsrc == EthAddr(mac_dst):
				a.hwsrc = EthAddr(mac_src)
				a.hwdst = EthAddr(mac_dst)

			#fake reply IP
			a.protosrc  = IPAddr(ip_dst)
			a.protodst  = arp_packet.protosrc
			a.hwlen     = 6
			a.protolen  = 4
			a.hwtype    = arp.HW_TYPE_ETHERNET
			a.prototype = arp.PROTO_TYPE_IP
		    
			#create ethernet packet
			e = ethernet()
			e.set_payload(a)
			e.type      = ethernet.ARP_TYPE
			if arp_packet.hwsrc == EthAddr(mac_src): 
				e.src = EthAddr(mac_dst)
				e.dst = EthAddr(mac_src) 
			elif arp_packet.hwsrc == EthAddr(mac_dst):
				e.src = EthAddr(mac_src)
				e.dst = EthAddr(mac_dst) 
	    
			msg         = of.ofp_packet_out()
			msg.data    = e.pack()
			msg.actions.append(of.ofp_action_nw_addr( of.OFPAT_SET_NW_DST,IPAddr(ip_dst)))  
			msg.actions.append( of.ofp_action_output( port = event.port ) )
			event.connection.send(msg)
			
			getRandomPath(mac_src, mac_dst) # choice random path from h_src to h_dst
			getRandomPath(mac_dst, mac_src) # choice random path from h_dst to h_src (back transfer)
			
			print "-------------------------------------------------------\n"			
			print "Random path : \t"




###############################################################################
## handling methods

def _handle_ConnectionUp (event):
	""" fire When the switches connect to the controller first time! """
	print "ConnectionUp event fired - init setup switch s", event.dpid, " !"
	initData()
  
  
def _handle_PacketIn(event):
	"""fire each time host send a packet (ping) to another host... """
	packet = event.parsed
	if   packet.type == packet.ARP_TYPE:
		print "ARP: start request connection..."
		h_src_name = _arp(event)
	elif packet.type == packet.IP_TYPE:
		switch_routing(event)  

def _handle_ConnectionDown (event):
	""" fire When the switches connect to the controller first time! """
	print "ConnectionDown event fired - disconnect switch s", event.dpid, " !"
	attrsNodes = {}
  

###############################################################################
## main function for controller
def launch():
	core.openflow.addListenerByName("ConnectionUp"  , _handle_ConnectionUp  )
	core.openflow.addListenerByName("PacketIn"      , _handle_PacketIn      )
	core.openflow.addListenerByName("ConnectionDown", _handle_ConnectionDown)
	print "Custom Controller running."
  



    
    
    


    
