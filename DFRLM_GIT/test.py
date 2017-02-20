import arcpy
from collections import defaultdict

path = 'F:\\data\\Orlando\\Orlando.gdb\\'
routes = "routes_volume"
OD_pair_dict = defaultdict(list)

for row in arcpy.da.SearchCursor(path + routes, ["OID@", "Name", "Gravity"]):
    s = str(row[1]).split("-")
    s1 = [x.split('Location') for x in s]
    OD_pair_dict[int(s1[0][1])].append((int(s1[1][1]), row[2]))
                                       
