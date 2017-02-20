import cPickle, pysal, Convexpath_module, networkx, shapefile
from shapely.geometry import Point, Polygon, LineString, MultiPoint, MultiPolygon
from collections import defaultdict


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

facilities_f = "sample_sites_2.shp"
obstacles_f = "obstacles_p.shp"
path = "/Users/insuhong/Dropbox/research/Distance restricted covering model/Locating recharging station/data4/"
path_results = "/Users/insuhong/Dropbox/research/Distance restricted covering model/Locating recharging station/results/"
facil_pysal = pysal.IOHandlers.pyShpIO.shp_file(path+facilities_f)
obs_pysal = pysal.IOHandlers.pyShpIO.shp_file(path+obstacles_f)
facil_shp = generateGeometry(facil_pysal)
obs_shp = generateGeometry(obs_pysal)

warehouse_ID = [127,324, 411]
solution_sites = [127, 324, 411, 350, 390, 323, 228, 184, 435, 494, 380, 483, 473, 416, 205, 34, 44, 13, 398, 195, 346, 49, 107, 334, 413]
return_dist = 10 * 5280 
w = shapefile.Writer(shapefile.POLYLINE)
w.field('nem')

for site in solution_sites:
    for i in solution_sites:
        if site != i:
            a = Convexpath_module.Convexpath_shapely(path, facil_shp[site], facil_shp[i], obs_shp)
            if a.esp.length <= return_dist:
                arc_list = list(a.esp.coords)
                w.line(parts = [[ list(x) for x in arc_list]])
                w.record('chu')

w.save(path_results + "return_network_" + str(len(solution_sites)))

            