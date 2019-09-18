from flask import Flask, render_template, redirect, request, url_for, session,make_response, jsonify
from os import path, mkdir
from json import load, dump
from dao import get_user_password,init_database, get_all_transactions,get_user_role
from hashlib import sha256
from jwt import encode, decode
from functools import wraps
app = Flask(__name__)

def token_checker(f):
    @wraps(f)
    def check(*args,**kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401
        try:
            data = decode(token,app.config['SECRET_KEY'])
            username = data['username']
        except:
             return jsonify({'message' : 'Token is missing!'}), 401
        return f(username,*args, **kwargs)
    return check

@app.route('/getalltransactions')
@token_checker
def statement(username):
    data = get_all_transactions(username)
    return jsonify(data)        

@app.route('/authenticate')
def authenticate():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('could not verify',401,{"www-Authenticate":'Basic realm="Login required!"'})
    if(get_user_password(auth.username)==sha256(auth.password.encode()).hexdigest()):
        token = encode({'username':auth.username},app.config['SECRET_KEY'])
        return jsonify({"token":token.decode('UTF-8')})
    return make_response('could not verify',401,{"www-Authenticate":'Basic realm="Login required!"'})  

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
    configuration = init_config()
    app.config['SECRET_KEY'] = configuration['secret_key'] 
    app.run(host=configuration['host'],port=configuration['port'])