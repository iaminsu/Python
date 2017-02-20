import networkx, time, cPickle, random, math, copy, arcpy
from collections import defaultdict




path_f = "F:\\Dropbox\\research\\DFRLM\\data\\FL\\"
path_data = 'F:\\data\\FL\\FL.gdb\\'
graph_list_f = "graph_list.txt"
OD_Pairs_f = "OD_pairs.txt"
driving_range = 160000   #in meters
distance_decay_f = 1.5 
threshold = 1.1
routes = "RoutesWithFlow"
routes_subset = "routes_subset"
arcs = "Arcs"
nodes = "nodes"

OD_pair = cPickle.load(open(path_f +OD_Pairs_f))
graph_list = cPickle.load(open(path_f + graph_list_f))

initial_sp = {}
gravity_list = []
short_gravity_list = []

OD_routes_sites = defaultdict(list)    #(O,D):[[routes], distance, time, [sites], flow] 
short_OD_routes = defaultdict(list)


class ODpair:
    def __init__(self, origin, destination):
        self.origin = origin
        self.destination = destination
        self.routes = []
        self.covered_flow = 0
        self.total_flow = OD_routes_sites[(origin, destination)][0][4]
        self.full_cover = False    #determine full cover, but it does not mean 100% cover. Based on given asuumption. 
    
    def newRoute(self, route):
        self.routes.append(route)
        self.covered_flow =+ route.covered_flow 
        if self.covered_flow == 1:
            self.full_cover = True

