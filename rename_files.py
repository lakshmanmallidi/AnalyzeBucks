import os
for filename in os.listdir("files/xls/"):
    f = open("files/xls/"+filename)
    raw_data = f.read()
    f.close()
    _,month,year = [row.split("\t") for row in raw_data.split("\n")][17][1].split(" ")
    os.rename("files/xls/"+filename,"files/xls/"+year+"_"+month+".xls")
    