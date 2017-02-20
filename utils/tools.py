import pysal, shapefile, cPickle, copy
from shapely.geometry import Point, Polygon, LineString, MultiPoint, MultiPolygon

path_r = "F:\\Dropbox\\research\\Distance restricted covering model\\Locating recharging station\\Data_mk8\\"


def generateGeometry(path, in_shp):
    """
    Using PySal, Load shapefile and return Shapley obj (list)
    
    """
    resultingGeometry = []
    f = pysal.IOHandlers.pyShpIO.shp_file(path+in_shp)
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
def select_by_location(source, target, condition):
    """
    return target layer features that satisfy given condition 
    conditions 
    Source and target layers must be list data 
    1. intersect 
    (working)
    """
    if condition == 'intersect':
        result = []
        for t in target:
            for s in source:
                if t.intersects(s):
                    result.append(t)
                    break
        return result
            
    #elif condition = 

def closest_point_to_centroid(polygon, point):
    """len()
    Return the closest point to a centroid for each polygon in polygon layer.
    If no point intersects to a polygon, return empty list
    """
    result = []
    t_pts = copy.copy(point)
    for poly in polygon: 
        candis = select_by_location([poly], t_pts, "intersect")
        t_pts = [x for x in t_pts if x not in candis]
        if len(candis) == 0:
            continue
        else:
            cent = poly.centroid
            dist = []
            for p in candis:
                dist.append((p.distance(cent), p))
            dist.sort()
            result.append((poly, dist[0][1]))
    return result

def save_shp(in_shp, v_type, path, shp_name):
    """
    Save Shapely object as new shapefile. No attribute. Meaningless field and value are generated.
    """
    if v_type == 'line':
        w = shapefile.Writer(shapefile.POLYLINE)
        w.field('nem')
        for el in in_shp:
            w.line(parts=[[ list(x) for x in list(el.coords)]])
            w.record('chu')
        w.save(path + shp_name)    
    if v_type == 'polygon':
        w = shapefile.Writer(shapefile.POLYGON)
        w.field('net')
        for el in in_shp:
            w.poly(parts=[[list(x) for x in list(el.exterior.coords)]])
            w.record('ff')
        w.save(path + shp_name) 
    if v_type == "point":
        w = shapefile.Writer(shapefile.POINT)
        w.field('cc')
        for el in in_shp:
            w.point(el.x, el.y)
            w.record('dd')
        w.save(path + shp_name)
    else:
        raise TypeError

def save_attShp(in_shp, in_attr, v_type, path):
    """
    Save Shapely object with attribute table (dictionary) as new shape file 
    attr dictionary: {OID: {field_name: vlaue}}
    """
    if v_type == 'line':
        field_list= in_attr[in_attr.keys()[0]].keys()
        w = shapefile.Writer(shapefile.POLYLINE)
        for field in field_list:
            w.field(field)
        for el in in_shp:
            w.line(parts=[[list(x) for x in list(el.coords)]])
            s = "w.record("
            for f in field_list:
                s += str(in_attr[in_shp.index(el)][f]) + ','
            s = s[:-1]
            s += ")"
            exec(s)
        w.save(path + shp_name)    
    if v_type == 'polygon':
        field_list= in_attr[in_attr.keys()[0]].keys()
        w = shapefile.Writer(shapefile.POLYGON)
        for field in field_list:
            w.field(field)        
        for el in in_shp:
            w.poly(parts=[[list(x) for x in list(el.exterior.coords)]])
            s = "w.record("
            for f in field_list:
                s += str(in_attr[in_shp.index(el)][f]) + ','
            s = s[:-1]
            s += ")"
            exec(s)
        w.save(path + shp_name) 
    if v_type == "point":
        field_list= in_attr[in_attr.keys()[0]].keys()
        w = shapefile.Writer(shapefile.POINT)
        for field in field_list:
            w.field(field)        
        for el in in_shp:
            w.point(el.x, el.y)
            s = "w.record("
            for f in field_list:
                s += str(in_attr[in_shp.index(el)][f]) + ','
            s = s[:-1]
            s += ")"
            exec(s)            
        w.save(path + shp_name)
    else:
        raise TypeError    