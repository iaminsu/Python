import networkx, time, cPickle, random, math, copy, arcpy
from collections import defaultdict
from arcpy import env



path_f = "F:\\Dropbox\\research\\DFRLM\\data\\FL\\"
path_data = 'F:\\data\\FL\\FL.gdb\\'
graph_list_f = "graph_list.txt"
OD_Pairs_f = "OD_pairs.txt"
driving_range = 160000   #in meters
distance_decay_f = 1.5 
threshold = 1.1
routes = "routes_no0"
routes_temp = "routes_temp"
routes_subset = "routes_subset"
arcs = "Arcs"
nodes = "nodes"
ODs = "OD"
env.overwriteOutput = True
OD_pair = cPickle.load(open(path_f +OD_Pairs_f))
graph_list = cPickle.load(open(path_f + graph_list_f))

initial_sp = {}
gravity_list = []
short_gravity_list = []

OD_routes_sites = defaultdict(list)    #(O,D):[[routes], distance, time, [sites], flow] 
short_OD_routes = defaultdict(list)


class Solution:
    def __init__(self):
	self.solution_sites = []
    def addSolution(self, new_site):
	if new_site in self.solution_sites:
	    raise Exception("Overallped solution")
	else:
	    self.solution_sites.append(new_site)
    
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

class Refuelable_route:      #class for routes 
    def __init__(self, origin, destination, in_graph):
        self.origin = origin
        self.destination = destination
        self.graph = in_graph
        self.covered_flow = 0   #percentage 
        self.total_flow = OD_routes_sites[(origin, destination)][0][4]
        self.shortest_route = OD_routes_sites[(origin, destination)][0][0]
        self.shortest_dist = OD_routes_sites[(origin, destination)][0][1]
        self.shortest_time = OD_routes_sites[(origin, destination)][0][2]
        self.sites = []    #These are stations that can serve this route. 
        self.feasible = False 
        self.direction = self.destination

        
    def make_feasible(self):  
        #make the shortest path feasible by locating sites *on* the path
        #Check solution_sites and include already located facilities 
        #In this case, the order of the stations does not matter (move function). 
	self.direction = self.destination
        if self.updateStatus() == False:
	    self.sites = [x for x in solution_stations.solution_sites if x in self.shortest_route]
	    location = self.origin
	    while self.feasible == False:
		n_station = self.move_mk2(location, driving_range/2)
		if self.direction == self.origin:
		    if n_station == self.origin:
			self.feasible == True
			continue
		else:
		    self.sites.append(n_station)
		    solution_stations.addSolution(n_station)
		    
	    self.covered_flow = 1

                        
    
    def updateStatus (self):
	self.direction = self.destination
        if self.move_mk2(self.origin, driving_range/2) == self.origin:
            if self.direction == self.origin:
                self.covered_flow = 1
                return True
            else:
                return False
        else:
            return False
    
    
    def test_feasible_mk2(self, new_sites = []):  
        
        #if feasible, update. 
	#Only for direct routes 
        
        t_sites = self.sites + new_sites
	self.direction = self.destination
	if self.move_mk2(self.origin, driving_range/2, t_sites) == self.origin:
	    if self.destination == self.origin:
		self.covered_flow = 1
		self.sites = t_sites
		return True


    def move_mk2(self, start_node, distance, stations =[]):
	if len(stations) == 0:
	    stations = self.sites
        able = True
        location = start_node
	if start_node in stations:
	    distance = driving_range
        while able:
            if self.direction == self.destination:
                next_node = self.shortest_route[self.shortest_route.index(location) + 1]
		
                try:
                    moving = graph_list[location][next_node][1]
                except:
                    moving = graph_list[next_node][location][1]
                if moving <= distance:
                    if next_node in stations:
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
		    if next_node == self.direction:
			able = False
		    else:
			if next_node in stations:
			    distance = driving_range
			else:
			    distance -= moving
			location = next_node

                else:
                    able = False
        return location
          

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
        #gravity_list.append((OD_pair[origin][destination], (origin, destination)))
        
#f = open(path_f + "od_routes_full.txt", "w")
#cPickle.dump(OD_routes_sites, f)
#f.close()
#f = open(path_f + "gravity_list.txt_full", "w")
#cPickle.dump(gravity_list, f)
#f.close()


#f = open(path_f + "od_routes.txt")
#OD_routes_sites = cPickle.load(f)
#f.close()

#f = open(path_f + "gravity_list.txt")
#gravity_list = cPickle.load(f)
#f.close()

