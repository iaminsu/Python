"""
SA for Drone Mk8
From Mk7

Single warehouse: does not consider connectivity between warehouses 
So hard to be applied for multiple warehouse cases. 

Goal: improve solution quality 
Changes
1. Interchange algorithm 
- Relax critical node exemption 
- Removing candidates: cut the following branch if necessary 


"""

import pysal,  shapefile, networkx, time, cPickle, random, math, copy, Convexpath_module, datetime
from shapely.geometry import Point, Polygon, LineString, MultiPoint, MultiPolygon
from collections import defaultdict
from shapely.ops import cascaded_union

import sys
sys.path.append("F:\\Dropbox\\Python\\utils")


path = "F:\\Dropbox\\research\\Distance restricted covering model\\Locating recharging station\\Data_mk8\\"

path_results = "F:\\Dropbox\\research\\Distance restricted covering model\\Locating recharging station\\results_mk8\\"
obstacles_f = "obstacles_p"
demands_f = "sample_demand_2_p.shp"
facilities_f = "new_candis.shp"

ffDict = "FF_Dictnew_candis.shp_new_candis.shp_obstacles_p.shp.txt"
fdDict = "FD_Dictnew_candis.shp_sample_demand_2_p.shp_obstacles_p.shp.txt"
demand_Dict = "demands.txt"
ffcords = "FF_coords_Dict_new_candis.shp.txt"
wareDist = "w_distance_dict.txt"
f_fc_reverse = "FF_coords_reverse_new_candis.shp.txt"
version = "Mk8"



def generateGeometry(in_shp):
    """Using PySal, Load shp file obj and return Shapley obj"""
    resultingGeometry = []
    if in_shp.header['Shape Type'] == 1:
        for i in range(len(in_shp)):
            resultingGeometry.append(Point(in_shp.get_shape(i)['X'], in_shp.get_shape(i)['Y']))
    elif in_shp.header['Shape Type'] == 3:
        for i in range(len(in_shp)):
            resultingGeometry.append(LineString(in_shp.get_shape(i)['Vertices']))
    elif in_shp.header['Shape Type'] == 5:
        for i in range(len(in_shp)):
            resultingGeometry.append(Polygon(in_shp.get_shape(i)['Vertices']))
    return resultingGeometry    

    

def cal_obj(in_solution):
    """Calculate objective value without considering deviation ratio"""
    covered = []
    obj = 0 
    for site in in_solution:
        for i in F_Ddict[site]:
            covered.append(i[0])
        
    covered = list(set(covered))
    #print covered
    for de in covered:
        obj += float(dDict[de])
    return obj



def chk_isolation(in_sol, wh_ids):   
    #return false if sites are linked to any of warehouses 
    #assume that the system allows separate delivery network from each warehouse
    
    result = []
    for i in in_sol:
        if len(result) == 0:
            result.append(facil_shp[i].buffer(fd_fullPayload))
        else:
            result[0] = result[0].union(facil_shp[i].buffer(fd_fullPayload))    
    if result[0].type == "MultiPolygon":
        indi = True
        for poly in result[0]:
            indi_poly = False
            for warehouse in wh_ids:
                if poly.intersects(facil_shp[warehouse]):
                    indi_poly = True
            if indi_poly == False:
                indi = False
                break
        if indi == True:
            return False
        else:
            return True
                    
    else:
        return False
    
