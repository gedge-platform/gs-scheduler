import subprocess
from curses import noecho
import os
from flask import Flask, render_template, session, abort, jsonify, Response, request, send_file
from flask_session import Session
import requests
import json


def root_dir():
    #ROOT_DIR = os.path.abspath(os.curdir)
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    return ROOT_DIR


upload_path = os.path.join(".", "upload")

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 1024*1024*1024
app.config['UPLOAD_FOLDER'] = upload_path

app.config["SECRET_KEY"] = "the top secret!"
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)




fission_control = 'http://10.107.192.35'



@app.route("/")
def hello_world():
    return render_template('index.html')

@app.route("/environmentinfo")
def environmentinfo():
    return render_template('environmentinfo.html')

@app.route("/functioninfo")
def functioninfo():
    return render_template('functioninfo.html')

@app.route("/triggerinfo")
def triggerinfo():
    return render_template('triggerinfo.html')


def error(code, text):
    return jsonify({"code":code,"text":text}), 406

@app.route("/v2/environments", methods = ['POST', 'GET', 'DELETE'])
def environments():
    
    
    if request.method == 'GET':
        response = requests.get(f"{fission_control}/v2/environments", timeout=10)
        if response.status_code == 200:
            json_object = json.loads(response.text)
            
            idx = 1
            for d in json_object:
                d['num'] = idx
                idx = idx + 1
            
            return jsonify(json_object), 200
    elif request.method == 'POST':
        
        print(request.get_json())
        
        response = requests.post(f"{fission_control}/v2/environments", json=request.get_json())
        
        return response.text, response.status_code
    
    elif request.method == 'DELETE':
        print(request.get_json())
        response = requests.delete(f"{fission_control}/v2/environments/{request.get_json()['metadata']['name']}")
        return response.text, response.status_code
    
    return error(response.status_code, response.text)
    
    
@app.route("/v2/functions", methods = ['POST', 'GET', 'DELETE'])
def functions():
    
    
    if request.method == 'GET':
        response = requests.get(f"{fission_control}/v2/functions", timeout=10)
        if response.status_code == 200:
            json_object = json.loads(response.text)
            
            idx = 1
            for d in json_object:
                
                p = subprocess.Popen(f"fission fn get --name {d['metadata']['name']}", stdout=subprocess.PIPE, shell=True)

                b = p.communicate()
                
                t = ''
                
                for s in b:
                    if s != None:
                        t += s.decode('utf-8')
                
                d['num'] = idx
                d['content'] = t 
                idx = idx + 1
            
            return jsonify(json_object), 200
    elif request.method == 'POST':
        j = request.get_json()
        
        p = subprocess.Popen(f"cat <<EOF > test.file\n{j['content']}\nEOF", stdout=subprocess.PIPE, shell=True)
        print(p.communicate())
        p = subprocess.Popen(f"fission fn create --name {j['name']} --code test.file --env {j['env']}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    
        b = p.communicate()
        t = ''
        for s in b:
            if s != None:
                t += s.decode('utf-8')
        print(t)
        
        return t, 201
    
    elif request.method == 'DELETE':
        print(request.get_json())
        response = requests.delete(f"{fission_control}/v2/functions/{request.get_json()['metadata']['name']}")
        return response.text, response.status_code
    
    return error(response.status_code, response.text)


    
@app.route("/v2/triggers/http", methods = ['POST', 'GET', 'DELETE'])
def triggers_http():
    
    
    if request.method == 'GET':
        response = requests.get(f"{fission_control}/v2/triggers/http", timeout=10)
        if response.status_code == 200:
            json_object = json.loads(response.text)
            
            idx = 1
            for d in json_object:
                d['num'] = idx
                d['call'] = 'http://172.16.11.206'+d['spec']['relativeurl']
                idx = idx + 1
            
            return jsonify(json_object), 200
    elif request.method == 'POST':
        j = request.get_json()
        
        p = subprocess.Popen(f"fission route create --name {j['name']} --function  {j['function']} --url {j['url']}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    
        b = p.communicate()
        t = ''
        for s in b:
            if s != None:
                t += s.decode('utf-8')
        print(t)
        
        return t, 201
    
    elif request.method == 'DELETE':
        print(request.get_json())
        response = requests.delete(f"{fission_control}/v2/triggers/http/{request.get_json()['metadata']['name']}")
        return response.text, response.status_code
    
    return error(response.status_code, response.text) 
    
    
@app.route("/v2/functions/<function>", methods = ['GET'])
def functions_function(function):
    
    response = requests.get(f"{fission_control}/v2/functions/{function}", timeout=10)
    if response.status_code == 200:
        json_object = json.loads(response.text)
        
        
        return jsonify(json_object), 200
    

import faas_api

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True, debug=False, port=8032)