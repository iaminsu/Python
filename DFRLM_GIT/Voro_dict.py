import arcpy, cPickle
from collections import defaultdict



path = 'F:\\data\\FL\\FL.gdb\\'
pathInfo = "ShortestPathInfo"
path_f = "F:\\Dropbox\\research\\DFRLM\\data\\FL\\"

voro = "voronoi"
route= "routes_no0"

voro_lyr = "voro_ly"
route_lyr = "routel"

arcpy.MakeFeatureLayer_management(path + voro, voro_lyr)
arcpy.MakeFeatureLayer_management(path + route, route_lyr)

voro_dict = defaultdict(list)
for row in arcpy.da.SearchCursor(voro_lyr, ["OID@"]):
    arcpy.SelectLayerByAttribute_management(voro_lyr, "NEW_SELECTION", '"OBJECTID" = ' + str(row[0]))
    arcpy.SelectLayerByLocation_management(route_lyr, "INTERSECT", voro_lyr)
    for row2 in arcpy.da.SearchCursor(route_lyr, ["origin","destination"]):
        voro_dict[row[0]].append((row2[0], row2[1]))
f = open(path_f + "voro_dict.txt", 'w')
cPickle.dump(voro_dict, f)
f.close()