def delivery_network_mk2(in_solution, s_file, in_name = "temp_graph"):
    """
    Generate graph, does not check connectivity
    """
    arc_list = []
    arc_shp_list = []
    connectivity = True
    resultingGraph = networkx.Graph()
    for i in range(len(in_solution)-1):
        sites =  F_Fdict2[in_solution[i]].keys()
        for j in range(i+1, len(in_solution)):
            if in_solution[j] in sites:
                resultingGraph.add_edge((facil_shp[in_solution[i]].x, facil_shp[in_solution[i]].y), (facil_shp[in_solution[j]].x, facil_shp[in_solution[j]].y), weight = F_Fdict2[in_solution[i]][in_solution[j]])
                arc_list.append("ESP_" + str(in_solution[i]) + "_" + str(in_solution[j]) + ".shp")
    
    if s_file == True:
        for arc in arc_list:
            try:
                arc_pysal = pysal.IOHandlers.pyShpIO.shp_file(path+arc)
                arc_shp = generateGeometry(arc_pysal)
                arc_shp_list.extend(arc_shp)
            except IOError:
                a = arc[:-4].split("_")
                arc_shp_list.append(LineString([F_F_Coords_reverse[int(a[1])], F_F_Coords_reverse[int(a[2])]]))
        w = shapefile.Writer(shapefile.POLYLINE)
        w.field('nem')
        for line in arc_shp_list:
            w.line(parts=[[ list(x) for x in list(line.coords)]])
            w.record('chu')
        w.save(path_results + in_name)
    return resultingGraph

def delivery_network_mk3(in_solution, s_file, in_name = "temp_graph_mk3"):
    #check connectivity between warehouses 
    arc_list = []
    arc_shp_list = []
    connectivity = True
    resultingGraph = networkx.Graph()
    for i in range(len(in_solution)-1):
        sites = F_Fdict2[in_solution[i]].keys()
        for j in range(i+1, len(in_solution)):
            if in_solution[j] in sites:
                resultingGraph.add_edge((facil_shp[in_solution[i]].x, facil_shp[in_solution[i]].y), (facil_shp[in_solution[j]].x, facil_shp[in_solution[j]].y), weight = F_Fdict2[in_solution[i]][in_solution[j]])
                arc_list.append("ESP_" + str(in_solution[i]) + "_" + str(in_solution[j]) + ".shp")
    
    for i in range(len(warehouse_coords)-1):
        for j in range(i+1, len(warehouse_coords)):
            try:
                route = networkx.dijkstra_path(resultingGraph, warehouse_coords[i], warehouse_coords[j])
            except:
                connectivity = False
                break
        if connectivity == False:
            break
    
    if connectivity == True:
        if s_file == True:
            for arc in arc_list:
                try:
                    arc_pysal = pysal.IOHandlers.pyShpIO.shp_file(path+arc)
                    arc_shp = generateGeometry(arc_pysal)
                    arc_shp_list.extend(arc_shp)
                except IOError:
                    a = arc[:-4].split("_")
                    arc_shp_list.append(LineString([F_F_Coords_reverse[int(a[1])], F_F_Coords_reverse[int(a[2])]]))
            w = shapefile.Writer(shapefile.POLYLINE)
            w.field('nem')
            for line in arc_shp_list:
                w.line(parts=[[ list(x) for x in list(line.coords)]])
                w.record('chu')
            w.save(path_results + in_name)
        return resultingGraph
    else:
        return None
 

def restricted_cadidates_mk2(in_solution): 
    """
    Consider candidates within flight range of current set of solution 
    No minimum distant restriction 
    
    """
    candis = []
    for site in in_solution:
        a = F_Fdict2[site].keys()
        candis.extend(a)
    candis = list(set(candis))
    candis = [x for x in candis if x not in in_solution]
    return candis

def chk_feasibility(in_solution, save):
    feasibility = True
    covers = {}    
    for site in in_solution:
        if len(covers) == 0:
            covers[in_solution.index(site)] = facil_shp[site].buffer(fd_fullPayload)
        else:
            in_list = []
            for key in covers:
                if covers[key].intersects(facil_shp[site]):
                    in_list.append(key)
                    area = covers[key].union(facil_shp[site].buffer(fd_fullPayload))
                    covers[key] = area
            if len(in_list) == 0:
                covers[in_solution.index(site)] = facil_shp[site].buffer(fd_fullPayload)
            elif len(in_list) > 1: 
                
                chunk = covers[in_list[0]]
                for i in in_list:
                    chunk = chunk.union(covers[i])
                
                for i in in_list:
                    covers.pop(i)
                covers[in_solution.index(site)] = chunk
    for key in covers:
        indi = False
        for warehouse in warehouses_ID:
            if covers[key].intersects(facil_shp[warehouse]):
                indi = True
                break
        if indi == False:
            feasibility = False
    
    if save == True:
        w = shapefile.Writer(shapefile.POLYGON)
        w.field('net')
        for key in covers:
            w.poly(parts=[[list(x) for x in list(covers[key].exterior.coords)]])
            w.record('ff')
        w.save(path + "area")                       
    return feasibility

