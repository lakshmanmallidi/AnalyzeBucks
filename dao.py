from os import path,mkdir,remove
from sqlite3 import connect
from hashlib import sha256
from re import sub
from datetime import datetime
from random import choice
from string import ascii_letters,digits
def init_database():
    if(not path.isfile("data/AnalyzeBucks.sqlite3")):
        conn = connect("data/AnalyzeBucks.sqlite3")
        conn.execute('''CREATE TABLE tbl_user(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_admin INTEGER NOT NULL)''')
        conn.execute('''CREATE TABLE tbl_session(
            key TEXT NOT NULL UNIQUE,
            username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()
        conn.close()
        create_user('admin','admin',1)

def is_user(username):
    conn = connect("data/AnalyzeBucks.sqlite3")
    cursor = conn.execute("SELECT COUNT(*) FROM tbl_user WHERE username=?",(username,))
    userCount = cursor.fetchone()[0]
    conn.close()
    if(userCount==0):
        return False
    return True

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
    conn.execute("UPDATE tbl_user SET is_admin=? WHERE username=?",(is_admin,username))
    conn.commit()
    conn.close()

def change_user_password(username,newpasswd):
    conn = connect('data/AnalyzeBucks.sqlite3')
    conn.execute("UPDATE tbl_user SET password=? WHERE username=?",(sha256(newpasswd.encode()).hexdigest(),username))
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

def create_session(username):
    conn = connect('data/AnalyzeBucks.sqlite3')
    key = None
    while True:
        key = ''.join([choice(ascii_letters + digits) for n in range(32)])
        cursor = conn.execute('SELECT * FROM tbl_session WHERE key=?',(key,))
        row = cursor.fetchone()
        if not row:
            break
    conn.execute('INSERT INTO tbl_session(key, username) VALUES(?,?)',(key,username))
    conn.commit()
    conn.close()
    return key

def get_session(key):
    username = None
    conn = connect('data/AnalyzeBucks.sqlite3')
    cursor = conn.execute('SELECT username FROM tbl_session WHERE key=?',(key,))
    row = cursor.fetchone()
    if row:
        username = row[0]
    conn.close()
    return username
 
def delete_session(username):
    conn = connect('data/AnalyzeBucks.sqlite3')
    conn.execute('DELETE FROM tbl_session WHERE username=?',(username,))
    conn.commit()
    conn.close()

def insert_into_tables(data,username):
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
        rearrange_data(username)

def rearrange_data(username):
    conn = connect('data/'+username+".sqlite3")
    conn.execute('''CREATE TEMPORARY TABLE temp_transaction AS 
                    SELECT transaction_date,details,
                    debit_amount,credit_amount,balance_amount 
                    FROM tbl_transaction ORDER BY transaction_date''')
    conn.execute("DELETE FROM tbl_transaction")
    conn.execute("DELETE FROM sqlite_sequence where name='tbl_transaction'")
    conn.execute('''INSERT INTO tbl_transaction(transaction_date,
                                                details,
                                                debit_amount,
                                                credit_amount,
                                                balance_amount) 
                    SELECT * FROM temp.temp_transaction''')
    conn.execute("DROP TABLE TEMP.temp_transaction")

    conn.execute('''CREATE TEMPORARY TABLE temp_debit AS 
                    SELECT transaction_date,details,
                    debit_amount,balance_amount 
                    FROM tbl_debit ORDER BY transaction_date''')
    conn.execute("DELETE FROM tbl_debit")
    conn.execute("DELETE FROM sqlite_sequence where name='tbl_debit'")
    conn.execute('''INSERT INTO tbl_debit(transaction_date,
                                                details,
                                                debit_amount,
                                                balance_amount) 
                    SELECT * FROM temp.temp_debit''')
    conn.execute("DROP TABLE TEMP.temp_debit")

    conn.execute('''CREATE TEMPORARY TABLE temp_credit AS 
                    SELECT transaction_date,details,
                    credit_amount,balance_amount 
                    FROM tbl_credit ORDER BY transaction_date''')
    conn.execute("DELETE FROM tbl_credit")
    conn.execute("DELETE FROM sqlite_sequence where name='tbl_credit'")
    conn.execute('''INSERT INTO tbl_credit(transaction_date,
                                                details,
                                                credit_amount,
                                                balance_amount) 
                    SELECT * FROM temp.temp_credit''')
    conn.execute("DROP TABLE TEMP.temp_credit")
    conn.commit()
    conn.close()

def preprocess(text):
    return sub(r"\s+$", "", sub(" +", " ", sub('[^a-zA-Z0-9]', ' ',sub('[/-]', " ", text))))

def delete_transactions(from_date, to_date, username):
    conn = connect('data/'+username+".sqlite3")
    from_date_epoch = from_date.strftime("%s")
    to_date_epoch = to_date.strftime("%s")
    conn.execute("DELETE FROM tbl_transaction WHERE transaction_date BETWEEN "+from_date_epoch+
                           " AND "+to_date_epoch )
    conn.execute("DELETE FROM tbl_credit WHERE transaction_date BETWEEN "+from_date_epoch+
                           " AND "+to_date_epoch )
    conn.execute("DELETE FROM tbl_debit WHERE transaction_date BETWEEN "+from_date_epoch+
                           " AND "+to_date_epoch )
    conn.commit()
    conn.close()
    rearrange_data(username)

def get_transactions(table_name,username):
    data_dict = {}
    conn = connect('data/'+username+'.sqlite3')
    cursor = conn.execute(
        "SELECT id, details FROM "+table_name)
    for row in cursor:
        data_dict.update({int(row[0]): preprocess(row[1])})
    conn.close()
    return data_dict
    
def get_transaction_count(username):
    count=0
    conn = connect("data/"+username+".sqlite3")
    cursor = conn.execute("SELECT count(*) FROM tbl_transaction")
    row = cursor.fetchone()
    if row:
        count = int(row[0])
    conn.close()
    return count

def get_all_transactions(username,id, pagination):
    data = []
    conn = connect('data/'+username+'.sqlite3')
    cursor = conn.execute("SELECT * FROM tbl_transaction WHERE id>? AND id<=?",(id,id+pagination))
    for row in cursor:
        data.append((row[0],datetime.utcfromtimestamp(row[1]).strftime("%d %b %Y"),row[2],row[3],row[4],row[5]))
    conn.close()
    return data

def get_all_users():
    data = []
    conn = connect("data/AnalyzeBucks.sqlite3")
    cursor = conn.execute("SELECT username,is_admin FROM tbl_user")
    for row in cursor:
        data.append((row[0],row[1]))
    conn.close()
    return data

def get_cluster(username, table, cluster_index):
    conn = connect('data/'+username+'.sqlite3')
    cursor = None
    if(table=='debit'):
        cursor = conn.execute("SELECT id, transaction_date, details, debit_amount, balance_amount FROM tbl_debit WHERE cluster_index=?",(cluster_index,))
    else:
        cursor = conn.execute("SELECT id, transaction_date, details, credit_amount, balance_amount FROM tbl_credit WHERE cluster_index=?",(cluster_index,))
    segment_data = []
    for row in cursor:
        segment_data.append((row[0],datetime.utcfromtimestamp(row[1]).strftime("%d %b %Y"),row[2],row[3],row[4]))
    if(table=='debit'):
        cursor = conn.execute("SELECT cluster_description FROM tbl_debit WHERE cluster_index=?",(cluster_index,))
    else:
        cursor = conn.execute("SELECT cluster_description FROM tbl_credit WHERE cluster_index=?",(cluster_index,)) 
    raw_cluster_description = cursor.fetchone()
    cluster_description = ""
    if(raw_cluster_description):
        cluster_description = raw_cluster_description[0]
    segment_data_graph = []
    if(table=='debit'):
        cursor = conn.execute("SELECT  transaction_date, sum(debit_amount) FROM tbl_debit GROUP BY transaction_date HAVING cluster_index=?",(cluster_index,))
    else:
        cursor = conn.execute("SELECT transaction_date, sum(credit_amount) FROM tbl_credit GROUP BY transaction_date HAVING cluster_index=?",(cluster_index,))
    for row in cursor:
        segment_data_graph.append((datetime.utcfromtimestamp(row[0]).strftime("%d %b %Y"), row[1]))
    conn.close()
    return (segment_data,segment_data_graph,cluster_description)

def get_group_by(username,table):
    conn = connect('data/'+username+'.sqlite3')   
    cursor = None
    if(table=="tbl_credit"):
        cursor = conn.execute("SELECT cluster_index,cluster_description,SUM(credit_amount) FROM tbl_credit GROUP BY cluster_index,cluster_description")
    else:
        cursor = conn.execute("SELECT cluster_index,cluster_description, SUM(debit_amount) FROM tbl_debit GROUP BY cluster_index,cluster_description")
    data = []
    for row in cursor:
        data.append((row[0],row[1],round(row[2],2)))
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