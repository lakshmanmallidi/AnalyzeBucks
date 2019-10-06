import os
from data_extractor import StateBankIndia
from dao import insert_into_tables,get_transactions,update_clusters,create_user,init_database
from data_analyzer import segregate
def upload_files():
    for statement in os.listdir("files/sbh"):
        f = open('files/sbh/'+statement)
        raw_data = f.read()
        f.close()
        data = StateBankIndia(raw_data)
        insert_into_tables(data,'lakshman')
#init_database()
#create_user('lakshman','harrypotter',0)
n_clusters = 10
upload_files()
data = get_transactions('tbl_debit','lakshman')
clusters, error_msg = segregate(list(data.values()), n_clusters)
update_clusters('tbl_debit', list(data.keys()), clusters,'lakshman')
print(error_msg)
data = get_transactions('tbl_credit','lakshman')
clusters, error_msg = segregate(list(data.values()), n_clusters)
update_clusters('tbl_credit', list(data.keys()), clusters,'lakshman')
print(error_msg)