import datetime
import time
import os
import sqlite3
import pickle
import shutil
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans as kmeans


def findstem(arr):
    result = []
    for x in range(len(arr)):
        subparts = arr[x].split(" ")
        for i in range(len(subparts)):
            for j in range(i+1, len(subparts)+1):
                part = " ".join(subparts[i:j])
                count = 0
                for y in range(len(arr)):
                    if (part in arr[y]) and (x != y):
                        count = count+1
                result.append((count, part))
    maxval = 0
    result_str = ""
    for count, str_part in result:
        if(count > maxval):
            maxval = count
            result_str = str_part
        elif(count == maxval and len(str_part) > len(result_str)):
            result_str = str_part
    return result_str


def update_clusters(table_name, keys, clusters):
    conn = sqlite3.connect('data/AnalyzeBucks.sqlite3')
    for i in range(len(keys)):
        conn.execute("UPDATE "+table_name+" set cluster_index = " + str(
            clusters[i][0])+" ,cluster_description = '"+str(clusters[i][1])+"' where transaction_id = "+str(keys[i]))
    conn.commit()
    conn.close()


def preprocess(text):
    return re.sub(r"\s+$", "", re.sub(" +", " ", re.sub('[^a-zA-Z]', ' ', re.sub('[0-9]', '', re.sub('[/-]', " ", text)))))


def get_transactions(table_name):
    data_dict = {}
    conn = sqlite3.connect("data/AnalyzeBucks.sqlite3")
    cursor = conn.execute(
        "SELECT transaction_id, transaction_details FROM "+table_name)
    for row in cursor:
        data_dict.update({int(row[0]): preprocess(row[1])})
    conn.close()
    return data_dict


def segregate(transaction_details, n):
    vectorizer = CountVectorizer()
    vector = vectorizer.fit_transform(transaction_details)
    word_counts = vector.toarray()
    k_means = kmeans(n_clusters=n)
    k_means.fit(word_counts)
    cluster_ids = k_means.labels_
    unique_clustor = set(cluster_ids)
    unique_clusters = {}
    for clustor_id in unique_clustor:
        common_words = []
        for j in range(len(cluster_ids)):
            if(clustor_id == cluster_ids[j]):
                common_words.append(transaction_details[j])
        unique_clusters.update({clustor_id: findstem(list(set(common_words)))})
    clusters = []
    for clustor_id in cluster_ids:
        clusters.append((clustor_id, unique_clusters[clustor_id]))
    return clusters


def initialize_database():
    conn = sqlite3.connect('data/AnalyzeBucks.sqlite3')
    conn.execute('''CREATE TABLE Transactions
            (transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_date INT NOT NULL,
            transaction_details TEXT NOT NULL, 
            debit REAL, 
            credit REAL, 
            balance REAL NOT NULL);''')
    conn.close()

def StateBankIndia(raw_data):
    def convert_date(raw_date):
        time_zones = load_time_zones()
        return int(time.mktime(datetime.datetime.strptime(raw_date, "%d %b %Y").timetuple())+time_zones['Asia/Kolkata (IST)'])

    formated_data = [row.split("\t") for row in raw_data.split("\n")]
    final_data = []
    row_num = 20
    while True:
        if(len(formated_data[row_num]) >= 5):
            transaction_date = convert_date(formated_data[row_num][0])
            transaction_details = formated_data[row_num][2].strip()
            if(formated_data[row_num][4] != " "):
                debit = float(formated_data[row_num][4].replace(",", ""))
            else:
                debit = ""
            if(formated_data[row_num][5] != " "):
                credit = float(formated_data[row_num][5].replace(",", ""))
            else:
                credit = ""
            if(formated_data[row_num][6] != " "):
                balance = float(formated_data[row_num][6].replace(",", ""))
            else:
                balance = ""
            final_data.append(
                (transaction_date, transaction_details, debit, credit, balance))
        else:
            break
        row_num = row_num+1
    return final_data


def InsertIntoBaseTable(data):
    if(len(data) > 0):
        query = "INSERT INTO Transactions(transaction_date,transaction_details,debit,credit,balance) VALUES "
        for row in data:
            if(row[2] != ""):
                query = query + \
                    "("+str(row[0])+",'"+row[1]+"'," + \
                    str(row[2])+",NULL,"+str(row[4])+"),"
            else:
                query = query + \
                    "("+str(row[0])+",'"+row[1]+"',NULL," + \
                    str(row[3])+","+str(row[4])+"),"
        query = query[:-1]+";"
        conn = sqlite3.connect('data/AnalyzeBucks.sqlite3')
        conn.execute(query)
        conn.commit()
        conn.close()


def create_sub_tables():
    conn = sqlite3.connect('data/AnalyzeBucks.sqlite3')
    conn.execute("CREATE TABLE Debits AS SELECT transaction_id,transaction_date,transaction_details,debit,balance,NULL as cluster_index,NULL as cluster_description FROM Transactions WHERE credit is NULL;")
    conn.execute("CREATE TABLE Credits AS SELECT transaction_id,transaction_date,transaction_details,credit,balance,NULL as cluster_index,NULL as cluster_description FROM Transactions WHERE debit is NULL;")
    conn.close()


def delete_sub_tables():
    conn = sqlite3.connect('data/AnalyzeBucks.sqlite3')
    conn.execute("DROP TABLE Debits")
    conn.execute("DROP TABLE Credits")
    conn.close()


def driver():
    for statement in os.listdir("files/sbh"):
        f = open('files/sbh/'+statement)
        raw_data = f.read()
        f.close()
        data = StateBankIndia(raw_data)
        InsertIntoBaseTable(data)


def load_time_zones():
    f = open('time_zones.pkl', 'rb')
    time_zones = pickle.load(f)
    f.close()
    return time_zones

'''
n_clusters = 80
initialize_database()
driver()
create_sub_tables()
data = get_transactions('debits')
clusters = segregate(list(data.values()), n_clusters)
update_clusters('debits', list(data.keys()), clusters)
data = get_transactions('credits')
clusters = segregate(list(data.values()), n_clusters)
update_clusters('credits', list(data.keys()), clusters)
'''