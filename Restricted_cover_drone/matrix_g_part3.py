import cPickle, pysal
from shapely.geometry import Point, Polygon, LineString, MultiPoint, MultiPolygon



def generateGeometry(in_shp):
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

facilities_f = "new_candis.shp"
path = "F:\\Dropbox\\research\\Distance restricted covering model\\Locating recharging station\\Data_Mk8\\"

facil_pysal = pysal.IOHandlers.pyShpIO.shp_file(path+facilities_f)
facil_shp = generateGeometry(facil_pysal)

coords_dict = {}
coords_reverse = {}
for i in range(len(facil_shp)):
    coords_dict[(facil_shp[i].x, facil_shp[i].y)] = i
    coords_reverse[i] = (facil_shp[i].x, facil_shp[i].y)

f = open(path + "FF_coords_Dict_" + facilities_f + ".txt","w")
ff = open(path + "FF_coords_reverse_" + facilities_f + ".txt", 'w')
cPickle.dump(coords_dict, f)
cPickle.dump(coords_reverse, ff)
f.close()
ff.close()

