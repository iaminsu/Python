import time, csv

csv_name = "dist.csv"
path = "F:\\Dropbox\\research\\Food desert\\Josh\\"
f = open(path + csv_name)
ff = csv.reader(f)

def int_chk (s):
    try: 
        int(s)
    except ValueError:
        return False
    else:
        return True


out_csv_name = "result_" + str(time.localtime()) + '.csv' 
out_csv = open(path + out_csv_name, 'w')

agency = -1
for line in ff: 
    string = ""
    
    l = [x for x in line if x != '']
    for i in range(len(l)):
        if ',' in l[i]:
            l[i] = l[i].translate(None, ',')
    if len(l) == 0:
        continue
    else:
        string = str(agency) + ','
        if int_chk(l[0]):  #data
            string += l[0] + "," + l[1] + ","
            if 'USDA' in l[1]: 
                string += "1" + ","
            else:
                string += "0" + ","
            string += l[-4]  + "," + l[-3]  + "," + l[-2] + ","+ l[-1] + "\n"
            out_csv.write(string)
        else:    #agency 
            a = l[0].split(' ')
            if 'Totals:' in a:   #total
                pass
            else:                #header 
                agency = a[1]
    
            
out_csv.close()