class refuelable_route:      #class for routes 
    def __init__(self, origin, destination, in_graph, sites = []):
        self.origin = origin
        self.destination = destination
        self.graph = in_graph
        self.covered_flow = 0   #percentage 
        self.total_flow = OD_routes_sites[(origin, destination)][0][4]
        self.shortest_route = OD_routes_sites[(origin, destination)][0][0]
        self.shortest_dist = OD_routes_sites[(origin, destination)][0][1]
        self.shortest_time = OD_routes_sites[(origin, destination)][0][2]
        self.sites = sites
        self.movement = []
        self.movement.append(origin)
        self.feasible = False 
        self.direction = self.destination
        
    def make_feasible(self):  
        #make the shortest path feasible by locating sites *on* the path
        #Check solution_sites and include already located facilities 
        self.sites = [x for x in solution_sites if x in self.shortest_route]
        location = self.origin
        
        while self.feasible == False:
            if location == self.origin:
                n_station = self.move_mk2(location, driving_range/2)
            else:
                n_station = self.move_mk2(location, driving_range)
            location = n_station
            if self.direction == self.origin:
                if n_station == self.origin:
                    continue
                else:
                    self.sites.append(n_station)
                    solution_sites.append(n_station)
            else:
                self.sites.append(n_station)
                solution_sites.append(n_station)
        self.covered_flow = 1

                        
    
    def test_feasible_mk2(self, new_sites = []):  #considering deviation, if feasible, update. 
        sites = new_sites
        
        temp_route = []
        temp_time = 0 
        temp_dist = 0
        if len(sites) == 1:
            ori_route = networkx.dijkstra_path(self.graph, self.origin, sites[-1])
            ori_dist = route_distance(ori_route)
            if  ori_dist > driving_range/2:
                return False
            else:
                des_route = networkx.dijkstra_path(self.graph, sites[-1], self.destination)
                des_dist = route_distance(des_route)
                if  des_dist > driving_range/2:
                    return False
                else:
                    self.shortest_dist = ori_dist + des_dist
                    ori_time = networkx.dijkstra_path_length(self.graph, self.origin, sites[-1])
                    des_time = networkx.dijkstra_path_length(self.graph, sites[-1], self.destination)
                    self.shortest_time = ori_time + des_time
                    self.shortest_route = ori_route + des_route[1:]
                    self.covered_flow = distance_decay([self.origin, self.destination], self.shortest_time)
                    return True
        else:
            ind = True
            for i in range(len(sites)):
                if i == 0:
                    t_route = networkx.dijkstra_path(self.graph, self.origin, sites[i])
                    t_dist = route_distance(t_route)
                    if  t_dist > driving_range/2:
                        ind = False
                        break
                    else:
                        temp_dist = t_dist
                        temp_route = t_route
                        temp_time = networkx.dijkstra_path_length(self.graph, self.origin, sites[i])
                    
                elif i == len(sites):
                    t_route = networkx.dijkstra_path(self.graph, sites[i], self.destination)
                    t_dist = route_distance(t_route)
                    if  t_dist > driving_range/2:
                        ind = False
                        break
                    else:
                        temp_dist += t_dist
                        temp_time += networkx.dijkstra_path_length(self.graph, sites[i], self.destination)
                        temp_route = temp_route + t_route[1:]
                        
                else:
                    t_route = networkx.dijkstra_path(self.graph, sites[i], sites[i+1])
                    t_dist = route_distance(t_route)
                    if  t_dist > driving_range:
                        ind = False
                        break
                    else:
                        temp_dist += t_dist
                        temp_time += networkx.dijkstra_path_length(self.graph, sites[i], sites[i+1])
                        temp_route = temp_route + t_route[1:]
            if ind == True:
                self.shortest_dist = temp_dist
                self.shortest_route = temp_route
                self.shortest_time = temp_time
                self.covered_flow = distance_decay([self.origin, self.destination], self.shortest_time)
                self.feasible = True
                self.sites = new_sites
            return ind
            
    def test_feasible(self, new_sites = []):  #considering deviation 
        sites = new_sites
        
        temp_route = []
        temp_time = 0 
        if len(sites) == 1:
            ori_route = networkx.dijkstra_path(self.graph, self.origin, sites[-1])
            if route_distance(ori_route) > driving_range/2:
                return False
            else:
                des_route = networkx.dijkstra_path(self.graph, sites[-1], self.destination)
                if route_distance(des_route) > driving_range/2:
                    return False
                else:
                    return True
        else:
            ind = True
            for i in range(len(sites)):
                if i == 0:
                    temp_route = networkx.dijkstra_path(self.graph, self.origin, sites[i])
                    if route_distance(temp_route) > driving_range/2:
                        ind = False
                        break
                elif i == len(sites):
                    temp_route = networkx.dijkstra_path(self.graph, sites[i], self.destination)
                    if route_distance(temp_route) > driving_range/2:
                        ind = False
                        break
                else:
                    temp_route = networkx.dijkstra_path(self.graph, sites[i], sites[i+1])
                    if route_distance(temp_route) > driving_range:
                        ind = False
                        break
            return ind        
        
            
    def move(self, start_node, distance):
        able = True
        location = start_node
        while able:
            if self.direction == self.destination:
                next_node = self.shortest_route[self.shortest_route.index(location) + 1]
                try:
                    moving = graph_list[location][next_node][1]
                except:
                    moving = graph_list[next_node][location][1]
                if moving <= distance:
                    distance -= moving
                    location = next_node
                    if location == self.direction:
                        self.direction = self.origin
                else:
                    able = False
            elif self.direction == self.origin:
                next_node = self.shortest_route[self.shortest_route.index(location) - 1]
                try:
                    moving = graph_list[location][next_node][1]
                except:
                    moving = graph_list[next_node][location][1]
                if moving <= distance:
                    distance -= moving
                    location = next_node
                    if location == self.direction:
                        self.feasible = True
                        able = False
                else:
                    able = False
        return location

    def move_mk2(self, start_node, distance):
        able = True
        location = start_node
        while able:
            if self.direction == self.destination:
                next_node = self.shortest_route[self.shortest_route.index(location) + 1]
                try:
                    moving = graph_list[location][next_node][1]
                except:
                    moving = graph_list[next_node][location][1]
                if moving <= distance:
                    if next_node in self.sites:
                        distance = driving_range
                    else:
                        distance -= moving
                    location = next_node
                    if location == self.direction:
                        self.direction = self.origin
                else:
                    able = False
            elif self.direction == self.origin:
                next_node = self.shortest_route[self.shortest_route.index(location) - 1]
                try:
                    moving = graph_list[location][next_node][1]
                except:
                    moving = graph_list[next_node][location][1]
                if moving <= distance:
                    if next_node in self.sites:
                        distance = driving_range
                    else:
                        distance -= moving
                    location = next_node
                    if location == self.direction:
                        self.feasible = True
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

def distance_decay(OD, new_time):
    total_flow = OD_routes_sites[(OD[0], OD[1])][0][4]
    initial_time = OD_routes_sites[(OD[0], OD[1])][0][2]
    deviation_ratio = new_time/initial_time
    if deviation_ratio > distance_decay_f:
        return 0
    else:
        rr = 2 - deviation_ratio
        return rr
    

def route_distance(in_route):
    distance = 0
    for i in range(len(in_route)-1):
        try:
            distance += graph_list[in_route[i]][in_route[i+1]][1]
        except:
            distance += graph_list[in_route[i+1]][in_route[i]][1]
    return distance
    


arc_graph = networkx.Graph()
for i in graph_list.keys():
    for j in graph_list[i].keys():
        arc_graph.add_edge(i, j, weight = graph_list[i][j][0])


