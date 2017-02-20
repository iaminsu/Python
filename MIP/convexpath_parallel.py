#Convexpath approach sequential version 

#Including containing case & spatial filtering method 

import pysal, shapefile, networkx, time
from shapely.geometry import Point, Polygon, LineString, MultiPoint, MultiPolygon
from collections import defaultdict
from multiprocessing import Pool
import multiprocessing as mp
#import cProfile, pstats, StringIO

path_macPro = "/Users/insu/Downloads/data_higher/"
path_imac = "/Users/insu/Dropbox/research/Convexpath Approach/HPC/data/"
path_home = "F:\\Dropbox\\research\\Convexpath Approach\\HPC\\data\\"
path_air = "/Users/insuhong/Dropbox/research/Convexpath Approach/testField/data/"
path_ubuntu = "/home/insu/Dropbox/research/Convexpath Approach/Convexpath_HiDensity/data/"

path = path_macPro
origin = "large_origin_2.shp"
destination = "large_destination_2.shp"
obstacles = "asu_500.shp"

#ncpus = mp.cpu_count()
ncpus = 4
print ncpus


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
ori_shp = pysal.IOHandlers.pyShpIO.shp_file(path + origin)
des_shp = pysal.IOHandlers.pyShpIO.shp_file(path + destination)
obs_shp = pysal.IOHandlers.pyShpIO.shp_file(path + obstacles)
originPoints = generateGeometry(ori_shp)
destinationPoints = generateGeometry(des_shp)
obstaclesPolygons = generateGeometry(obs_shp)

version_name = "_Convexpath_Parallel_B_"
pair_number = 0
ODPairs = []
for i in originPoints:
    for j in destinationPoints:
        ODPairs.append([(i,j), pair_number])
        pair_number += 1
        
f = open(path + "Results" + version_name + origin + "_" + destination +"_"+obstacles+ "_" + str(ncpus)+ ".txt", "w")
        
        

def createGraph(lineSet):
    resultingGraph = networkx.Graph()
    for line in lineSet:
        resultingGraph.add_edge(line[0], line[1], weight = LineString(line).length)
    return resultingGraph
def createConvexhull(poly, endPoints = []):
    convexVerticex = []
    if poly.type == 'MultiPolygon':
        for i in poly.geoms:
            convexVerticex.extend(list(i.exterior.coords))
    else:
        convexVerticex.extend(list(poly.exterior.coords))
    convexVerticex.extend(endPoints)
    convex_hull = MultiPoint(convexVerticex).convex_hull

    return convex_hull
def splitBoundary_l(lineSet, poly):
    poly_vertices = list(poly.exterior.coords)
    for v in range(len(poly_vertices)):
        if (v + 1) == len(poly_vertices):
            a = [(poly_vertices[v][0], poly_vertices[v][1]), (poly_vertices[-1][0], poly_vertices[-1][1])]
            if a[0] != a[1]:
                if a not in lineSet:
                    if [a[1],a[0]] not in lineSet:
                        lineSet.append(a)
        else:
            a = [(poly_vertices[v][0], poly_vertices[v][1]), (poly_vertices[v+1][0], poly_vertices[v+1][1])]
            if a[0] != a[1]:
                if a not in lineSet:
                    if [a[1],a[0]] not in lineSet:
                        lineSet.append(a)
def splitBoundary(lineSet, poly):
    poly_vertices = list(poly.exterior.coords)


    for v in range(len(poly_vertices)):
        if (v + 1) == len(poly_vertices):
            a = ((poly_vertices[v][0], poly_vertices[v][1]), (poly_vertices[-1][0], poly_vertices[-1][1]))
            if a[0] != a[1]:
                if not lineSet.has_key(a):
                    if not lineSet.has_key((a[1],a[0])):
                        lineSet[a] = LineString(a)
        else:
            a = ((poly_vertices[v][0], poly_vertices[v][1]), (poly_vertices[v+1][0], poly_vertices[v+1][1]))
            if a[0] != a[1]:
                if not lineSet.has_key(a):
                    if not lineSet.has_key((a[1],a[0])):
                        lineSet[a] = LineString(a)

class makeImpededPaths(object):
    def __init__(self, in_path, in_obs):
        self.in_path = in_path
        self.in_obs = in_obs
    def __call__(self):
        results = []
        Line = LineString(self.in_path)
        for obs in self.in_obs:
            if Line.crosses(obs):
                results.append(self.in_path)
                break
        return results
