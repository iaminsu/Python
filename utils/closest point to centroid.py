import pysal, shapefile, cPickle
from shapely.geometry import Point, Polygon, LineString, MultiPoint, MultiPolygon

path_r = "F:\\Dropbox\\research\\Distance restricted covering model\\Locating recharging station\\Data4\\"


def generateGeometry(path, in_shp):
    """Using PySal, Load shp file obj and return Shapley obj"""
    resultingGeometry = []
    f = open(path + in_shp)
    if f.header['Shape Type'] == 1:
        for i in range(len(f)):
            resultingGeometry.append(Point(f.get_shape(i)['X'], f.get_shape(i)['Y']))
    elif f.header['Shape Type'] == 3:
        for i in range(len(f)):
            resultingGeometry.append(LineString(f.get_shape(i)['Vertices']))
    elif f.header['Shape Type'] == 5:
        for i in range(len(f)):
            resultingGeometry.append(Polygon(f.get_shape(i)['Vertices']))
    return resultingGeometry    
def interset(shp_a, shp_b):
    

grid_f = "grid.shp"
demands_f = "sample_demand_2_p.shp"

grid_shp = generateGeometry(grid_f)
demand_shp = generateGeometry(demands_f)

for box in grid_shp:
    