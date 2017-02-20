import networkx, fiona
from shapely.geometry import Polygon, Point, LineString

path = "C:\\Users\\Insu\\Dropbox\\Classes\\2016 Fall\\GEOG 493K\\data\\"    #change path for your own data 
def openShp_mk2(path, in_f):
    with fiona.open(path +in_f, 'r') as f_sh:
        shape = []
        att_table = []
        if f_sh[0]['geometry']['type'] == 'Polygon':
            for record in f_sh:
                #geometry
                if len(record['geometry']['coordinates']) == 1:
                    shape.append(Polygon(record['geometry']['coordinates'][0]))
                else:
                    shape.append(Polygon(record['geometry']['coordinates'][0],record['geometry']['coordinates'][1:]))
                #attribute 
                att_table.append(record['properties'])
        elif f_sh[0]['geometry']['type'] == 'LineString':
            for record in f_sh:
                shape.append(LineString(record['geometry']['coordinates']))
                att_table.append(record['properties'])
        elif f_sh[0]['geometry']['type'] == 'Point':
            for record in f_sh:
                shape.append(Point(record['geometry']['coordinates']))
                att_table.append(record['properties'])
        return shape, att_table


schema_poly = {
    'geometry': 'Polygon',
    'properties': {'id': 'int'}, }
schema_line = {
    'geometry': 'LineString',
    'properties': {'id': 'int'}, }
schema_point = {
    'geometry': 'Point',
    'properties': {'id': 'int'}, }
def writeShp(path, in_shp, out_name):
    """
    in_shp must be list 
    all elements must be same type 
    """
    for i in in_shp:
        if i.is_empty:
            print str(i) + ' is empty'
            raise Exception
    if in_shp[0].type == 'Polygon':
        schema = schema_poly
    elif in_shp[0].type == 'LineString':
        schema = schema_line
    elif in_shp[0].type == 'Point':
        schema = schema_point
    else:
        raise TypeError
    with fiona.open(path + out_name, 'w', 'ESRI Shapefile', schema) as c:
        for i in in_shp:
            c.write({
                'geometry': mapping(i),
                'properties': {'id': in_shp.index(i)},
            })   





def createGraph(shp, a_table):
    out_graph = networkx.Graph()
    nodes_dict = {}
    for i in range(len(shp)):
        attributes = {}
        for item in a_table[i]:
            attributes[item] = a_table[i][item]
        out_graph.add_edge(list(shp[i].coords)[0], list(shp[i].coords)[1], attributes)
        
    return out_graph



print "test"