def makeCrossing(in_list):

    crossing = defaultdict(list)
    lines = []
    results = {}
    Line = LineString(in_list[0])
    for obs in in_list[1]:
        if Line.crosses(obs):
            crossing[tuple(in_list[0])].append(obs)
    if len(crossing) == 0:
        return results
    else:
        containingObs = []
        for obs in crossing[tuple(in_list[0])]:
            convexHull2 = createConvexhull(obs)
            chk_contain = 0
            if convexHull2.contains(Point(in_list[0][0])):
                chk_contain = 1
                containingObs.append(obs)
            elif convexHull2.contains(Point(in_list[0][1])):
                chk_contain = 1
                containingObs.append(obs)
            if chk_contain == 0:
                convexHull = createConvexhull(obs, in_list[0])
                splitBoundary_l(lines, convexHull)
        if len(containingObs) != 0:
            #print "SPLIT"
            subConvexPathList = []
            vi_obs = MultiPolygon([x for x in containingObs])
            containedLineCoords = list(in_list[0])
            fromX = containedLineCoords[0][0]
            fromY = containedLineCoords[0][1]
            toX = containedLineCoords[1][0]
            toY = containedLineCoords[1][1]
            fxA = (fromY - toY) / (fromX - toX)
            fxB = fromY - (fxA * fromX)
            minX = vi_obs.bounds[0]
            maxX = vi_obs.bounds[2]
            split_line = LineString([(min(minX, fromX, toX), fxA * min(minX, fromX, toX) + fxB), (max(maxX, fromX, toX), fxA * max(maxX, fromX, toX) + fxB)])
            
            for obs in containingObs:
                s1, s2 = splitPolygon(split_line, obs)
                
                dividedObsPoly = []
                #to deal with multipolygon
                a = s1.intersection(obs)
                b = s2.intersection(obs)
                if a.type == "Polygon":
                    dividedObsPoly.append(a)
                else:
                    for o in a.geoms:
                        if o.type == "Polygon":
                            dividedObsPoly.append(o)
                if b.type == "Polygon":
                    dividedObsPoly.append(b)
                else:
                    for o2 in b.geoms:
                        if o2.type == "Polygon":
                            dividedObsPoly.append(o2)
                
                for obs2 in dividedObsPoly:
                    for pt in in_list[0]:
                        convexHull = createConvexhull(obs2, [pt])
                        splitBoundary_l(subConvexPathList, convexHull)
            subVertices = []
            for line in subConvexPathList:
                subVertices.extend(line)
            subVertices = list(set(subVertices))
            containingObsVertices = []
            for obs in containingObs:
                containingObsVertices.extend(list(obs.exterior.coords))
            subVertices = [x for x in subVertices if x in containingObsVertices]
            deleteList = []
            for line in subConvexPathList:
                chk_cross = 0
                for obs in containingObs:
                    if LineString(line).crosses(obs):
                        chk_cross = 1
                if chk_cross == 1:
                    deleteList.append(line)
            subConvexPathList = [x for x in subConvexPathList if x not in deleteList]
            pairList = []
            for i in range(len(subVertices)):
                for j in range(i+1, len(subVertices)):
                    pairList.append([subVertices[i], subVertices[j]])
            
            for i in pairList:
                Line = LineString(i)
                chk_cross = 0
                for obs in containingObs:
                    if Line.crosses(obs):
                        chk_cross = 1
                    elif Line.within(obs):
                        chk_cross = 1
                if chk_cross == 0:
                    subConvexPathList.append(i)
            buffer_st_line = split_line.buffer(0.1)
            deleteList = []
            for line in subConvexPathList:
                if buffer_st_line.contains(LineString(line)):
                    deleteList.append(line)
            subConvexPathList = [x for x in subConvexPathList if x not in deleteList]
            lines.extend(subConvexPathList)                  
        results[tuple(in_list[0])] = lines
        return results 
    
