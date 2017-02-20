#Simulated annealing for location optimization of recharging stations for drone delivery system 
#MCLP

import cPickle, random


path = ""
ffDict = ""
fdDict = ""
dDict = ""
#loading matrices & initialize variables 
f_FF = open(path + ffDict)
f_FD = open(path + fdDict)
f_demand = open(path + dDict)
F_Fdict = cPickle.load(f_FF)
F_Ddict = cPickle.load(f_FD)
dDict = cPickle.load(f_demand)
warehouses = []    #id_f of warehouses
solution_sites = []
covered_demand = []
objective_value = 0
p = 0    #given number of facilities including existing warehouses 
t0 = 0
max_iter = 0
tf = 0
cf = 0.2


def cal_obj(in_solution):
    for site in in_solution:
        covered_demand.extend(F_Ddict[site])
    covered_demand = list(set(covered_demand))
    for de in covered_demand:
        obj += dDict[de]
    return obj

def chk_feasibility(in_solution=[]):
    result = True
    for site in in_solution:
        eval_list = in_solution 
        eval_list.remove(site)
        linked_sites = []
        for i in eval_list:
            linked_sites.extend(F_Fdict[i])
        linked_sites = list(set(linked_sites))
        if site not in linked_sites:
            result = False
            break
        else:
            continue
    return result

def resctricted_cadidates(in_solution):
    candis = []
    for site in in_solution:
        candis.extend(F_Fdict[site])
    candis = list(set(candis))
    candis = [x for x in candis if x not in in_solution]
    return candis

def spatial_interchange(in_solution):
    c = resctricted_cadidates(in_solution)
    flag = False
    while len(c) != 0:
        candi = random.choice(c)
        c.remove(candi)
        current_obj = [in_solution, cal_obj(in_solution)]
        for site in in_solution:
            temp_sol = in_solution.remove(site)
            temp_sol.append(candi)
            temp_obj = cal_obj(temp_sol)
            if temp_obj > current_obj[1]:
                flag = True
                current_obj = [temp_sol, temp_obj]
                
            

#initializing seed solution (random) 
solution_sites.extend(warehouses)


while len(solution_sites) < p:
    random_pool = []
    for i in solution_sites:
        random_pool.extend(F_Fdict[i])
    random_pool = list(set(random_pool))
    solution_sites.append(random.choice(random_pool))


while t0 > 0.5:
    #spatially restricted interchange algorithm 
    c = resctricted_cadidates(solution_sites)
    flag = False 
    while len(c) != 0:
        candi = random.choice(c)
        c.remove(candi)
        
    
    
        
        
        
        
        
