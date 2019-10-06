from sqlite3 import connect
from tabulate import tabulate
conn = connect("data/lakshman.sqlite3")
cursor = conn.execute("SELECT * FROM tbl_debit ORDER BY cluster_index")
data = []
for row in cursor:
    data.append([row[2],row[5],row[6]])
print(tabulate(data,headers=["description","cluster id","cluster name"]))
conn.close()