def splitPolygon(line, poly):
    
    minX, minY, maxX, maxY = poly.bounds
    polyBound = Polygon([(minX, minY), (minX, maxY), (maxX, maxY), (maxX, minY)])
    splitLine = polyBound.intersection(line)        
    lcoord = list(splitLine.coords)
    Ax, Ay, Bx, By = 0, 0, 0, 0 
    if lcoord[0][0] > lcoord[1][0]:
        Ax, Ay, Bx, By = lcoord[0][0], lcoord[0][1], lcoord[1][0], lcoord[1][1]
    elif lcoord[0][0] == lcoord[1][0]:  #vertical line 
        if lcoord[0][1] > lcoord[1][1]:
            Ax, Ay, Bx, By = lcoord[0][0], lcoord[0][1], lcoord[1][0], lcoord[1][1]
        else:
            Ax, Ay, Bx, By = lcoord[1][0], lcoord[1][1], lcoord[0][0], lcoord[0][1]
    elif lcoord[0][0] < lcoord[1][0]:
        Ax, Ay, Bx, By = lcoord[1][0], lcoord[1][1], lcoord[0][0], lcoord[0][1]
    
    if Ax == maxX:
        if Bx == minX:
            s1 = Polygon([(minX, maxY),(maxX, maxY), (Ax, Ay), (Bx, By)])
            s2 = Polygon([(Bx, By), (Ax, Ay), (maxX, minY), (minX, minY)])
        elif By == maxY:
            s1 = Polygon([(Bx, By), (maxX, maxY), (Ax, Ay)])
            s2 = Polygon([(minX, maxY), (Bx, By), (Ax, Ay), (maxX, minY), (minX, minY)])
        elif By == minY:
            s1 = Polygon([(minX, maxY), (maxX, maxY), (Ax, Ay), (Bx, By), (minX, minY)])
            s2 = Polygon([(Ax, Ay), (maxX, minY), (Bx, By)])
    elif Ay == maxY:
        if By == minY:
            s1 = Polygon([(minX, maxY), (Ax, Ay), (Bx, By), (minX, minY)])
            s2 = Polygon([(Ax, Ay), (maxX, maxY), (maxX, minY), (Bx, By)])
        elif Bx == minX:
            s1 = Polygon([(minX, maxY), (Ax, Ay), (Bx, By)])
            s2 = Polygon([(Bx, By), (Ax, Ay), (maxX, maxY), (maxX, minY), (minX, minY)])
    elif Ay == minY:
        if By == maxY:
            s1 = Polygon([(minX, maxY), (Bx, By), (Ax, Ay), (minX, minY)])
            s2 = Polygon([(Bx, By), (maxX, maxY), (maxX, minY), (Ax, Ay)])
        elif Bx == minX:
            s1 = Polygon([(Bx, By), (Ax, Ay), (minX, minY)])
            s2 = Polygon([(Bx, By), (minX, maxY), (maxX, maxY), (maxX, minY), (Ax, Ay)])
    return s1, s2
    
    
    

class Worker(mp.Process):

    def __init__(self, tasks, results):
        mp.Process.__init__(self)
        self.tasks = tasks
        self.results = results

    def run(self):
        while True:
            time.sleep(10)
            #Draw a job off the queue
            next_job = self.tasks.get()
            #If the queue is finished we can shutdown
            if next_job is None:
                self.tasks.task_done()
                break
            #Executes __call__ method in Small_pp1 class
            job_result = next_job()
            #Set the task as finished.
            self.tasks.task_done()
            self.results.put(job_result)


to_compute = mp.JoinableQueue()
computed = mp.Queue()

#Get the cpu count

workers = [Worker(to_compute, computed) for i in range(ncpus)]
for w in workers:
    w.start()
    
pool = Pool()



