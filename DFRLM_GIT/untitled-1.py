import networkx, time, cPickle, random, math, copy
from collections import defaultdict




path = "F:\\Dropbox\\research\\DFRLM\\data\\FL\\"
graph_list_f = "graph_list.txt"
OD_Pairs_f = "OD_pairs.txt"
driving_range = 160000   #in meters

OD_pair = cPickle.load(open(path +OD_Pairs_f))
graph_list = cPickle.load(open(path + graph_list_f))

initial_sp = {}
gravity_list = []

OD_routes_sites = {}    #(O,D):[[routes], distance, time, [sites], flow] 


class refuelable_route:      #class for routes 
    def __init__(self, origin, destination, in_graph, sites = []):
        self.origin = origin
        self.destination = destination
        self.graph = in_graph
        self.covered_demand = 0 
        self.shortest_route = OD_routes_sites[(origin, destination)][0]
        self.shortest_dist = OD_routes_sites[(origin, destination)][1]
        self.route = self.shortest_route
        self.sites = sites
        self.movement = []
        self.movement.append(origin)
        self.completed = False
        self.direction = self.destination
        
    def move(self, start_node, distance):
        able = True
        location = start_node
        while able:
            if self.direction == self.destination:
                next_node = self.route[self.route.index(location) + 1]
                moving = graph_list[location][next_node]
                if moving <= distance:
                    distance -= moving
                    location = next_node
                    if location == self.direction:
                        self.direction = self.origin
                else:
                    able = False
            elif self.direction == self.origin:
                next_node = self.route[self.route.index(location) - 1]
                moving = graph_list[location][next_node]
                if moving <= distance:
                    distance -= moving
                    location = next_node
                    if location == self.direction:
                        self.completed = True
                        able = False
                else:
                    able = False
        return location

    def newRoute(self, new_site):
        sites = copy.copy(self.sites)
        sites.append(new_site)
        temp_route = []
        temp_time = 0 
        if len(sites) == 1:
            ori_route = networkx.dijkstra_path(self.graph, self.origin, sites[-1])
            ori_time = networkx.dijkstra_path_length(self.graph, self.origin, sites[-1])
            des_route = networkx.dijkstra_path(self.graph, sites[-1], self.destination)
            des_time = networkx.dijkstra_path_length(self.graph, sites[-1], self.destination)
            temp_route = ori_route + des_route[1:]
            temp_time = ori_time + des_time
        else:
            for i in range(len(sites)):
                if i == 0:
                    temp_route = networkx.dijkstra_path(self.graph, self.origin, sites[i])
                    temp_time = networkx.dijkstra_path_length(self.graph, self.origin, sites[i])
                elif i == len(sites):
                    temp_route = temp_route + networkx.dijkstra_path(self.graph, sites[i], self.destination)
                    temp_time = temp_time + networkx.dijkstra_path_length(self.graph, sites[i], self.destination)
                else:
                    temp_route = temp_route + networkx.dijkstra_path(self.graph, sites[i], sites[i+1])
                    temp_time = temp_time + networkx.dijkstra_path_length(self.graph, sites[i], sites[i+1])
        return temp_route, temp_time

def 

def route_con (in_route):   #in_route is list of nodes 
    route = {}
    for i in range(len(in_route)-1):
        route[(in_route[i], in_route[i+1])] = graph_list[in_route[i]][in_route[i+1]][1]
    return route 

def route_distance(in_route):
    distance = 0
    for i in range(len(in_route)-1):
        distance += graph_list[in_route[i]][in_route[i+1]]
    return distance
    
    
def route_update(in_graph, in_route, new_node, sites, threshold):
    ori_path = networkx.dijkstra_path(in_graph, in_route[0], new_node)
    ori_time = networkx.dijkstra_path_length(in_graph, in_route[0], new_node)
    ori_dist = route_distance(ori_path)
    
    destination_path = networkx.dijkstra_path(in_graph, new_node, in_graph[-1])
    destination_time = networkx.dijkstra_path_length
    des_dist = route_distance(destination_path)
    updated_route = ori_path.extend(destination_path[1:])
    updated_time = ori_time + destination_time
    return updated_route, updated_time




arc_graph = networkx.Graph()
for i in graph_list.keys():
    for j in graph_list[i].keys():
        arc_graph.add_edge(i, j, weight = graph_list[i][j][0])



for origin in OD_pair.keys():
    for destination in OD_pair[origin].keys():
        path = networkx.dijkstra_path(arc_graph, origin, destination)
        path_dist = route_distance(path)
        if path_dist >= driving_range/2:   #exclude short routes from evaluation: consider them covered 
            path_time = networkx.dijkstra_path_length(arc_graph, origin, destination)
            OD_routes_sites[(origin, destination)] = [ path, path_dist, path_time, [], OD_pair[origin][destination]]
            
            
            gravity_list.append((OD_pair[origin][destination], (origin, destination), path_dist))
gravity_list.sort()
gravity_list.reverse()

target = gravity_list[0][1]

#find candidates 
#How to pick up deviation route candidate? 
        

    