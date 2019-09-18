from os import path,mkdir,remove
from sqlite3 import connect
from hashlib import sha256
from re import sub
from datetime import datetime
def init_database():
    if(not path.isfile("data/AnalyzeBucks.sqlite3")):
        conn = connect("data/AnalyzeBucks.sqlite3")
        conn.execute('''CREATE TABLE tbl_user(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_admin INTEGER NOT NULL)''')
        conn.commit()
        conn.close()
        create_user('admin','admin',1)

def create_user(username,password,is_admin):
    conn = connect("data/AnalyzeBucks.sqlite3")
    conn.execute("INSERT INTO tbl_user(username,password,is_admin) VALUES(?,?,?)",
                (username,sha256(password.encode()).hexdigest(),is_admin))
    conn.commit()
    conn.close()
    
    conn = connect('data/'+username+'.sqlite3')
    conn.execute('''CREATE TABLE tbl_transaction
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_date INT NOT NULL,
            details TEXT NOT NULL, 
            debit_amount REAL, 
            credit_amount REAL, 
            balance_amount REAL NOT NULL);''')
    conn.execute('''CREATE TABLE tbl_debit
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_date INT NOT NULL,
        details TEXT NOT NULL, 
        debit_amount REAL, 
        balance_amount REAL NOT NULL,
        cluster_index INT,
        cluster_description TEXT);''')
    conn.execute('''CREATE TABLE tbl_credit
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_date INT NOT NULL,
        details TEXT NOT NULL, 
        credit_amount REAL, 
        balance_amount REAL NOT NULL,
        cluster_index INT,
        cluster_description TEXT);''')
    conn.commit()
    conn.close()

def delete_user(username):
    if(path.isfile("data/AnalyzeBucks.sqlite3")):
        conn = connect('data/AnalyzeBucks.sqlite3')
        conn.execute("DELETE FROM tbl_user WHERE username=?",(username,))
        conn.commit()
        conn.close()
    if(path.isfile("data/"+username+".sqlite3")):
        remove('data/'+username+'.sqlite3')

def change_user_role(username,is_admin):
    conn = connect('data/AnalyzeBucks.sqlite3')
    conn.execute("UPDATE tbl_user SET is_admin=? WHERE username=?",(username,is_admin))
    conn.commit()
    conn.close()

def change_user_password(username,newpasswd):
    conn = connect('data/AnalyzeBucks.sqlite3')
    conn.execute("UPDATE tbl_user SET password=? WHERE username=?",(username,sha256(newpasswd.encode()).hexdigest()))
    conn.commit()
    conn.close()

def get_user_password(username):
    password = None
    conn = connect('data/AnalyzeBucks.sqlite3')
    cursor = conn.execute('SELECT password FROM tbl_user WHERE username=?',(username,))
    row = cursor.fetchone()
    if row:
        password = row[0]
    conn.close()
    return password

def get_user_role(username):
    role = None
    conn = connect('data/AnalyzeBucks.sqlite3')
    cursor = conn.execute('SELECT is_admin FROM tbl_user WHERE username=?',(username,))
    row = cursor.fetchone()
    if row:
        role = int(row[0])
    conn.close()
    return role    

def InsertIntoTables(data,username):
    if(len(data) > 0):    
        tbl_transaction_query = "INSERT INTO tbl_transaction(transaction_date,details,debit_amount,credit_amount,balance_amount) VALUES "
        tbl_debit_query = "INSERT INTO tbl_debit(transaction_date,details,debit_amount,balance_amount) VALUES "
        tbl_credit_query = "INSERT INTO tbl_credit(transaction_date,details,credit_amount,balance_amount) VALUES "
        transaction_type = ""
        for row in data:
            if(row[2] != ""):
                transaction_type = "debit"
                tbl_transaction_query = tbl_transaction_query + \
                    "("+str(row[0])+",'"+row[1]+"'," + \
                    str(row[2])+",NULL,"+str(row[4])+"),"
                tbl_debit_query = tbl_debit_query + \
                    "("+str(row[0])+",'"+row[1]+"'," + \
                    str(row[2])+","+str(row[4])+"),"
            else:
                transaction_type = "credit"
                tbl_transaction_query = tbl_transaction_query + \
                    "("+str(row[0])+",'"+row[1]+"',NULL," + \
                    str(row[3])+","+str(row[4])+"),"
                tbl_credit_query = tbl_credit_query + \
                    "("+str(row[0])+",'"+row[1]+"'," + \
                    str(row[3])+","+str(row[4])+"),"
        tbl_transaction_query = tbl_transaction_query[:-1]+";"
        tbl_debit_query = tbl_debit_query[:-1]+";"
        tbl_credit_query = tbl_credit_query[:-1]+";"
        conn = connect('data/'+username+'.sqlite3')
        conn.execute(tbl_transaction_query)
        if(transaction_type=="debit"):
            conn.execute(tbl_debit_query)
        else:
            conn.execute(tbl_credit_query)
        conn.commit()
        conn.close()


def preprocess(text):
    return sub(r"\s+$", "", sub(" +", " ", sub('[^a-zA-Z0-9]', ' ',sub('[/-]', " ", text))))

def get_transactions(table_name,username):
    data_dict = {}
    conn = connect('data/'+username+'.sqlite3')
    cursor = conn.execute(
        "SELECT id, details FROM "+table_name)
    for row in cursor:
        data_dict.update({int(row[0]): preprocess(row[1])})
    conn.close()
    return data_dict

def get_credit_transactions(username):
    data = {}
    conn = connect('data/'+username+'.sqlite3')
    cursor = conn.execute("SELECT * FROM tbl_credit")
    for row in cursor:
        data.update({row[0]:[datetime.utcfromtimestamp(row[1]),row[2],row[3],row[4]]})
    conn.close()
    return data

def get_debit_transactions(username):
    data = {}
    conn = connect('data/'+username+'.sqlite3')
    cursor = conn.execute("SELECT * FROM tbl_debit")
    for row in cursor:
        data.update({row[0]:[datetime.utcfromtimestamp(row[1]),row[2],row[3],row[4]]})
    conn.close()
    return data

def get_all_transactions(username):
    data = {}
    conn = connect('data/'+username+'.sqlite3')
    cursor = conn.execute("SELECT * FROM tbl_transaction")
    for row in cursor:
        data.update({row[0]:[datetime.utcfromtimestamp(row[1]),row[2],row[3],row[4],row[5]]})
    conn.close()
    return data

def update_clusters(table_name, keys, clusters,username):
    if(len(clusters)>0):
        conn = connect('data/'+username+'.sqlite3')
        for i in range(len(keys)):
            conn.execute("UPDATE "+table_name+" set cluster_index = " + str(
                clusters[i][0])+" ,cluster_description = '"+str(clusters[i][1])+"' where id = "+str(keys[i]))
        conn.commit()
        conn.close()