def chk_feasibility_all (in_solution, save):
    feasibility = True
    covers = {}    
    for site in in_solution:
        if len(covers) == 0:
            covers[in_solution.index(site)] = facil_shp[site].buffer(fd_fullPayload)
        else:
            in_list = []
            for key in covers:
                if covers[key].intersects(facil_shp[site]):
                    in_list.append(key)
                    area = covers[key].union(facil_shp[site].buffer(fd_fullPayload))
                    covers[key] = area
            if len(in_list) == 0:
                covers[in_solution.index(site)] = facil_shp[site].buffer(fd_fullPayload)
            elif len(in_list) > 1: 
                
                chunk = covers[in_list[0]]
                for i in in_list:
                    chunk = chunk.union(covers[i])
                
                for i in in_list:
                    covers.pop(i)
                covers[in_solution.index(site)] = chunk
    if len(covers) == 1:
        feasibility = True
    else:
        feasibility = False
    if save == True:
        w = shapefile.Writer(shapefile.POLYGON)
        w.field('net')
        for key in covers:
            w.poly(parts=[[list(x) for x in list(covers[key].exterior.coords)]])
            w.record('ff')
        w.save(path + "area")        
    return feasibility


def random_fill(in_solution=[]):
    isolation = True
    while isolation == True:
        new_sol = copy.copy(in_solution)
        while len(new_sol) < p:
            random_pool = restricted_cadidates_mk2(new_sol)
            new_sol.append(random.choice(random_pool))
        if chk_feasibility_all(new_sol, False):
            in_solution = []
            in_solution = copy.copy(new_sol)
            isolation = False
    return in_solution

def generate_graph(in_solution):
    arc_list = []
    arc_shp_list = []
    
    for i in range(len(in_solution)-1):
        sites =  F_Fdict2[in_solution[i]].keys()
        for j in range(i+1, len(in_solution)):
            if in_solution[j] in sites:
                arc_list.append("ESP_" + str(in_solution[i]) + "_" + str(in_solution[j]) + ".shp")
    resultingGraph = networkx.Graph()
    for arc in arc_list:
        try:
            arc_pysal = pysal.IOHandlers.pyShpIO.shp_file(path+arc)
            arc_shp = generateGeometry(arc_pysal)
            arc_shp_list.extend(arc_shp)
        except IOError:
            a = arc[:-4].split("_")
            arc_shp_list.append(LineString([F_F_Coords_reverse[int(a[1])], F_F_Coords_reverse[int(a[2])]]))
        for line in arc_shp:
            
            resultingGraph.add_edge(list(line.coords)[0], list(line.coords)[1], weight = line.length)
    w = shapefile.Writer(shapefile.POLYLINE)
    w.field('nem')
    for line in arc_shp_list:
        
        w.line(parts=[[ list(x) for x in list(line.coords)]])
        w.record('chu')
    w.save(path + "in_name")        
    return resultingGraph