#f = open(path_f + "od_short_routes.txt")
#short_OD_routes = cPickle.load(f)
#f.close()

#f = open(path_f + "gravity_short_list.txt")
#short_gravity_list = cPickle.load(f)
#f.close()


full_gravity_list = []
f = open(path_f + "od_routes_full.txt")
OD_routes_sites = cPickle.load(f)
f.close()
f = open(path_f + "gravity_list.txt_full")
gravity_list = cPickle.load(f)
f.close()


gravity_list.sort()
gravity_list.reverse()
#full_gravity_list.sort()
#full_gravity_list.reverse()


#variables for heuristic 

p = 20    #number of refueling stations required 
routes_dict = defaultdict(list)
solution_stations = Solution()
fully_covered = []
for pair in OD_routes_sites:
    routes_dict[pair].append(Refuelable_route(pair[0], pair[1], arc_graph))

#initial greedy solution 
route_lyr = "route_lyr"
node_lyr = "node_lyr"
OD_lyr = "OD_lyr"
arcpy.MakeFeatureLayer_management(path_data + ODs, OD_lyr)
arcpy.MakeFeatureLayer_management(path_data + routes, route_lyr)
arcpy.MakeFeatureLayer_management(path_data + nodes, node_lyr)

while len(solution_stations.solution_sites) < 20:
    #pick the largest flow OD from uncovered 
    #partially covered routes: how to consider them?? 
    target = gravity_list[0][1]
    print target
    print gravity_list[0]
    
    #Check length of the route. 
    #IF the length is shorter than 1/4 of driving range, which means it can be feasible with any node on its route
    #Evaluate only direct cover. Deviation evaluation will make this very inefficient sudo-exact approache 
    if OD_routes_sites[target][0][1] < driving_range/4:
        candidates = [x for x in routes_dict[target][0].shortest_route if not x in solution_stations.solution_sites]
	
        covered_flow = []
	eval_routes = []
	failed_routes = []
        for site in candidates:
            covered = 0
            #evaluate for being on the shortest path 
            arcpy.SelectLayerByAttribute_management(node_lyr, 'NEW_SELECTION', '"IDF" = '+ str(site))
            arcpy.SelectLayerByLocation_management(route_lyr, "INTERSECT", node_lyr)
            for row in arcpy.da.SearchCursor(route_lyr, ["OID@", "origin", "destination"]):
		if (row[1], row[2]) == target:
		    continue
		elif (row[1], row[2]) in fully_covered:
		    continue
		else:
		    eval_routes.append((row[1], row[2]))
		    temp_route = Refuelable_route(row[1], row[2], arc_graph)
		    
		    if temp_route.test_feasible_mk2([site]):
			covered += temp_route.total_flow
		    else:
			failed_routes.append((row[1], row[2]))
		
            covered_flow.append((covered, site))
            
        covered_flow.sort()
        covered_flow.reverse()
	if covered_flow[0][0] == 0:
	    raise Exception("0 Flow")
        routes_dict[target][0].covered_flow = 1
        routes_dict[target][0].sites = [covered_flow[0][1]]
	solution_stations.addSolution(covered_flow[0][1])
        
        fully_covered.append(target)
        arcpy.SelectLayerByAttribute_management(node_lyr, 'NEW_SELECTION', '"IDF" = '+ str(covered_flow[0][1]))
        arcpy.SelectLayerByLocation_management(route_lyr, "INTERSECT", node_lyr)
        for row in arcpy.da.SearchCursor(route_lyr, ["OID@", "origin", "destination"]):
            ori = row[1]
            des = row[2]  
	   
	    if (ori, des) != target:
		if routes_dict[(ori, des)][0].test_feasible_mk2([covered_flow[0][1]]):
		    fully_covered.append((ori, des))
		    a = routes_dict[(ori, des)][0]
		    gravity_list.remove((a.total_flow, (a.origin, a.destination)))
		else:  #not feasible but add stations to routes 
		    routes_dict[(ori, des)][0].sites.append(covered_flow[0][1])
		    
    else:
        #If the length of the route is longer
        routes_dict[target][0].make_feasible()
        contacts = []
        for site in routes_dict[target][0].sites:
            arcpy.SelectLayerByAttribute_management(node_lyr, 'NEW_SELECTION', '"IDF" = '+ str(site))
            arcpy.SelectLayerByLocation_management(route_lyr, "INTERSECT", node_lyr)
            for row in arcpy.da.SearchCursor(route_lyr, ["OID@", "origin", "destination"]):
		if (row[1], row[2]) == target:
		    continue
		elif (row[1], row[2]) in fully_covered:
		    continue
		else:
		    routes_dict[(row[1], row[2])][0].sites.append(site)
		    contacts.append((row[1], row[2]))
        for r_pair in contacts:
	   
            if routes_dict[r_pair][0].updateStatus():
		
                fully_covered.append((r_pair))
		a = routes_dict[(ori, des)][0]
		gravity_list.remove((a.total_flow, (a.origin, a.destination)))
		
    #Make deviation routes uring current solution 
    gravity_list.remove(gravity_list[0]) 
