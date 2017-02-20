import networkx, time, cPickle, random, math, copy, arcpy
from collections import defaultdict
from arcpy import env


#Mk3: No deviation at all
#Mk4: Deviation 

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
voronoi = "voronoi"
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
        self.deviation_route = []
        self.deviation_time = 0
        self.sites = []    #These are stations that can serve this route. 
        self.feasible = False 
        self.direction = self.destination

    def makeDeviation(self, devi_sites = []):
        #check feasiblity with given stations: deviation stations are given, so this function only determines feasibility and 
        #demand coverage of given deviation stations 
        
        #feasiblity of deviation route:
        # 1) refuelable 
        # 2) within maximum deviation threshold 
        #If feasible, compare it to existing deviation route
        # 1) if none exist, designate it
        # 2) if existing route covers less demand, update it to new one. Otherwise, ignore new one 
        
        #How do determine the order of devi_site? 
        #How do consider configuration with already located sites on the shortest path?
        sts = devi_sites + self.sites
        d_list = []
        d_route = []
        for site in sts:
            r = networkx.dijkstra_path_length(self.graph, self.origin, site)
            d_list.append(r, site)
        d_list.sort()
        if len(d_list) == 1:
            r = networkx.dijkstra_path(self.graph, self.origin, d_list[0][1])
            r_dist = route_distance(r)
            if r_dist > driving_range/2:
                return False
            else:
                r_2 = networkx.dijkstra_path(self.graph, d_list[0][1], self.destination)
                r_2_dist = route_distance(r_2)
                if r_2_dist > driving_range/2:
                    return False
                else:
                    d_route.extend(r)
                    d_route.extend(r_2[1:])
                    return d_route
        else:
            for i in len(d_list):
                if i == 0:  #from origin to first station 
                    r = networkx.dijkstra_path(self.graph, self.origin, d_list[i][1])
                    r_dist = route_distance(r)
                    if r_dist > driving_range/2:
                        return False
                    else:
                        d_route.extend(r)
                elif i == (len(d_list) -1):  #from previous station to last station & from last station to destination 
                    r = networkx.dijkstra_path(self.graph, d_list[i-1][1], d_list[i][1])
                    r_dist = route_distance(r)
                    if r_dist > driving_range:
                        return False
                    else:
                        d_route.extend(r[1:])
                        r2 = networkx.dijkstra_path(self.graph, d_list[i][1], self.destination)
                        r2_dist = route_distance(r2)
                        if r2_dist > driving_range/2:
                            return False
                        else:
                            d_route.extend(r2[1:])
                else:  #from previous station to this station 
                    r = networkx.dijkstra_path(self.graph, d_list[i-1])
                    r_dist = route_distance(r)
                    if r_dist > driving_range:
                        return False
                    else:
                        d_route.extend(r[1:])
   
        d_time = route_time(d_route)
        if self.deviation_time == 0:
            if d_time < threshold * self.shortest_time:
                self.deviation_route = d_route
                self.deviation_time = d_time
                for site in devi_sites:
                    self.addStation(site)
                self.covered_flow = self.demand_decay()
        else:
            if d_time < threshold * self.shortest_time:
                if d_time < self.deviation_time:
                    self.deviation_route = d_route
                    self.deviation_time = d_time
                    for site in devi_sites:
                        self.addStation(site)
                    self.covered_flow = self.demand_decay()
                    
                
    def demand_decay(self):
        d = self.deviation_time - self.shortest_time
        return self.total_flow - self.total_flow * (d/self.shortest_time)
            
    def makeFeasible(self):
        if self.updateStatus() == False:
            location = self.origin
            self.updateStations()
            while self.feasible == False:
                if location == self.origin:
                    n_result = self.move(location, driving_range/2)
                else:
                    n_result = self.move(location, driving_range)
                if n_result[1] == True:
                    self.feasible = True
                    self.covered_flow = 1
                else:
                    self.sites.append(n_result[0])
                    solution_stations.addSolution(n_result[0])
                    location = n_result[0]
        else:
            self.feasible = True
            self.covered_flow = 1



    def updateStatus(self):
        result = self.move(self.origin, driving_range/2)
        #print result
        if result[1] == True:
            self.direction = self.destination
            return True
        else:
            self.direction = self.destination
            return False

    def updateStations(self):
        additional = [x for x in solution_stations.solution_sites if x in self.shortest_route]
        additional = [x for x in additional if not x in self.sites]
        self.sites.extend(additional)

    def testFeasible(self, test_sites):
        result = self.move(self.origin, driving_range/2, test_sites)
        self.direction = self.destination
        return result[1]

    def updateCoveredFlow(self, dd):
        #for deviation route 
        pass 

    def addStation(self, new_station):
        if new_station in self.sites:
            raise Exception("Duplication")
        else:
            self.sites.append(new_station)

    def move(self, start_node, distance, new_station = []):
        stations = self.sites + new_station
        if start_node in stations:
            distance = driving_range
        total_route = self.shortest_route
        able = True
        location = start_node
        arrived_origin = False
        movement = []
        movement.append(start_node)
        while able:
            if self.direction == self.destination:
                next_node = total_route[total_route.index(location)+1]
                try:
                    moving = graph_list[location][next_node][1]
                except:
                    moving = graph_list[next_node][location][1]
                if moving <= distance:
                    if next_node in stations:
                        distance = driving_range
                    else:
                        distance = distance - moving
                    location = next_node
                    movement.append(next_node)
                    if next_node == self.destination:
                        self.direction = self.origin
                else:	
                    able = False
                    continue
            elif self.direction == self.origin:
                next_node = total_route[total_route.index(location)-1]
                try:
                    moving = graph_list[location][next_node][1]
                except:
                    moving = graph_list[next_node][location][1]	
                if moving <= distance:
                    if next_node in stations:
                        distance = driving_range
                    else:
                        distance = distance - moving
                    location = next_node
                    movement.append(next_node)
                    if next_node == self.origin:
                        self.direction = self.destination    #direction reset 
                        arrived_origin = True
                        able = False
                        continue
                else:
                    able = False
                    continue
        return location, arrived_origin






