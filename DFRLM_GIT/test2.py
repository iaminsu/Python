import arcpy, cPickle
from collections import defaultdict

path = 'F:\\data\\FL\\FL.gdb\\'
routes = "routes_newFlow"
OD_pair_dict = defaultdict(dict)


route_lyr = "route_lyr"
arcpy.MakeFeatureLayer_management(path + routes, route_lyr)

for row in arcpy.da.SearchCursor(path + routes, ["OID@", "Name", "Gravity_1"]):
   s = str(row[1]).split("-")
   s1 = [x.split('Location') for x in s]
   OD_pair_dict[int(s1[0][1])][int(s1[1][1])] = int(row[2])
   arcpy.SelectLayerByAttribute_management(route_lyr, 'NEW_SELECTION', '"OBJECTID" = '+ str(row[0]))
   with arcpy.da.UpdateCursor(route_lyr, ["origin", "destination"]) as cursor:
      for row2 in cursor:
         row2[0] = int(s1[0][1])
         row2[1] = int(s1[1][1])
         cursor.updateRow(row2)

ff = open("F:\\Dropbox\\research\\DFRLM\\data\\FL\\OD_pairs.txt",'w')
cPickle.dump(OD_pair_dict, ff)
ff.close()


arcs = "Arcs"
nodes = "nodes"
##arc_lyr = "arc_lyr"
node_lyr = 'node_lyr'
##arcpy.MakeFeatureLayer_management(path + arcs, arc_lyr)
##arcpy.MakeFeatureLayer_management(path + nodes, node_lyr)
##for row in arcpy.da.SearchCursor(path + arcs, ["OID@", "origin", "destination"]):
##    arcpy.SelectLayerByAttribute_management(arc_lyr, 'NEW_SELECTION', '"OBJECTID" = '+ str(row[0]))
##    arcpy.SelectLayerByLocation_management(node_lyr, "INTERSECT", arc_lyr)
##    nodelist = []
##    for row1 in arcpy.da.SearchCursor(node_lyr, ["IDF"]):
##        
##        nodelist.append(row1[0])
##    if len(nodelist) != 2:
##        print row
##    else:
##        with arcpy.da.UpdateCursor(arc_lyr, ["origin", "destination"]) as cursor:
##            for row2 in cursor:
##                row2[0] = nodelist[0]
##                row2[1] = nodelist[1]
##                cursor.updateRow(row2)
            
##

##graph_dict = defaultdict(dict)
##for row in arcpy.da.SearchCursor(path + arcs, ["OID@", "origin", "destination", "seconds", "Shape_Length"]):
##   graph_dict[row[1]][row[2]] = (row[3], row[4])
##   
##
##f = open("F:\\Dropbox\\research\\DFRLM\\data\\FL\\graph_list.txt",'w')
##
##cPickle.dump(graph_dict, f)
##f.close()
##    
###pick nodes within half of driving distance 
##node_lyr2 = "node_lyr2"
##arcpy.MakeFeatureLayer_management(path + nodes, node_lyr2)
##nodes_160000 = defaultdict(list)
##nodes_80000 = defaultdict(list)
##for node in arcpy.da.SearchCursor(path + nodes, ["IDF"]):
##    arcpy.SelectLayerByAttribute_management(node_lyr, 'NEW_SELECTION', '"IDF" = '+ str(node[0]))
##    arcpy.SelectLayerByLocation_management(node_lyr2, "WITHIN_A_DISTANCE", node_lyr, 80000)
##    for node1 in arcpy.da.SearchCursor(node_lyr2, ["IDF"]):
##        nodes_80000[node[0]].append(node1[0])
##    arcpy.SelectLayerByLocation_management(node_lyr2, "WITHIN_A_DISTANCE", node_lyr, 160000)
##    for node1 in arcpy.da.SearchCursor(node_lyr2, ["IDF"]):
##        nodes_160000[node[0]].append(node1[0])       
##f = open("F:\\Dropbox\\research\\DFRLM\\data\\FL\\nodes_160000.txt",'w')
##cPickle.dump(nodes_160000, f)
##f.close()
##f = open("F:\\Dropbox\\research\\DFRLM\\data\\FL\\nodes_80000.txt",'w')
##cPickle.dump(nodes_80000, f)
##f.close()