print solution_stations.solution_sites
covered_demand = 0            
for i in fully_covered:
    covered_demand += routes_dict[i][0].total_flow
print covered_demand

#if a candidate makes feasible detour for given OD pair, create new route with it. 
            
#make a copy of current route 
            



#find candidates 
#How to pick up deviation route candidate? 

#don't consider deviation in this stage         
#a_route = refuelable_route(target[0], target[1], arc_graph)

##make the largest flow feasible without considering deviation 
#a_route.make_feasible()
#routes_dict[target] = ODpair(target[0], target[1])
#routes_dict[target].newRoute(a_route)

##Considering only top 50% of OD_routes (excluding short routes)

#route_lyr = "route_lyr"
#node_lyr = "node_lyr"
#arcpy.MakeFeatureLayer_management(path_data + routes_subset, route_lyr)
#arcpy.MakeFeatureLayer_management(path_data + nodes, node_lyr)

##find any direct cover from new sites 
#arcpy.SelectLayerByAttribute_management(node_lyr, 'NEW_SELECTION', '"IDF" = '+ str(a_route.sites[0]))
#arcpy.SelectLayerByLocation_management(route_lyr, "INTERSECT", node_lyr)

#for row in arcpy.da.SearchCursor(route_lyr, ["OID@", "origin", "destination"]):
    #ori = row[1]
    #des = row[2]
    #temp_route = refuelable_route(ori, des, arc_graph)
    #if temp_route.test_feasible_mk2(a_route.sites):
        #routes_dict[row[1], row[2]] = ODpair(row[1], row[2])
        #routes_dict[row[1], row[2]].newRoute(temp_route)
        

##Move to next uncovered largest flow? 


##Then when does start to consider the deviation? 

##How can we store mutiple routes for each OD pair...


##How can consider feasible detours? 



##evlaute for deviation path
##find relevant OD pairs for given site --> HOW??? Need more filter rather than simple proximity evalution 


#arcpy.SelectLayerByLocation_management(route_lyr, "WITHIN_A_DISTANCE", node_lyr, 40000)
#arcpy.SelectLayerByLocation_management(OD_lyr, "WITHIN_A_DISTANCE", node_lyr, 40000)
#od_list = []
#for row in arcpy.da.SearchCursor(OD_lyr, ["OID@"]):
    #od_list.append(row[0])
#st =""
#for i in od_list:
    #st += " OR \"origin\" = " + str(i)            
    #st += " OR \"destination\" = " + str(i)
#st = st[3:]
##select routes that 1) within 40km from station & 2) have origin or destination that within 40km from station
#arcpy.SelectLayerByAttribute_management(route_lyr, 'SUBSET_SELECTION', st)
#for row in arcpy.da.SearchCursor(route_lyr, ["origin","destination"]):
    ##deviation route
    #current_sites = routes_dict[(row[0], row[1])].sites
    #potential_sites = []
    #t_route_lyr = "t_route_lyr"
    #t_station_lyr = "t_station_lyr"
    #arcpy.MakeFeatureLayer_management(path_data + routes, t_route_lyr)
    #arcpy.MakeFeatureLayer_management(path_data + nodes, t_station_lyr)
    #arcpy.SelectLayerByAttribute_management(t_route_lyr, 'NEW_SELECTION', '"origin" = '+ str(self.origin) + " AND " + '"destination" = ' + str(self.destination))
    #arcpy.SelectLayerByLocation_management(t_station_lyr, "WITHIN_A_DISTANCE", t_route_lyr, 40000)
    #for row2 in arcpy.da.SearchCursor(t_station_lyr, ["IDF"]):
	#if row2[0] in solution_sites:
	    #potential_sites.append(row2[0])
    #potential_sites.append(site)
    
    
    #temp_route = refuelable_route(row[0], row[1], arc_graph)