def delivery_network(in_solution, s_file, in_name = "temp_graph"):
    #Generate graph
    #Check connectivity between warehouses
    #Check connectivity to each site 
    arc_list = []
    arc_shp_list = []
    connectivity = True
    resultingGraph = networkx.Graph()
    for i in range(len(in_solution)-1):
        sites =  F_Fdict2[in_solution[i]].keys()
        for j in range(i+1, len(in_solution)):
            if in_solution[j] in sites:
                resultingGraph.add_edge((facil_shp[in_solution[i]].x, facil_shp[in_solution[i]].y), (facil_shp[in_solution[j]].x, facil_shp[in_solution[j]].y), weight = F_Fdict2[in_solution[i]][in_solution[j]])
                arc_list.append("ESP_" + str(in_solution[i]) + "_" + str(in_solution[j]) + ".shp")

    for i in range(len(warehouse_coords)-1):
        for j in range(i+1, len(warehouse_coords)):
            try:
                route = networkx.dijkstra_path(resultingGraph, warehouse_coords[i], warehouse_coords[j])
            except:
                connectivity = False
                break
        if connectivity == False:
            break
    for site in in_solution:
        for whouse in warehouse_coords:
            try:
                route = networkx.dijkstra_path(resultingGraph, (facil_shp[site].x, facil_shp[site].y), whouse)
            except:
                connectivity = False
                break
        if connectivity == False:
            break
    
    if connectivity == True:
        if s_file == True:
            w = shapefile.Writer(shapefile.POLYLINE)
            w.field('nem')
            for line in arc_shp_list:
                
                w.line(parts=[[ list(x) for x in list(line.coords)]])
                w.record('chu')
            w.save(path + in_name)
        return resultingGraph
    else:
        return None
def greedy_fill(in_solution=[]):
    isolation = True
    tt = 0 
    
    while isolation == True:
        obj_time = 0 
        new_sol = [] 
        stime = time.time()
        new_sol = copy.copy(in_solution)
        c_obj = cal_obj(new_sol)
        loop_no = 0
        pool_len = 0 
        while len(new_sol) < p:
            loop_no += 1
            #print new_sol
            pool = restricted_cadidates_mk2(new_sol)
            pool_len += len(pool)
            temp = []
            stime_l = time.time()
            for i in pool:
                temp_obj = cal_obj(new_sol + [i])
                temp.append((temp_obj, i))
            etime_l = time.time()
            obj_time += etime_l - stime_l
            temp.sort()
            temp.reverse()
            c_obj = temp[0][0]
            new_sol = new_sol + [temp[0][1]]
        if delivery_network(new_sol, False) != None:
        #if chk_feasibility_all(new_sol, False):
            in_solution =[]
            in_solution = copy.copy(new_sol)
            isolation = False
        etime = time.time()
        tt += etime - stime
        if tt > 600: 
            print "greedy failed"
            print tt
            print new_sol
            nn = delivery_network_mk2(new_sol, True, "failed_greedy")
            chk_feasibility_all(new_sol, True)
            f = raw_input()        
    return in_solution

def greedy_fill_exampt(in_solution, exampt):
    isolation = True
    tt = 0 
    
    while isolation == True:
        obj_time = 0 
        new_sol = [] 
        stime = time.time()
        new_sol = copy.copy(in_solution)
        c_obj = cal_obj(new_sol)
        loop_no = 0
        pool_len = 0 
        while len(new_sol) < p:
            loop_no += 1
            #print new_sol
            pool = restricted_cadidates_mk2(new_sol)
            if exampt in pool:
                pool.remove(exampt)
            pool_len += len(pool)
            temp = []
            stime_l = time.time()
            for i in pool:
                temp_obj = cal_obj(new_sol + [i])
                temp.append((temp_obj, i))
            etime_l = time.time()
            obj_time += etime_l - stime_l
            temp.sort()
            temp.reverse()
            c_obj = temp[0][0]
            new_sol = new_sol + [temp[0][1]]
        if delivery_network(new_sol, False) != None:
        #if chk_feasibility_all(new_sol, False):
            in_solution =[]
            in_solution = copy.copy(new_sol)
            isolation = False
        etime = time.time()
        tt += etime - stime
        if tt > 600: 
            print "greedy failed"
            print tt
            print new_sol
            nn = delivery_network_mk2(new_sol, True, "failed_greedy")
            chk_feasibility_all(new_sol, True)
            f = raw_input()        
    return in_solution


