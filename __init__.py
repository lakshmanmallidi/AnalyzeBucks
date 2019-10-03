from flask import Flask,\
    render_template,\
    redirect,\
    request,\
    url_for,session,\
    make_response,\
    jsonify,\
    send_from_directory
from os import path, mkdir
from json import load, dump
from dao import get_user_password,\
                init_database,\
                get_all_transactions,\
                get_user_role,\
                get_session, \
                create_session, \
                delete_session, \
                change_user_password, \
                get_transaction_count , \
                delete_transactions, \
                insert_into_tables, \
                get_all_users, \
                delete_user, \
                change_user_password, \
                change_user_role, \
                is_user, \
                create_user
from data_extractor import factory           
from hashlib import sha256
from jwt import encode, decode
from functools import wraps
from datetime import datetime
app = Flask(__name__)

def session_checker(f):
    @wraps(f)
    def check(*args,**kwargs):
        print("entered")
        if('key' in session):
            username = get_session(session.get('key'))
            if(username):
                role =  get_user_role(username)
                return f(username,role,*args, **kwargs)
            else:
                return redirect(url_for("login"))
        else:
            return redirect(url_for("login"))    
    return check

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static/images','favicon.ico') 

@app.errorhandler(500)
def servererror(e):
    return render_template("error_500.html")


@app.errorhandler(404)
def pagenotfound(e):
    return render_template("error_404.html")

@app.route("/logout")
@session_checker
def logout(username, role):
    delete_session(username) 
    session.clear()
    return redirect(url_for("login"))

@app.route("/get_transactions")
@session_checker
def get_transactions(username,role):
    if("page" in request.args):
        page = int(request.args["page"])
        data = get_all_transactions(username,(page*pagination)-pagination,pagination)
        response = ""
        for row in data:
            response = response +"<tr><td>"+str(row[0])+"</td><td>"+str(row[1])+\
                "</td><td colspan='3'>"+str(row[2])+"</td>"
            if row[3]==None:
                response = response+"<td>0</td><td>"+str(row[4])+"</td><td>"+str(row[5])+"</td></tr>"
            else:
                response = response+"<td>"+str(row[3])+"</td><td>0</td><td>"+str(row[5])+"</td></tr>"
        return response
    else:
        return ""

@app.route("/user_manager",methods=["GET","POST"])
@session_checker
def  user_manager(username, role):
    if(role==1):
        if(request.method=="POST"):
            if(request.form['type']=='Revoke'):
                change_user_role(request.form['username'], 0)
            elif(request.form['type']=='Grant'):
                change_user_role(request.form['username'], 1)
            elif(request.form['type']=='Reset'):
                change_user_password(request.form['username'],'password')
            elif(request.form['type']=='Delete'):
                if(request.form['username']!=username):
                    delete_user(request.form['username'])
            elif(request.form['type']=="Create"):
                if(not is_user(request.form['username'])):
                    create_user(request.form['username'],'password',0)
                    users = get_all_users()
                    return render_template("user_manager.html",role=role, users = users, username = username, msg="user successfully created")
                else:
                    users = get_all_users()
                    return render_template("user_manager.html",role=role, users = users, username = username,error="user already exists")
            else:
                pass
            return ""
        else:
            users = get_all_users()
            return render_template("user_manager.html",role=role, users = users, username = username)
    else:
        return redirect(url_for("login"))

def get_meta_info(username):
    transaction_count = get_transaction_count(username)
    if(transaction_count%pagination != 0):
        page_count = int(transaction_count/pagination)+1
    else:
        page_count = int(transaction_count/pagination)
    data = get_all_transactions(username,0,pagination)
    return (data,page_count)

@app.route("/upload", methods=["GET","POST"])
@session_checker
def upload(username, role):
    page_count = None
    if(request.method == "POST"):
        if(request.form['form-type']=='Upload'):
            if(request.form['bank']!='default'):
                data_files=request.files.getlist("files")
                extractor = factory(request.form['bank'])
                data_arr = []
                try:
                    for data_file in data_files:
                        data_arr.append(extractor(data_file.read().decode()))
                except Exception as e:
                    data, page_count =  get_meta_info(username)
                    return render_template("upload.html",transactions = data,page_count = page_count,role = role,error="Invalid file format") 
                for e in data_arr:
                    insert_into_tables(e,username)
                data, page_count =  get_meta_info(username)
                return render_template("upload.html",transactions = data,page_count = page_count,role = role,msg="Succesfully uploaded files")
            else:
                data, page_count =  get_meta_info(username)
                return render_template("upload.html",transactions = data,page_count = page_count,role = role,error="Please select your bank")
        else:
            if(request.form['from_date']!="" and request.form['to_date']!=""):
                from_date = datetime.strptime(request.form['from_date'], "%Y-%m-%d")
                to_date = datetime.strptime(request.form['to_date'],"%Y-%m-%d")
                if(to_date>=from_date):
                    delete_transactions(from_date, to_date, username)
                    data, page_count =  get_meta_info(username)
                    return render_template("upload.html",transactions=data,page_count = page_count,role=role,msg="Records successfully deleted")
                else:
                    data, page_count =  get_meta_info(username)
                    return render_template("upload.html",transactions = data,page_count = page_count,role = role,error="From Date should less than or equal to To Date")    
            else:
                data, page_count =  get_meta_info(username)
                return render_template("upload.html",transactions = data,page_count = page_count,role = role,error="Please select valid date")
    else:
        data, page_count =  get_meta_info(username)
        return render_template("upload.html",transactions = data,page_count = page_count,role = role)

@app.route("/settings",methods=["GET","POST"])
@session_checker
def settings(username, role):
    if(request.method=="POST"):
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"] 
        if(new_password == confirm_password):
            if(sha256(old_password.encode()).hexdigest()==get_user_password(username)):
                change_user_password(username, new_password)
                return render_template("settings.html",role = role, msg="Password successfully updated")
            else:
                return render_template("settings.html",role = role, error="Incorrect password")
        else:
            return render_template("settings.html",role = role, msg="Please enter same password")   
    else:
        return render_template("settings.html", role = role)

@app.route('/', methods=['GET','POST'])
def login():      
    if("key" in session):
        username = get_session(session.get("key")) 
        if(username):
            return redirect(url_for("upload"))
        else:
            return render_template("login.html",msg="Please login again!")
    else:   
        if(request.method == "POST"):
            username = request.form['name']
            password = request.form['password']
            if(sha256(password.encode()).hexdigest()==get_user_password(username)):
                session.perminent = True
                session['key'] = create_session(username)
                return redirect(url_for("upload"))
            else:
                return render_template("login.html",error="Invalid password or username")
        else:
            return render_template("login.html")

def init_config():
    configuration = None
    if(not path.isdir('data')):
        mkdir("data")
    init_database()
    if(not path.isfile('data/configuration.json')):
        configuration = {'secret_key':'your_own_secret_key',
                         'host':'localhost',
                         'port':'9997'}
        with open('data/configuration.json','w') as config_file:
            dump(configuration,config_file)
    else:
        with open('data/configuration.json','r') as config_file:
            configuration = load(config_file)
    return configuration

if __name__ == "__main__":
    pagination = 100
    configuration = init_config()
    app.config['SECRET_KEY'] = configuration['secret_key'] 
    app.run(host=configuration['host'],port=configuration['port'])