from flask import Flask, render_template, redirect, request, url_for, session,send_from_directory
import random
import shutil
import json
import operations
import string

app = Flask(__name__)
randomkey = ""

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static/images','favicon.ico') 

@app.errorhandler(500)
def servererror(e):
    return render_template("error_500.html")


@app.errorhandler(404)
def pagenotfound(e):
    return render_template("error_404.html")

@app.route("/", methods=['GET', 'POST'])
def login():
    global randomkey
    try:
        if(session.get("key")==randomkey):
            return render_template("main.html")
        else:
            if request.method == "POST":
                name = request.form['name']
                password = request.form['password']
                if(name=="admin"):
                    if(check_password(password)):
                        randomkey = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])
                        session['key'] = randomkey
                        return render_template("main.html")
                    else:
                        return render_template("index.html",error="Incorrect password")
                else:
                    return render_template("index.html",error="Incorrect username")
            else:
                return render_template("index.html")
    except Exception as e:
        print(e)
        return redirect(url_for("servererror"))

def change_password(old_password, new_password):
    if(check_password(old_password)):
        f=open("data/credentials.json",'r')
        data = json.loads(f.read())
        f.close()
        data.update({'password':new_password})
        f = open("data/credentials.json",'w')
        f.write(json.dumps(data))
        f.close()
        return True
    else:
        return False
    
def check_password(password):
    f=open("data/credentials.json",'r')
    original_password = json.loads(f.read())["password"]
    f.close()
    if(original_password==password):
        return True
    else:
        return False

def init_configurations():
    if(not shutil.os.path.isdir("data")):
        shutil.os.mkdir("data")
        f = open("data/credentials.json",'w')
        f.write(json.dumps({"password":"password"}))
        f.close()
        operations.initialize_database()

if __name__ == "__main__":
    init_configurations()
    app.config['SECRET_KEY'] = "Your_secret_string"
    app.run()