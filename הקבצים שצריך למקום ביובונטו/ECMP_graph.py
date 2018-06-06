#!/usr/bin/python
 
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pprint import pprint
import random
import simplejson as json
import sys


FILE_NAME 	= 'graph'
n 		= 10
p 		= 0.2
host 		= 1
switch 		= 1
attrs 		= {}
hosts 		= []
switchs 	= []
labels 		= {}
links 		= {}
MIN_HOSTS 	= 2
printResult 	= True
pos	 	= None
G		= None
#####################################################################
## networkx - graph generation

## create a random graph
def GenerateRandomGraph():
	global nx, G, pos
	ConnectedGraph = False
	while not ConnectedGraph:
		G = nx.erdos_renyi_graph(n,p, seed = None, directed = False)
		ConnectedGraph = nx.is_connected(G)
	pos=nx.spring_layout(G)

#####################################################################
## function 

## save graph to file in json format
def saveToFile(G, fname):
			#nodes = list(G.nodes()),
			#edges = list(G.edges()),
	json.dump(dict(	attrs = attrs,
    			links = links),
		  open(fname, "w"), indent=2)
	
## convert int to ip 
def ipAddr(n):
	return '10.0.0.'+ str(n)

## convert int to mac
def macAddr(n):
	mac = hex(n)
	mac = mac.split('x')[1].zfill(12)
	mac = ':'.join(''.join(x) for x in zip(*[iter(mac)]*2))
	return mac

## add host attributes  
def addHostAttr(v):
	global host, 	hosts,	labels, attrs, macAddr, ipAddr
	nameHost  = 'h' + str(host)
	labels[v] = r'$'+nameHost+'$'
	attrs[v]  = {'kind' : 'host' , 'name' : nameHost, 'mac' : macAddr(host), 'ip' : ipAddr(host)}
	host      = host + 1
	hosts.append(v)

## add switch attributes 
def addSwitchAttr(v):
	global switch, switchs,	labels, attrs, macAddr, ipAddr
	nameSwitch  = 's' + str(switch)
	labels[v] = r'$'+nameSwitch+'$'
	attrs[v] = {'kind' : 'switch' , 'name' : nameSwitch, 'dpid' : str(switch)}
	switch = switch + 1
	switchs.append(v)

## add ports out to Node v
def addPortsForNode(v):
	global G, attrs
        ports = {}
	nieghbors = list(G.neighbors(v))
	i = 1
	for u in nieghbors:
		ports[attrs[u]['name']] = i
		i = i + 1
	attrs[v]['ports'] = ports

## add links
def addEdgesNames():
	global G, attrs, links
	edgesNamed = {}
	i = 1
	for v,u in G.edges(): 
		p_src = ''
		p_dst = ''
		if(('ports' in attrs[v]) and attrs[u]['name'] in attrs[v]['ports']):
			p_src = attrs[v]['ports'][attrs[u]['name']]
		if(('ports' in attrs[u]) and attrs[v]['name'] in attrs[u]['ports']):
			p_dst = attrs[u]['ports'][attrs[v]['name']]
		edgesNamed[i] = {'h_src': attrs[v]['name'],'h_dst': attrs[u]['name'],'port_src': p_src,'port_dst':p_dst }	
		i = i + 1
	links = edgesNamed

#####################################################################
## setting host and switch to graph 
def setupNetwork():
   	global nx, G, host , switch, attrs, hosts, switchs, labels, links, addHostAttr, addSwitchAttr, addPortsForNode, addEdgesNames
	## set each node with one neighbor to Host
	for v in range(len(list(G.nodes()))):
		if len(list(G.neighbors(v))) == 1:
 			# set node as host
			addHostAttr(v)


	## there are minimum hosts - add rest nodes as switchs
	if len(hosts) >= MIN_HOSTS:
		# set rest nodes as servers
		for v in range(len(list(G.nodes()))):
			if v not in hosts:
	 			# set node as switch
				addSwitchAttr(v)
	else: 
		# complete mininum hosts
		for v in range(MIN_HOSTS - len(hosts)):
			while True:
				v = random.choice(list(G.nodes()))
				h_edge_s = True
				for u in list(G.neighbors(v)):
					if (u in hosts): h_edge_s = False
				if (v not in hosts) and h_edge_s:
					break;
			addHostAttr(v)
		# add rest nodes as switchs
		for v in range(len(list(G.nodes()))):
			if v not in hosts:
	 			# set node as switch
				addSwitchAttr(v)

	## add all simple path to atrribute
	for h_src in hosts:
		named_paths = []
		for h_dst in hosts:
			if not(h_src == h_dst):
				paths = list(nx.all_simple_paths(G,source = h_src,target = h_dst))
				for p in paths:
					named_paths.append(list(map(lambda h: attrs[h]['name'] , p)))
		attrs[h_src]['paths'] = named_paths

	## add port to each switch
	for v in range(len(list(G.nodes()))):
		addPortsForNode(v)

	## add links to attrs
	addEdgesNames();

## add another configurations for display and data graph
def setConfigurationGraph():
	global nx, G, attrs, hosts, switchs, labels, saveToFile, pos, plt, FILE_NAME, random
	nx.set_node_attributes(G, attrs)
	nx.draw_networkx_nodes(G,pos,
		               nodelist=hosts,
		               node_color='b',
		               node_size=500,
		               alpha=0.8)
	nx.draw_networkx_nodes(G,pos,
		               nodelist=switchs,
		               node_color='r',
		               node_size=500,
		               alpha=0.8)
	nx.draw_networkx_labels(G,pos,labels,font_size=14)
	nx.draw_networkx_edges(G,pos,width=1.0,alpha=0.5)
	plt.axis('off')


	## save data graph to json file and image file
	plt.savefig(FILE_NAME +'.png')
	print 'save random graph image to file: ' , FILE_NAME, ".png"
	saveToFile(G, FILE_NAME+'.txt')
	print 'save random graph  json to file: ' , FILE_NAME, ".txt"


## print graph data
def printData():
	print 'hosts   : ', hosts
	print 'switchs : ', switchs
	for node in attrs: 
		print node
		for attr in attrs[node]:
			if attr == 'paths':
				print '\t', attr, "\t:\t" ,
				for p in range(len(attrs[node][attr])):
					if p == 0: print attrs[node][attr][p]
					else     : print '\t\t\t' , attrs[node][attr][p]
			else: 
				print '\t', attr , "\t:\t", attrs[node][attr]
		print '-'*50


if __name__ == "__main__":
	if(sys.argv[0] is not None): n	 	= int(sys.argv[0])
	if(sys.argv[1] is not None): p	 	= float(sys.argv[1])
	if(sys.argv[2] is not None): MIN_HOSTS 	= int(sys.argv[2])
	if(sys.argv[3] is not None): FILE_NAME 	= sys.argv[3]
	if(sys.argv[4] is not None): printResult= sys.argv[4] == 'True'

	GenerateRandomGraph()
	setupNetwork()
	setConfigurationGraph()
	if(printResult): printData()

	
    