def network_removal_mk3 (in_solution, removeSite):
    """
    Remove given site from in_solution 
    If it causes any isolated network segment, remove them as well. 
    
    """    
    new_sol = copy.copy(in_solution)
    new_sol.remove(removeSite)
    removed = []
    resultingGraph = networkx.Graph()
    for i in range(len(new_sol)-1):
        sites =  F_Fdict2[new_sol[i]].keys()
        if removeSite in sites:
            sites.remove(removeSite)
        for j in range(i+1, len(new_sol)):
            if new_sol[j] in sites:           
                resultingGraph.add_edge((facil_shp[new_sol[i]].x, facil_shp[new_sol[i]].y), (facil_shp[new_sol[j]].x, facil_shp[new_sol[j]].y), weight = F_Fdict2[new_sol[i]][new_sol[j]])
                
    for site in new_sol:
        try:
            route = networkx.dijkstra_path(resultingGraph, warehouse_coords[0], (facil_shp[site].x, facil_shp[site].y))
        except:
            removed.append(site)
    new_sol = [x for x in new_sol if x not in removed]
    return new_sol

def diff(list1, list2):
    """
    return removed and added elements 
    """
    removed = [x for x in list1 if x not in list2]
    added = [x for x in list2 if x not in list1]
    return removed, added
    
def shaker(in_solution):
    removed = random.choice(in_solution)
    new_sol = copy.copy(in_solution)
    network_removal_mk3(new_sol, removed)
    new_sol = random_fill(new_sol)
    return new_sol
    

def random_fill_mk2(in_candis):

    print "random fill mk2 start"
    isolation = True
    if len(in_candis) == 2:
        w_origin = facil_shp[in_candis[0]]
        w_destination = facil_shp[in_candis[1]]
        a = Convexpath_module.Convexpath_shapely(path, w_origin, w_destination, obstacles_shp)
        w_esp = a.esp  #esp is Linestring object
        w_corridor = w_esp.buffer(fd_delivery*0.5)
        
    else:
        w_points = []
        candis_coords = []
        for candi in in_candis:
            candis_coords.append((facil_shp[candi].x, facil_shp[candi].y))        
        for i in candis_coords:
            w_points.append(i)
        w_mp = MultiPoint(w_points)
        w_ch = w_mp.convex_hull
        w_cp = w_ch.centroid
        for obs in obstacles_shp:
            if obs.contains(w_cp):
                search_circle = w_cp.buffer(search_radius)
                for i in facil_shp:
                    if search_circle.contains(i):
                        w_cp = i
                        break
                break
        
        w_c_lines = []
        for i in candis_coords:
            a = Convexpath_module.Convexpath_shapely(path, Point(i), w_cp, obstacles_shp)
            w_c_lines.append(a.esp.buffer(fd_delivery * 0.5))
        w_corridor = cascaded_union(w_c_lines)        
    w = shapefile.Writer(shapefile.POLYGON)
    w.field('net')
    for obs in [w_corridor]:
        w.poly(parts=[[list(x) for x in list(obs.exterior.coords)]])
        w.record('ff')
    w.save(path_results + "w_corridor")      
    print "corridor"
    while isolation == True: 
        
        new_sol = []
        new_sol = copy.copy(in_candis)
        print new_sol
        while len(new_sol) < p:
            if chk_feasibility_all(new_sol, False) == False:
                random_pool = restricted_cadidates(new_sol)
                #print new_sol
                #print random_pool
                corridor_pool = []
                for i in random_pool:
                    if w_corridor.intersects(facil_shp[i]):
                        corridor_pool.append(i)
                if len(corridor_pool) != 0:
                    new_sol.append(random.choice(corridor_pool))
                else: 
                    new_sol.append(random.choice(random_pool))
            else:
                random_pool = restricted_cadidates(new_sol)
                new_sol.append(random.choice(random_pool))
        print new_sol
        if delivery_network(new_sol, False) != None:
            in_solution = []
            in_solution = copy.copy(new_sol)
            isolation = False
    return in_solution

def restricted_cadidates(in_solution):   #for spatial_interchange: 
    candis = []
    for site in in_solution:
        for i in F_Fdict2[site]:
            if F_Fdict2[site][i] > min_dist:
                candis.append(i)
    too_close = []
    for site in in_solution:
        too_close.extend(F_F_close_d[site])
    
        
    candis = list(set(candis))
    candis = [x for x in candis if x not in in_solution]
    candis = [x for x in candis if x not in too_close]
    return candis