def route_distance(in_route):
    distance = 0
    for i in range(len(in_route)-1):
        try:
            distance += graph_list[in_route[i]][in_route[i+1]][1]
        except:
            distance += graph_list[in_route[i+1]][in_route[i]][1]
    return distance

def route_time(in_route):
    t = 0.0
    for i in range(len(in_route)-1):
        try:
            t += graph_list[in_route[i]][in_route[i+1]][0]
        except:
            t += graph_list[in_route[i+1]][in_route[i]][0]
    return t


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

p = 1    #number of refueling stations required 
routes_dict = defaultdict(list)
solution_stations = Solution()
fully_covered = []
for pair in OD_routes_sites:
    routes_dict[pair].append(Refuelable_route(pair[0], pair[1], arc_graph))

#initial greedy solution 
route_lyr = "route_lyr"
node_lyr = "node_lyr"
OD_lyr = "OD_lyr"
voro_lyr = "vorno_lyr"
arcpy.MakeFeatureLayer_management(path_data + ODs, OD_lyr)
arcpy.MakeFeatureLayer_management(path_data + routes, route_lyr)
arcpy.MakeFeatureLayer_management(path_data + nodes, node_lyr)
arcpy.MakeFeatureLayer_management(path_data + voronoi, voro_lyr)
while len(solution_stations.solution_sites) < p:
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
                    temp_route = Refuelable_route(row[1], row[2], arc_graph)

                    if temp_route.testFeasible([site]):
                        covered += temp_route.total_flow
            
            covered_flow.append((covered, site))

        covered_flow.sort()
        covered_flow.reverse()
        if covered_flow[0][0] == 0:
            routes_dict[target][0].makeFeasible()
            fully_covered.append(target)
            print "Zero"
            #raise Exception("0 Flow")
        else:
            routes_dict[target][0].covered_flow = 1
            routes_dict[target][0].addStation(covered_flow[0][1])
            solution_stations.addSolution(covered_flow[0][1])

            fully_covered.append(target)
            arcpy.SelectLayerByAttribute_management(node_lyr, 'NEW_SELECTION', '"IDF" = '+ str(covered_flow[0][1]))
            arcpy.SelectLayerByLocation_management(route_lyr, "INTERSECT", node_lyr)
            for row in arcpy.da.SearchCursor(route_lyr, ["OID@", "origin", "destination"]):
                ori = row[1]
                des = row[2]  

                if (ori, des) != target:
                    if (ori, des) not in fully_covered:
                        if routes_dict[(ori, des)][0].testFeasible([covered_flow[0][1]]):
                            fully_covered.append((ori, des))
                            a = routes_dict[(ori, des)][0]
                            a.feasible = True
                            a.covered_flow = 1
                            a.addStation(covered_flow[0][1])
                            gravity_list.remove((a.total_flow, (a.origin, a.destination)))
                        else:  #not feasible but add stations to routes 
                            routes_dict[(ori, des)][0].addStation(covered_flow[0][1])

    else:
        #If the length of the route is longer
        routes_dict[target][0].makeFeasible()
        fully_covered.append(target)
        contacts = []
        candidates = [x for x in routes_dict[target][0].sites if not x in solution_stations.solution_sites]
        for site in candidates:
            arcpy.SelectLayerByAttribute_management(node_lyr, 'NEW_SELECTION', '"IDF" = '+ str(site))
            arcpy.SelectLayerByLocation_management(route_lyr, "INTERSECT", node_lyr)
            for row in arcpy.da.SearchCursor(route_lyr, ["OID@", "origin", "destination"]):
                if (row[1], row[2]) == target:
                    continue
                elif (row[1], row[2]) in fully_covered:
                    continue
                else:
                    routes_dict[(row[1], row[2])][0].addStation(site)
                    contacts.append((row[1], row[2]))
        for r_pair in contacts:
            if routes_dict[r_pair][0].updateStatus():
                fully_covered.append(r_pair)
                a = routes_dict[(r_pair)][0]
                a.covered_flow = 1
                a.feasible = True
                gravity_list.remove((a.total_flow, (a.origin, a.destination)))

    #Make deviation routes uring current solution 
    gravity_list.remove(gravity_list[0]) 
print solution_stations.solution_sites
covered_demand = 0            
for i in fully_covered:
    covered_demand += routes_dict[i][0].total_flow
print covered_demand
print fully_covered

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