for pair in ODPairs:
    #pr = cProfile.Profile()
    #pr.enable()
    time_start = time.time()
    odPointsList = ((pair[0][0].x, pair[0][0].y), (pair[0][1].x, pair[0][1].y))
    st_line = LineString(odPointsList)
    labeledObstaclePoly = []
    totalConvexPathList = {}
    dealtArcList = {}
    totalConvexPathList[odPointsList] = st_line
    terminate = 0
    idx_loop1 = 0
    sp_l_set = []
    time_convexPP = 0
    time_impedingArcs = 0
    time_crossingDict = 0
    time_list1 = 0
    time_list2 = 0
    time_list3 = 0
    time_pp = 0
    time_loop1 = 0
    
    while terminate == 0:
        idx_loop1 += 1
        totalGraph = createGraph(totalConvexPathList.keys())
        spatial_filter_n = networkx.dijkstra_path(totalGraph, odPointsList[0], odPointsList[1])
        spatial_filter = []
        for i in range(len(spatial_filter_n)-1):
            spatial_filter.append([spatial_filter_n[i], spatial_filter_n[i+1]])
        crossingDict = defaultdict(list)
        for line in spatial_filter:
            Line = LineString(line)
            deleteList = []
            for obs in obstaclesPolygons:
                if Line.crosses(obs):
                    if obs not in labeledObstaclePoly:
                        labeledObstaclePoly.append(obs)
                    crossingDict[tuple(line)].append(obs)
        if len(crossingDict.keys()) == 0:
            terminate = 1
            continue   
        else:
            for tLine in crossingDict:
                if dealtArcList.has_key(tLine):
                    del totalConvexPathList[tLine]
                    continue
                else:
                    dealtArcList[tLine] = LineString(tLine)
                    try:
                        del totalConvexPathList[tLine]
                    except:
                        totalConvexPathList[(tLine[1], tLine[0])]
                    containingObs = []
                    for obs in crossingDict[tLine]:
                        convexHull = createConvexhull(obs, tLine)
                        splitBoundary(totalConvexPathList, convexHull)
                        convexHull = createConvexhull(obs, odPointsList)
                        splitBoundary(totalConvexPathList, convexHull)
                        convexHull2 = createConvexhull(obs)
                        if convexHull2.contains(Point(tLine[0])):
                            containingObs.append(obs)
                        elif convexHull2.contains(Point(tLine[1])):
                            containingObs.append(obs)
                    if len(containingObs) != 0:
                        subConvexPathList = {}
                        vi_obs = MultiPolygon([x for x in containingObs])
                        containedLineCoords = tLine
                        fromX = containedLineCoords[0][0]
                        fromY = containedLineCoords[0][1]
                        toX = containedLineCoords[1][0]
                        toY = containedLineCoords[1][1]
                        fxA = (fromY - toY) / (fromX - toX)
                        fxB = fromY - (fxA * fromX)
                        minX = vi_obs.bounds[0]
                        maxX = vi_obs.bounds[2]
                        split_line = LineString([(min(minX, fromX, toX), fxA * min(minX, fromX, toX) + fxB), (max(maxX, fromX, toX), fxA * max(maxX, fromX, toX) + fxB)])
                        
                        for obs in containingObs:
                            s1, s2 = splitPolygon(split_line, obs)
                            dividedObsPoly = []
                            #to deal with multipolygon
                            a = s1.intersection(obs)
                            b = s2.intersection(obs)
                            if a.type == "Polygon":
                                dividedObsPoly.append(a)
                            else:
                                for o in a.geoms:
                                    if o.type == "Polygon":
                                        dividedObsPoly.append(o)
                            if b.type == "Polygon":
                                dividedObsPoly.append(b)
                            else:
                                for o2 in b.geoms:
                                    if o2.type == "Polygon":
                                        dividedObsPoly.append(o2)
                            
                            for obs2 in dividedObsPoly:
                                for pt in tLine:
                                    convexHull = createConvexhull(obs2, [pt])
                                    splitBoundary(subConvexPathList, convexHull)   
                        subVertices = []
                        for line in subConvexPathList:
                            subVertices.extend(line)
                        subVertices = list(set(subVertices))
                        containingObsVertices = []
                        for obs in containingObs:
                            containingObsVertices.extend(list(obs.exterior.coords))
                        subVertices = [x for x in subVertices if x in containingObsVertices]
                        deleteList = []
                        for line in subConvexPathList:
                            chk_cross = 0
                            for obs in containingObs:
                                if subConvexPathList[line].crosses(obs):
                                    chk_cross = 1
                                    break
                            if chk_cross == 1:
                                deleteList.append(line)
                        for line in deleteList:
                            del subConvexPathList[line]
                        pairList = []
                        for i in range(len(subVertices)):
                            for j in range(i+1, len(subVertices)):
                                pairList.append((subVertices[i], subVertices[j]))
                        for i in pairList:
                            Line = LineString(i)
                            chk_cross = 0
                            for obs in containingObs:
                                if Line.crosses(obs):
                                    chk_cross = 1
                                elif Line.within(obs):
                                    chk_cross = 1
                            if chk_cross == 0:
                                subConvexPathList[i] = Line
                        buffer_st_line = split_line.buffer(0.1)
                        deleteList = []
                        for line in subConvexPathList:
                            if buffer_st_line.contains(LineString(line)):
                                deleteList.append(line)     
                        for line in deleteList:
                            if subConvexPathList.has_key(line):
                                del subConvexPathList[line]
                        for line in subConvexPathList:
                            if not totalConvexPathList.has_key(line):
                                totalConvexPathList[line] = subConvexPathList[line]

        labeled_multyPoly = MultiPolygon([x for x in labeledObstaclePoly])
        convexHull = createConvexhull(labeled_multyPoly, odPointsList)
        splitBoundary(totalConvexPathList, convexHull)        
        
        t1s = time.time()
        impededPathList = {}
       
        for line in totalConvexPathList:
            for obs in labeledObstaclePoly:
                if totalConvexPathList[line].crosses(obs):
                    impededPathList[line] = totalConvexPathList[line]
                    break
        for line in impededPathList:
            if totalConvexPathList.has_key(line):
                del totalConvexPathList[line]
        t1e = time.time()
        time_list1 += t1e - t1s 
        terminate2 = 0
        idx_loop2 = 0   
        #w = shapefile.Writer(shapefile.POLYGON)
        #w.field('net')
        #for obs in labeledObstaclePoly:
            #w.poly(parts=[[list(x) for x in list(obs.exterior.coords)]])
            #w.record('ff')
        #w.save(path + "obs"+ str(idx_loop1) + "_" + version_name)        
        while terminate2 == 0:
            idx_loop2 += 1
            for line in dealtArcList:
                if impededPathList.has_key(line):
                    del impededPathList[line]
            in_iter = []
            t2s = time.time()
            t4s = time.time()
            for line in impededPathList:
                in_iter.append([line, labeledObstaclePoly])
            
            
            results = pool.map_async(makeCrossing, in_iter)
            
            t4e = time.time()
            time_pp += t4e - t4s
            length = 0
            t10s = time.time()
            for i in results.get():
                
                if len(i) != 0:
                    
                    length += len(i)
                    dealtArcList[i.keys()[0]] = LineString(i.keys()[0])
                    del impededPathList[i.keys()[0]]
                    for line in i[i.keys()[0]]:
                        if not impededPathList.has_key(tuple(line)):
                            impededPathList[tuple(line)] = LineString(line)
            t10e = time.time()
            time_list3 += t10e - t10s
            t2e = time.time()
            
            time_convexPP += t2e - t2s
            if length == 0:
                terminate2 = 1
            for line in dealtArcList:
                if impededPathList.has_key(line):
                    del impededPathList[line]
        t3s = time.time()
        
        for line in impededPathList:
            if not totalConvexPathList.has_key(line):
                totalConvexPathList[line] = impededPathList[line]
        t3e = time.time()
        time_list2 += t3e - t3s
                    
        
    #pr.disable()  
    #s = StringIO.StringIO()
    #sortby = 'cumulative'

    #ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    
    #ps.print_stats()
    #print s.getvalue()
    totalGraph = createGraph(totalConvexPathList)
    esp_n = networkx.dijkstra_path(totalGraph, odPointsList[0], odPointsList[1])
    esp = []
    for i in range(len(esp_n)-1):
        esp.append([esp_n[i], esp_n[i+1]])
    w = shapefile.Writer(shapefile.POLYLINE)
    w.field('nem')
    no_edges = 0
    for line in totalConvexPathList:
        no_edges += 1
        w.line(parts=[[ list(x) for x in line ]])
        w.record('ff')
    w.save(path + "totalpath" + version_name + "%d" % pair[1] )     
    
    w = shapefile.Writer(shapefile.POLYLINE)
    w.field('nem')
    for line in esp:
        w.line(parts=[[ list(x) for x in line ]])
        w.record('ff')
    w.save(path + "ESP_" + version_name + "%d" % pair[1])
    time_end = time.time()
    print pair[1]
    print "creating impedingArcs: ", time_list1
    print "Convex PP: ", time_convexPP   #crossingDict + time_contain _ convexLoop 
    print "time_pp:", time_pp
    print "list2: ", time_list2
    print "list3: ", time_list3
    print time_end - time_start
    f.write('convexpath %d %d %d %f %f %f' % (pair[1], no_edges, len(labeledObstaclePoly), time_convexPP, time_end - time_start, time_list3) + "\n")

    
f.close()    
for c in range(ncpus):
    to_compute.put(None)