def spatial_interchage_mk7(in_solution):
    """
    Non-Conventional interchange algorithm
    0. Calculate current objective value
    1. Pick one of the removable candiate sites (that is, except warehouse)
    2. If removal of the picked cause any isolated network segment, remove them as well 
    3. Greedy filling solution 
    4. Compare new objective value: if it's better, accept it 
    """
    current_obj = cal_obj(in_solution)
    removable_solution = [x for x in in_solution if x not in warehouses_ID]
    new_sets = []
    for site in removable_solution:
        t_sol = copy.copy(removable_solution)
        t_sol.extend(warehouses_ID)
        
        t_sol = network_removal_mk3(t_sol, site)
        print "removed"
        t_sol = greedy_fill_exampt(t_sol, site)
        print "filled"
        t_obj = cal_obj(t_sol)
        new_sets.append((t_obj, t_sol))
    new_sets.sort()
    new_sets.reverse()
    return new_sets[0][1]

f_FF = open(path + ffDict)
f_FD = open(path + fdDict)
ffcr = open(path + f_fc_reverse)
ware_dist = cPickle.load(open(path + wareDist))
f_demand = open(path + demand_Dict, 'rb')
F_Fdict = cPickle.load(f_FF)     
F_Fdict2 = defaultdict(dict)
F_F_Coords_reverse = cPickle.load(ffcr)
for i in F_Fdict:
    for j in F_Fdict[i]:
        F_Fdict2[i][j] = F_Fdict[i][j][0]


F_Ddict = cPickle.load(f_FD)
F_FCoords = cPickle.load(open(path+ ffcords))
facil_pysal = pysal.IOHandlers.pyShpIO.shp_file(path+facilities_f)
demand_pysal = pysal.IOHandlers.pyShpIO.shp_file(path + demands_f)
obstacles_pysal = pysal.IOHandlers.pyShpIO.shp_file(path + obstacles_f)

obstacles_shp = generateGeometry(obstacles_pysal)
dDict = cPickle.load(f_demand)
facil_shp = generateGeometry(facil_pysal)
demand_shp = generateGeometry(demand_pysal)
warehouses_ID = [1229]    #id_f of warehouses
warehouse_coords = []

for warehouse in warehouses_ID:
    warehouse_coords.append((facil_shp[warehouse].x, facil_shp[warehouse].y))
solution_sites = []
covered_demand = []
objective_value = 0   #initialize objective value 
p = 10  #number of stations to be sited including existing warehouses 
temperature = 30   #start temperature
max_iter = 3   #iteration limit
terminate_temp = 1         
temp_ratio = 0.15   
sa_count = 0
remove_percent = 0.2 
fd_fullPayload = 5 * 5280    #flight distance with full payload
fd_empty = 10 * 5280         #flight distance with empty payload 
fd_delivery = 3.33 *5280     #max flight distance for safe return after delivery 
search_radius = 2 * 5280 
min_dist = fd_delivery
rc = 0.001
rc_obj = 0.1
total_demand = 0.0 
dist_limit_ratio = 1.4



F_F_close_d = defaultdict(list)
for i in F_Fdict2:
    for j in F_Fdict2[i]:
        if F_Fdict2[j] <= min_dist:
            F_F_close_d[i].append(j)

for i in dDict:
    total_demand += float(dDict[i])

print "initializing solution"
start_time = time.time()
covered_list = []
for site in F_Ddict:
    covered_list.append((cal_obj([site]), site))
cl_filtered = []
cl_filtered.append(covered_list[0])
for i in range(1, len(covered_list)):
    for site in cl_filtered:
        if covered_list[i][1] in F_F_close_d[site[1]]:
            break
    else:
        cl_filtered.append(covered_list[i])
