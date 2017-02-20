import fiona, networkx
from shapely.geometry import Point, LineString

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


ddawwad

