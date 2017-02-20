import arcpy, cPickle
from collections import defaultdict


path = "F:\\data\\Netherland\\GDB4BP-SLOT.gdb\\"
pathInfo = "ShortestPathInfo"

#info_lyr = "info_lyr"
#arcpy.MakeFeatureLayer_management("F:\\data\Netherland\\GDB4BP-SLOT.gdb\\ShortestPathInfo", info_lyr)

#OD_pair_dict = defaultdict(dict)

#for row in arcpy.da.SearchCursor(path + pathInfo, ["ONode", "DNode", "Gravity"]):
    #if row[2] != None:
        #OD_pair_dict[int(row[0])][int(row[1])] = float(row[2])
    #else:
        #OD_pair_dict[int(row[0])][int(row[1])] = 0.0

#f = open("F:\\Dropbox\\research\\DFRLM\\data\\Netherland\\OD_pairs.txt",'w')
#cPickle.dump(OD_pair_dict, f)
#f.close()


#graph_dict = defaultdict(dict)
#arcs = "arcs_all"
#nodes = "nodes_all"
#arc_lyr = "arc_lyr"
#node_lyr = 'node_lyr'
#arcpy.MakeFeatureLayer_management(path + arcs, arc_lyr)
#arcpy.MakeFeatureLayer_management(path + nodes, node_lyr)
#for row in arcpy.da.SearchCursor(path + arcs, ["OID@", "FNode", "TNode", "Travel_Cost", "Shape_Length"]):
    #graph_dict[row[1]][row[2]] = (row[3], row[4])
    


###for row in arcpy.da.SearchCursor(path + arcs, ["OID@", "origin", "destination", "seconds", "Shape_Length"]):
###   graph_dict[row[1]][row[2]] = (row[3], row[4])
###   
###
#f = open("F:\\Dropbox\\research\\DFRLM\\data\\Netherland\\graph_list.txt",'w')
###
#cPickle.dump(graph_dict, f)
#f.close()
###    

#od = "OD"
#od_dict = {}
#for row in arcpy.da.SearchCursor(path + od, ["OID@", "NodeID"]):
    #od_dict[row[0]] = row[1]


route = "Routes"
route_lyr = "route_lyr"
arcpy.MakeFeatureLayer_management(path + route, route_lyr)
#with arcpy.da.UpdateCursor(route_lyr, ["FacilityID", "IncidentID", "origin", "destination"]) as cursor:
    #for row in cursor:
        #row[2] = od_dict[row[0]]
        #row[3] = od_dict[row[1]]
        #cursor.updateRow(row)
        
        
path_f = "F:\\Dropbox\\research\\DFRLM\\data\\Netherland\\"

f = open(path_f + "od_routes_full.txt")
OD_routes_sites = cPickle.load(f)
with arcpy.da.UpdateCursor(route_lyr, ["origin", "destination", "gravity"]) as cursor:
    for row in cursor:
        row[2] = OD_routes_sites[(row[0], row[1])]
        cursor.updateRow(row)
            
            