cl_filtered.sort()
cl_filtered.reverse()
top_candis = cl_filtered[0:int(p/2)]
top_c_dis = []
top_c_t = [x[1] for x in top_candis if x[1] not in warehouses_ID]
for site in top_c_t:
    a = Convexpath_module.Convexpath_shapely(path, facil_shp[warehouses_ID[0]], facil_shp[site], obstacles_shp)
    w_esp = a.esp
    top_c_dis.append((w_esp.length, site))
top_c_dis.sort()
top_c_dis.reverse()
top_c_dis = [x[1] for x in top_c_dis]
        
    

solution_sites.extend(warehouses_ID)
solution_sites.extend(top_c_dis[:2])
solution_sites = random_fill_mk2(solution_sites)   
solution_graph = delivery_network_mk2(solution_sites, True)
print "solution initialized"
history = []
history.append((cal_obj(solution_sites), solution_sites))
number = 0
while temperature > 0.5:
    current_solution = copy.copy(solution_sites)
    current_graph = delivery_network_mk2(current_solution, True, "currrent_graph")
    current_obj = cal_obj(current_solution)
    print "current Objective value: ", current_obj
    
    new_solution = copy.copy(current_solution)
    sstime = time.time()
    new_solution = spatial_interchage_mk7(new_solution)
    eetime = time.time()
    print "interchange time: " + str(eetime - sstime)
    new_graph = delivery_network_mk2(new_solution, True, "new_solution")
    new_obj = cal_obj(new_solution)
    print new_obj
    
    if new_obj > current_obj:
        solution_sites = new_solution
        sa_count = 0
        print "new better solution accepted"
        print new_solution
        history.append((new_obj, new_solution))
    elif new_obj == current_obj:
        new_solution = shaker(new_solution)
        new_obj = cal_obj(new_solution)
        print "shaking!"
        sa_count += 1
        print "SA COUNT: ", sa_count
        if random.random() < math.exp((new_obj - current_obj)*rc/temperature):
            solution_sites = new_solution
            print "new but bad objective: ", new_obj
            history.append((new_obj, new_solution))
            if sa_count >= max_iter:
                sa_count = 0
                temperature = temperature - (temperature * temp_ratio)
                print "new temperature: ", temperature
                if temperature < terminate_temp:
                    break                
        else:
            if sa_count >= max_iter:
                sa_count = 0
                temperature = temperature - (temperature * temp_ratio)
                print "new temperature: ", temperature
                if temperature < terminate_temp:
                    break              
    else:
        if sa_count >= max_iter:
            sa_count = 0
            temperature = temperature - (temperature * temp_ratio)
            print "new temperature: ", temperature
            if temperature < terminate_temp:
                break
        else:
            sa_count += 1
            print "SA COUNT: ", sa_count
            if random.random() < math.exp((new_obj - current_obj)*rc/temperature):
                solution_sites = new_solution
                print "new but bad objective: ", new_obj
                history.append((new_obj, new_solution))
                if sa_count >= max_iter:
                    sa_count = 0
                    temperature = temperature - (temperature * temp_ratio)
                    print "new temperature: ", temperature
                    if temperature < terminate_temp:
                        break                
            else:
                if sa_count >= max_iter:
                    sa_count = 0
                    temperature = temperature - (temperature * temp_ratio)
                    print "new temperature: ", temperature
                    if temperature < terminate_temp:
                        break                                    
end_time = time.time()
print "solution"                
solution_obj = cal_obj(solution_sites)

print "time: ", end_time - start_time
f_result = open(path_results + "result_" + version+ "_"+ str(p) + "_" + str(random.random()) + ".txt", "w")

f_result.write("P = " + str(p) + "\n")
f_result.write("Final solution: " + str(best_solution[0]) + "\n")
f_result.write("Objective value_r: " +  str(best_solution[1]) +"\n")
f_result.write("Covered population: " +  str(cal_obj(best_solution[0])) + "\n")    
f_result.write("time: " + str(end_time - start_time))
print "final solution: ", best_solution[0]
print "Objective value_r: ", best_solution[1]
print "Covered population: ", cal_obj(best_solution[0])
final_graph = delivery_network_mk2(best_solution[0], True, "final_solution" + str(p) + "_" + str(random.random()))


f_result.close()