#for origin in OD_pair.keys():
    #for destination in OD_pair[origin].keys():
        #path = networkx.dijkstra_path(arc_graph, origin, destination)
        #path_dist = route_distance(path)
        #if path_dist >= driving_range/4:   #exclude short routes from evaluation: consider them covered 
            #path_time = networkx.dijkstra_path_length(arc_graph, origin, destination)
            #OD_routes_sites[(origin, destination)].append([ path, path_dist, path_time, [], OD_pair[origin][destination]])
            #gravity_list.append((OD_pair[origin][destination], (origin, destination), path_dist))
        #else:
            #path_time = networkx.dijkstra_path_length(arc_graph, origin, destination)
            #short_OD_routes[(origin, destination)].append([ path, path_dist, path_time, [], OD_pair[origin][destination]])
            #short_gravity_list.append((OD_pair[origin][destination], (origin, destination), path_dist))
#f = open(path_f + "od_routes.txt", "w")
#cPickle.dump(OD_routes_sites, f)
#f.close()
#f = open(path_f + "gravity_list.txt", "w")
#cPickle.dump(gravity_list, f)
#f.close()
#f = open(path_f + "od_short_routes.txt", "w")
#cPickle.dump(short_OD_routes, f)
#f.close()
#f = open (path_f + "gravity_short_list.txt", "w")
#cPickle.dump(short_gravity_list, f)
#f.close()




#for origin in OD_pair.keys():
    #for destination in OD_pair[origin].keys():
        #path = networkx.dijkstra_path(arc_graph, origin, destination)
        #path_dist = route_distance(path)
        #path_time = networkx.dijkstra_path_length(arc_graph, origin, destination)
        #OD_routes_sites[(origin, destination)].append([ path, path_dist, path_time, [], OD_pair[origin][destination]])
        #gravity_list.append((OD_pair[origin][destination], (origin, destination), path_dist))
        
#f = open(path_f + "od_routes_full.txt", "w")
#cPickle.dump(OD_routes_sites, f)
#f.close()
#f = open(path_f + "gravity_list.txt_full", "w")
#cPickle.dump(gravity_list, f)
#f.close()


f = open(path_f + "od_routes.txt")
OD_routes_sites = cPickle.load(f)
f.close()

f = open(path_f + "gravity_list.txt")
gravity_list = cPickle.load(f)
f.close()

f = open(path_f + "od_short_routes.txt")
short_OD_routes = cPickle.load(f)
f.close()

f = open(path_f + "gravity_short_list.txt")
short_gravity_list = cPickle.load(f)
f.close()

full_OD_routes = {}
full_gravity_list = []
f = open(path_f + "od_routes_full.txt_full")
full_OD_routes  = cPickle.load(f)
f.close()
f = open(path_f + "gravity_list.txt_full")
full_gravity_list = cPickle.load(f)
f.close()


gravity_list.sort()
gravity_list.reverse()

target = gravity_list[0][1]
print target


#variables for heuristic 

p = 20    #number of refueling stations required 
routes_dict = {}
solution_sites = []    #located refuleing stations
for pair in OD_routes_sites:
    routes_dict[pair] = refuelable_route(pair[0], pair[1], arc_graph)



#find candidates 
#How to pick up deviation route candidate? 

#don't consider deviation in this stage         
a_route = refuelable_route(target[0], target[1], arc_graph)

#make the largest flow feasible without considering deviation 
a_route.make_feasible()
routes_dict[target] = ODpair(target[0], target[1])
routes_dict[target].newRoute(a_route)

#Considering only top 50% of OD_routes (excluding short routes)

route_lyr = "route_lyr"
node_lyr = "node_lyr"
arcpy.MakeFeatureLayer_management(path_data + routes_subset, route_lyr)
arcpy.MakeFeatureLayer_management(path_data + nodes, node_lyr)

#find any direct cover from new sites 
arcpy.SelectLayerByAttribute_management(node_lyr, 'NEW_SELECTION', '"IDF" = '+ str(a_route.sites[0]))
arcpy.SelectLayerByLocation_management(route_lyr, "INTERSECT", node_lyr)

for row in arcpy.da.SearchCursor(route_lyr, ["OID@", "origin", "destination"]):
    ori = row[1]
    des = row[2]
    temp_route = refuelable_route(ori, des, arc_graph)
    if temp_route.test_feasible_mk2(a_route.sites):
        routes_dict[row[1], row[2]] = ODpair(row[1], row[2])
        routes_dict[row[1], row[2]].newRoute(temp_route)
        

#Move to next uncovered largest flow? 


#Then when does start to consider the deviation? 

#How can we store mutiple routes for each OD pair...


#How can consider feasible detours? 
