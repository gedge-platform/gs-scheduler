from __main__ import app, upload_path
from __main__ import fission_control

import os, sys
from flask import request, abort, jsonify, session
import json
import uuid
import requests
import subprocess
from curses import noecho
from werkzeug.utils import secure_filename


dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
sys.path.append(dir_path)
add_path = os.path.join(dir_path,'sch')
sys.path.append(add_path)

from mongoagent import MongoAgent

mongo_ip = os.getenv('MONGO_IP')


route_url = 'http://172.16.11.206'


if mongo_ip == None:
    mongo_ip = 'mongo.gedge.ai'

print('MongoAgent connecting to ',mongo_ip,'..........')

mongo = MongoAgent(mongo_ip)

PREFIX= "/GEP/FAAS/users/<user_name>"

@app.route(f"{PREFIX}/environments", methods=["GET", "POST"])
def user_environments(user_name):
    
    #if mongo.isexist('user', {'user_name':user_name}) == False:
    #    abort(406, description='user_name  is not exists.')

    if request.method == "POST":
        if request.data == None:
            abort(406, description='content is empty.')
            
        environment = json.loads(request.data.decode('utf8'))
        
        
        if 'env_name' not in environment:
            abort(406, description='env_name is empty.')
            
        if 'image' not in environment:
            abort(406, description='image is empty.')

        args = ''

        environment['user_name'] = user_name

        if 'image' in environment:
            args += f"--image={environment['image']} "

        if 'poolsize' in environment:
            args += f"--poolsize={environment['poolsize']} "

        if 'builder' in environment:
            args += f"--builder={environment['builder']} "

        if 'buildcmd' in environment:
            args += f"--buildcmd={environment['buildcmd']} "

        p = subprocess.Popen(f"fission environment create --name {environment['env_name']} --namespace={user_name} {args}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        b = p.communicate()
        t = ''
        l = ''
        for s in b:
            if s != None:
                s_ = s.decode('utf-8')
                t += s_
                l = s_

        
        if 'Error:' not in l:
            response = requests.get(f"{fission_control}/v2/environments/{environment['env_name']}?namespace={user_name}", timeout=10)
        
            if response.status_code == 200:
                fission_meta = response.json()
                
                if 'managedFields' in fission_meta['metadata']:
                    fission_meta['metadata'].pop('managedFields')
                
                environment['fission_meta'] = fission_meta['metadata']
                environment['fission_spec'] = fission_meta['spec']
                environment['env_uid'] = fission_meta['metadata']['uid']
                mongo.insert('environment', environment)
                
                environment.pop('_id')
                return jsonify(environment), 201
            else:
                return response.text, response.status_code
        
        return l, 406
        
    elif request.method == "GET":
        d = {'user_name':user_name}
             
        rs = mongo.select('environment', d)
        
        environments = []
        
        for r in rs:
            r.pop('_id')

            response = requests.get(f"{fission_control}/v2/environments/{r['env_name']}?namespace={user_name}", timeout=10)
            if response.status_code == 200:
                fission_meta = response.json()
                
                if 'managedFields' in fission_meta['metadata']:
                    fission_meta['metadata'].pop('managedFields')
                
                r['fission_meta'] = fission_meta['metadata']
                r['fission_spec'] = fission_meta['spec']
                r['env_uid'] = fission_meta['metadata']['uid']

            environments.append(r)
            
        return jsonify(environments)



@app.route(f"{PREFIX}/environments/<env_name>", methods=["GET","PUT", "DELETE"])
def user_environmentsbyenv_name(user_name, env_name):
    
    #if mongo.isexist('user', {'user_name':user_name}) == False:
    #    abort(406, description='user_name  is not exists.')
        
    d = {'user_name':user_name, "env_name": env_name}
    

    rs = mongo.select('environment', d)


    environment_ = None

    for r in rs:
        r.pop('_id')
        environment_ = r

    if request.method == "GET" or request.method == "PUT":
        if environment_ is None:
            abort(404, description=f"environment[{env_name}] is not found.")
        
    if request.method == "GET":

        response = requests.get(f"{fission_control}/v2/environments/{environment_['env_name']}?namespace={user_name}", timeout=10)
        if response.status_code == 200:
            fission_meta = response.json()
            
            if 'managedFields' in fission_meta['metadata']:
                fission_meta['metadata'].pop('managedFields')
            
            environment_['fission_meta'] = fission_meta['metadata']
            environment_['fission_spec'] = fission_meta['spec']
            environment_['env_uid'] = fission_meta['metadata']['uid']

        return jsonify(environment_)
    elif request.method == "PUT":
        
        if request.data == None:
            abort(406, description='content is empty.')
            
        environment = json.loads(request.data.decode('utf8'))

        args = ''

        if 'image' in environment:
            args += f"--image={environment['image']} "
            environment_['image'] = environment['image']

        if 'poolsize' in environment:
            args += f"--poolsize={environment['poolsize']} "
            environment_['poolsize'] = environment['poolsize']

        if 'builder' in environment:
            args += f"--builder={environment['builder']} "
            environment_['builder'] = environment['builder']

        if 'buildcmd' in environment:
            args += f"--buildcmd={environment['buildcmd']} "
            environment_['buildcmd'] = environment['buildcmd']
            

        p = subprocess.Popen(f"fission environment update --name {env_name} --namespace={user_name} {args}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        b = p.communicate()
        l = ''
        for s in b:
            if s != None:
                s_ = s.decode('utf-8')
                t += s_
                l = s_

        if 'updated' in l:
            mongo.update('environment', d, environment_)

            if '_id' in environment_:
                environment_.pop('_id')
            return jsonify(environment_)
        else:
            return l, 406
        
        '''
        response = requests.put(f"{fission_control}/v2/environments/{env_name}?namespace={user_name}", json=environment_['fission_meta'])
        
        if response.status_code == 200:
            fission_meta = response.json()
            
            if 'managedFields' in fission_meta:
                fission_meta.pop('managedFields')
            
            d['fission_meta'] = fission_meta
            d['env_uid'] = fission_meta['uid']
            mongo.update('environment', d)
            
            d.pop('_id')
            return jsonify(d)
        
        
        return response.text, response.status_code
        '''
        
    elif request.method == "DELETE":
        response = requests.delete(f"{fission_control}/v2/environments/{env_name}?namespace={user_name}")
        
        mongo.remove('environment', d)


        return jsonify(d), response.status_code
    

    
@app.route(f"{PREFIX}/functions", methods=["GET", "POST"])
def user_functions(user_name):

    if request.method == "POST":
        if request.data == None:
            abort(406, description='content is empty.')
            
        function = json.loads(request.data.decode('utf8'))
        
        if 'func_name' not in function:
            abort(406, description='func_name is empty.')

        '''
        d = {'user_name':user_name, "env_name": function['env_name']}
    
        
        rs = mongo.select('environment', d)

        environment_ = None
    
        for r in rs:
            r.pop('_id')
            environment_ = r

        if environment_ is None:
            abort(404, description=f"environment[{function['env_name']}] is not found.")
        '''

        '''
        if 'minscale' not in function:
            function['minscale'] = 1

        if 'maxscale' not in function:
            function['maxscale'] = 2
        '''


        args = ''

        if 'pkg' in function:
            args += f"--pkg {function['pkg']} "

        if 'entrypoint' in function:
            args += f"--entrypoint {function['entrypoint']} "

        if 'func_content' in function:
            p = subprocess.Popen(f"cat <<EOF > test.file\n{function['func_content']}\nEOF", stdout=subprocess.PIPE, shell=True)
            print(p.communicate())
            args += f"--code test.file "

        if 'env_name' in function:
            args += f"--env {function['env_name']} "



        function['user_name'] = user_name
            

        
        p = subprocess.Popen(f"fission fn create --name {function['func_name']} --namespace {user_name} {args}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    
        b = p.communicate()
        t = ''
        l = ''
        for s in b:
            if s != None:
                s_ = s.decode('utf-8')
                t += s_
                l = s_
   
        if 'Error:' not in l:
            response = requests.get(f"{fission_control}/v2/functions/{function['func_name']}?namespace={user_name}", timeout=10)
            
            if response.status_code == 200:
                fission_meta = response.json()
                
                if 'managedFields' in fission_meta['metadata']:
                    fission_meta['metadata'].pop('managedFields')
                
                function['fission_meta'] = fission_meta['metadata']
                function['fission_spec'] = fission_meta['spec']
                function['package'] = fission_meta['spec']['package']
                function['func_uid'] = fission_meta['metadata']['uid']
                mongo.insert('function', function)
                
                function.pop('_id')
                return jsonify(function), 201
            
            return response.text, response.status_code
        else:
            return l, 406
        
    elif request.method == "GET":
        d = {'user_name':user_name}
             
        rs = mongo.select('function', d)
        
        functions = []
        
        for r in rs:
            r.pop('_id')

            response = requests.get(f"{fission_control}/v2/functions/{r['func_name']}?namespace={user_name}", timeout=10)

            if response.status_code == 200:
                fission_meta = response.json()
                
                if 'managedFields' in fission_meta['metadata']:
                    fission_meta['metadata'].pop('managedFields')
                
                r['fission_meta'] = fission_meta['metadata']
                r['fission_spec'] = fission_meta['spec']
                r['package'] = fission_meta['spec']['package']
                r['func_uid'] = fission_meta['metadata']['uid']

            functions.append(r)
            
        return jsonify(functions)



@app.route(f"{PREFIX}/functions/<func_name>", methods=["GET","PUT", "DELETE"])
def user_functionsbyfunc_name(user_name, func_name):
    
    d = {'user_name':user_name, "func_name": func_name}
    

    rs = mongo.select('function', d)

    function_ = None
    
    for r in rs:
        r.pop('_id')
        function_ = r

    if request.method == "GET" or request.method == "PUT":
        if function_ is None:
            abort(404, description=f"function[{func_name}] is not found.")
        
    if request.method == "GET":

        response = requests.get(f"{fission_control}/v2/functions/{function_['func_name']}?namespace={user_name}", timeout=10)

        if response.status_code == 200:
            fission_meta = response.json()
            
            if 'managedFields' in fission_meta['metadata']:
                fission_meta['metadata'].pop('managedFields')
            
            function_['fission_meta'] = fission_meta['metadata']
            function_['fission_spec'] = fission_meta['spec']
            function_['package'] = fission_meta['spec']['package']
            function_['func_uid'] = fission_meta['metadata']['uid']

        return jsonify(function_)
    elif request.method == "PUT":
        
        if request.data == None:
            abort(406, description='content is empty.')
            
        function = json.loads(request.data.decode('utf8'))
        
        args = ''

        if 'func_content' in function:
            p = subprocess.Popen(f"cat <<EOF > test.file\n{function['func_content']}\nEOF", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            print(p.communicate())
            args += f"--code test.file "

        if 'env_name' in function:
            args += f"--env {function['env_name']} "


        p = subprocess.Popen(f"fission fn update --name {func_name} --namespace={user_name} {args}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        b = p.communicate()
        t = ''
        l = ''

        for s in b:
            if s != None:
                s_ = s.decode('utf-8')
                t += s_
                l = s_

        if 'updated' in l:

            response = requests.get(f"{fission_control}/v2/functions/{func_name}?namespace={user_name}", timeout=10)
            
            if response.status_code == 200:
                fission_meta = response.json()
                
                if 'managedFields' in fission_meta['metadata']:
                    fission_meta['metadata'].pop('managedFields')
                
                function_['fission_meta'] = fission_meta['metadata']
                function_['fission_spec'] = fission_meta['spec']
                function_['package'] = fission_meta['spec']['package']
                function_['func_uid'] = fission_meta['metadata']['uid']
                mongo.update('function', d, function_)
                
                if '_id' in function_:
                    function_.pop('_id')
                return jsonify(function_), 200
            else:
                return response.text, response.status_code
            
        else:
            return l, 406

        
    elif request.method == "DELETE":
        response = requests.delete(f"{fission_control}/v2/functions/{func_name}?namespace={user_name}")
  
        mongo.remove('function', d)


        return jsonify(d), response.status_code
    
@app.route(f"{PREFIX}/functions/<func_name>/test", methods=["GET","PUT", "DELETE"])
def user_functionsbyfunc_name_test(user_name, func_name):
    d = {'user_name':user_name, "func_name": func_name}
    

    rs = mongo.select('function', d)

    function_ = None
    
    for r in rs:
        r.pop('_id')
        function_ = r

    if function_ is None:
        abort(404, description=f"function[{func_name}] is not found.")


    p = subprocess.Popen(f"fission fn test --name {func_name} --namespace={user_name}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    b = p.communicate()
    t = ''

    for s in b:
        if s != None:
            s_ = s.decode('utf-8')
            t += s_

    return t, 200

    
@app.route(f"{PREFIX}/packages/upload", methods=["POST"])
def user_packages_upload(user_name):

    if request.method == "POST":
        files = request.files

        filenames = []

        for k in files:
            file = files[k]
            user_path = os.path.join(upload_path, user_name)
            filename = secure_filename(file.filename)
            os.makedirs(user_path, exist_ok=True)
            file.save(os.path.join(user_path, filename))

            filenames.append(filename)

        return jsonify(filenames), 200
    
@app.route(f"{PREFIX}/packages/filelist", methods=["GET"])
def user_packages_filelist(user_name):

    filenames = []
    user_path = os.path.join(upload_path, user_name)
    user_path = os.path.abspath(user_path)
    isExist = os.path.exists(user_path)

    if isExist:
        file_list = os.listdir(user_path)

        for filename in file_list:
            filenames.append(filename)
            
    return jsonify(filenames), 200

@app.route(f"{PREFIX}/packages", methods=["GET", "POST"])
def user_packages(user_name):

    user_path = os.path.join(upload_path, user_name)
    user_path = os.path.abspath(user_path)

    if request.method == "POST":
        if request.data == None:
            abort(406, description='content is empty.')
            
        package = json.loads(request.data.decode('utf8'))


        if 'pack_name' not in package:
            abort(406, description='pack_name is empty.')
        
        if 'env_name' not in package:
            abort(406, description='env_name is empty.')

        d = {'user_name':user_name, "env_name": package['env_name']}
    

        rs = mongo.select('environment', d)

        environment_ = None
    
        for r in rs:
            r.pop('_id')
            environment_ = r

        if environment_ is None:
            abort(404, description=f"environment[{package['env_name']}] is not found.")


        args = ''

        if 'buildcmd' in package:
            args += f"--buildcmd {package['buildcmd']} "

        if 'code' in package:

            p = package['code']
            if not p.startswith('http'):
                p = os.path.join(user_path, package['code'])
                isExist = os.path.exists(p)

                if isExist is False:
                    abort(404, description=f"{package['code']} is not found.")

            args += f"--code {p} "

        if 'sourcearchive' in package:
            '''
            sourcearchive = package['sourcearchive']
            if isinstance(sourcearchive, list) == False:
                abort(404, description=f"sourcearchive must be a list.")

            sa = []
            for s in sourcearchive:
                sa.append(os.path.join(user_path, s))

            args += f"--sourcearchive {sa} "
            '''
            p = os.path.join(user_path, package['sourcearchive'])
            isExist = os.path.exists(p)

            if isExist is False:
                abort(404, description=f"{package['sourcearchive']} is not found.")


            args += f"--sourcearchive {p} "

        if 'deployarchive' in package:
            
            '''
            deployarchive = package['deployarchive']
            if isinstance(deployarchive, list) == False:
                abort(404, description=f"deployarchive must be a list.")

            da = []
            for d in deployarchive:
                da.append(os.path.join(user_path, d))
            args += f"--deployarchive {da} "
            '''

            p = os.path.join(user_path, package['deployarchive'])
            isExist = os.path.exists(p)

            if isExist is False:
                abort(404, description=f"{package['deployarchive']} is not found.")
            
            args += f"--deployarchive {p} "



        package['user_name'] = user_name
            
        p = subprocess.Popen(f"fission package create --name {package['pack_name']} --env {package['env_name']} --namespace {user_name} {args}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    
        b = p.communicate()
        t = ''
        l = ''
        for s in b:
            if s != None:
                s_ = s.decode('utf-8')
                t += s_
                l = s_
   
        if 'Error:' not in l:
            response = requests.get(f"{fission_control}/v2/packages/{package['pack_name']}?namespace={user_name}", timeout=10)
            
            if response.status_code == 200:
                fission_meta = response.json()
                
                if 'managedFields' in fission_meta['metadata']:
                    fission_meta['metadata'].pop('managedFields')
                
                package['fission_meta'] = fission_meta['metadata']
                package['fission_spec'] = fission_meta['spec']
                package['fission_status'] = fission_meta['status']
                #package['package'] = fission_meta['spec']['package']
                package['pack_uid'] = fission_meta['metadata']['uid']
                mongo.insert('package', package)
                
                package.pop('_id')
                return jsonify(package), 201
            
            return response.text, response.status_code
        else:
            return l, 406
        
    elif request.method == "GET":
        d = {'user_name':user_name}
             
        rs = mongo.select('package', d)
        
        packages = []
        
        for r in rs:
            r.pop('_id')

            response = requests.get(f"{fission_control}/v2/packages/{r['pack_name']}?namespace={user_name}", timeout=10)
            
            if response.status_code == 200:
                fission_meta = response.json()
                
                if 'managedFields' in fission_meta['metadata']:
                    fission_meta['metadata'].pop('managedFields')
                
                r['fission_meta'] = fission_meta['metadata']
                r['fission_spec'] = fission_meta['spec']
                r['fission_status'] = fission_meta['status']
                r['pack_uid'] = fission_meta['metadata']['uid']


            packages.append(r)
            
        return jsonify(packages)



@app.route(f"{PREFIX}/packages/<pack_name>", methods=["GET","PUT", "DELETE"])
def user_packagesbyfunc_name(user_name, pack_name):
    
    d = {'user_name':user_name, "pack_name": pack_name}
    

    rs = mongo.select('package', d)

    package_ = None
    
    for r in rs:
        r.pop('_id')
        package_ = r

    if request.method == "GET" or request.method == "PUT":
        if package_ is None:
            abort(404, description=f"package[{pack_name}] is not found.")
        
    if request.method == "GET":

        response = requests.get(f"{fission_control}/v2/packages/{package_['pack_name']}?namespace={user_name}", timeout=10)
            
        if response.status_code == 200:
            fission_meta = response.json()
            
            if 'managedFields' in fission_meta['metadata']:
                fission_meta['metadata'].pop('managedFields')
            
            package_['fission_meta'] = fission_meta['metadata']
            package_['fission_spec'] = fission_meta['spec']
            package_['fission_status'] = fission_meta['status']
            package_['pack_uid'] = fission_meta['metadata']['uid']

        return jsonify(package_)
    elif request.method == "PUT":
        
        user_path = os.path.join(upload_path, user_name)
        user_path = os.path.abspath(user_path)

        if request.data == None:
            abort(406, description='content is empty.')
            
        package = json.loads(request.data.decode('utf8'))
        
        args = ''

        if 'buildcmd' in package:
            args += f"--buildcmd {package['buildcmd']} "

        if 'code' in package:

            p = package['code']
            if not p.startswith('http'):
                p = os.path.join(user_path, package['code'])
                isExist = os.path.exists(p)

                if isExist is False:
                    abort(404, description=f"{package['code']} is not found.")

            args += f"--code {p} "

        if 'sourcearchive' in package:

            p = os.path.join(user_path, package['sourcearchive'])
            isExist = os.path.exists(p)

            if isExist is False:
                abort(404, description=f"{package['sourcearchive']} is not found.")


            args += f"--sourcearchive {p} "

        if 'deployarchive' in package:

            p = os.path.join(user_path, package['deployarchive'])
            isExist = os.path.exists(p)

            if isExist is False:
                abort(404, description=f"{package['deployarchive']} is not found.")
            
            args += f"--deployarchive {p} "


        p = subprocess.Popen(f"fission package update --name {pack_name} --namespace={user_name} {args}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        b = p.communicate()
        t = ''
        l = ''
        for s in b:
            if s != None:
                s_ = s.decode('utf-8')
                t += s_
                l = s_

        if 'updated' in t:

            response = requests.get(f"{fission_control}/v2/packages/{pack_name}?namespace={user_name}", timeout=10)
            
            if response.status_code == 200:
                fission_meta = response.json()
                
                if 'managedFields' in fission_meta['metadata']:
                    fission_meta['metadata'].pop('managedFields')

                package_['fission_meta'] = fission_meta['metadata']
                package_['fission_spec'] = fission_meta['spec']
                package_['fission_status'] = fission_meta['status']
                package_['pack_uid'] = fission_meta['metadata']['uid']

                mongo.update('package', d, package_)
                
                if '_id' in package_:
                    package_.pop('_id')
                return jsonify(package_), 200
            else:
                return response.text, response.status_code
            
        else:
            return l, 406

        
    elif request.method == "DELETE":
        response = requests.delete(f"{fission_control}/v2/packages/{pack_name}?namespace={user_name}")
        
        mongo.remove('package', d)

        return jsonify(d), response.status_code
    


@app.route(f"{PREFIX}/triggers", methods=["GET", "POST"])
def user_triggers(user_name):

    if request.method == "POST":
        if request.data == None:
            abort(406, description='content is empty.')
            
        trigger = json.loads(request.data.decode('utf8'))
        
        if 'trig_name' not in trigger:
            abort(406, description='trig_name is empty.')

        if 'trig_type' not in trigger:
            abort(406, description='trig_type is empty.')

        trigger['user_name'] = user_name
        trigger['trig_type'] = trigger['trig_type'].lower()

        t_type = 'http'
        if 'httptrigger' == trigger['trig_type']:
            t_type = 'http'
        else:
            t_type = 'messagequeue'

        args = ''

        if 'function' in trigger:
            args += f"--function {trigger['function']} "

        if 'method' in trigger:
            args += f"--method {trigger['method']} "

        if 'url' in trigger:
            args += f"--url {trigger['url']} "

        if 'createingress' in trigger:
            args += f"--createingress {trigger['createingress']} "

        if 'mqtype' in trigger:
            args += f"--mqtype {trigger['mqtype']} "
        
        if 'mqtkind' in trigger:
            args += f"--mqtkind {trigger['mqtkind']} "

        if 'topic' in trigger:
            args += f"--topic {trigger['topic']} "

        if 'resptopic' in trigger:
            args += f"--resptopic {trigger['resptopic']} "

        if 'errortopic' in trigger:
            args += f"--errortopic {trigger['errortopic']} "

        if 'maxretries' in trigger:
            args += f"--maxretries {trigger['maxretries']} "

        if 'metadata' in trigger:

            metadata = trigger['metadata']
            if isinstance(metadata, list) == False:
                abort(404, description=f"metadata must be a list.")

            for md in metadata:
                args += f"--metadata {md} "

        if 'cooldownperiod' in trigger:
            args += f"--cooldownperiod {trigger['cooldownperiod']} "

        if 'pollinginterval' in trigger:
            args += f"--pollinginterval {trigger['pollinginterval']} "

        if 'secret' in trigger:
            args += f"--secret {trigger['secret']} "

        
        
        p = subprocess.Popen(f"fission {trigger['trig_type']} create --name {trigger['trig_name']} --namespace {user_name} {args}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    
        b = p.communicate()
        t = ''
        l = ''
        for s in b:
            if s != None:
                s_ = s.decode('utf-8')
                t += s_
                l = s_
   
        if 'Error:' not in l:
            u = f"{fission_control}/v2/{trigger['trig_type']}s/{trigger['trig_name']}?namespace={user_name}"
            response = requests.get(f"{fission_control}/v2/triggers/{t_type}/{trigger['trig_name']}?namespace={user_name}", timeout=10)
            
            if response.status_code == 200:
                fission_meta = response.json()
                
                if 'managedFields' in fission_meta['metadata']:
                    fission_meta['metadata'].pop('managedFields')
                
                trigger['fission_meta'] = fission_meta['metadata']
                trigger['fission_spec'] = fission_meta['spec']
                trigger['trig_uid'] = fission_meta['metadata']['uid']
                mongo.insert('trigger', trigger)
                
                if t_type == 'http':
                    trigger['url'] = route_url+trigger['url']
                trigger.pop('_id')
                return jsonify(trigger), 201
            
            return response.text, response.status_code
        else:
            return l, 406
        
    elif request.method == "GET":
        d = {'user_name':user_name}
             
        rs = mongo.select('trigger', d)
        
        triggers = []
        
        for r in rs:
            r.pop('_id')

            t_type = 'http'
            if 'httptrigger' == r['trig_type']:
                t_type = 'http'
            else:
                t_type = 'messagequeue'

            response = requests.get(f"{fission_control}/v2/triggers/{t_type}/{r['trig_name']}?namespace={user_name}", timeout=10)

            if response.status_code == 200:
                fission_meta = response.json()
                
                if 'managedFields' in fission_meta['metadata']:
                    fission_meta['metadata'].pop('managedFields')
                
                r['fission_meta'] = fission_meta['metadata']
                r['fission_spec'] = fission_meta['spec']
                r['trig_uid'] = fission_meta['metadata']['uid']

                if t_type == 'http':
                    r['url'] = route_url+r['url']

            triggers.append(r)
            
        return jsonify(triggers)
    

@app.route(f"{PREFIX}/triggers/<trig_name>", methods=["GET","PUT", "DELETE"])
def user_triggersbyfunc_name(user_name, trig_name):
    
    d = {'user_name':user_name, "trig_name": trig_name}
    

    rs = mongo.select('trigger', d)

    trigger_ = None
    
    for r in rs:
        r.pop('_id')
        trigger_ = r

    t_type = 'http'

    if trigger_ is not None:
        if 'httptrigger' == r['trig_type']:
            t_type = 'http'
        else:
            t_type = 'messagequeue'

    if request.method == "GET" or request.method == "PUT":
        if trigger_ is None:
            abort(404, description=f"trigger[{trig_name}] is not found.")
        
    if request.method == "GET":

        response = requests.get(f"{fission_control}/v2/triggers/{t_type}/{trigger_['trig_name']}?namespace={user_name}", timeout=10)
            
        if response.status_code == 200:
            fission_meta = response.json()
            
            if 'managedFields' in fission_meta['metadata']:
                fission_meta['metadata'].pop('managedFields')
            
            trigger_['fission_meta'] = fission_meta['metadata']
            trigger_['fission_spec'] = fission_meta['spec']
            trigger_['trig_uid'] = fission_meta['metadata']['uid']
            if t_type == 'http':
                trigger_['url'] = route_url+trigger_['url']

        return jsonify(trigger_)
    elif request.method == "PUT":

        if request.data == None:
            abort(406, description='content is empty.')
            
        trigger = json.loads(request.data.decode('utf8'))
        
        args = ''

        if 'function' in trigger:
            args += f"--function {trigger['function']} "

        if 'method' in trigger:
            args += f"--method {trigger['method']} "

        if 'url' in trigger:
            args += f"--url {trigger['url']} "

        if 'createingress' in trigger:
            args += f"--createingress {trigger['createingress']} "

        if 'mqtype' in trigger:
            args += f"--mqtype {trigger['mqtype']} "
        
        if 'mqtkind' in trigger:
            args += f"--mqtkind {trigger['mqtkind']} "

        if 'topic' in trigger:
            args += f"--topic {trigger['topic']} "

        if 'resptopic' in trigger:
            args += f"--resptopic {trigger['resptopic']} "

        if 'errortopic' in trigger:
            args += f"--errortopic {trigger['errortopic']} "

        if 'maxretries' in trigger:
            args += f"--maxretries {trigger['maxretries']} "

        if 'metadata' in trigger:

            metadata = trigger['metadata']
            if isinstance(metadata, list) == False:
                abort(404, description=f"metadata must be a list.")

            for md in metadata:
                args += f"--metadata {md} "

        if 'cooldownperiod' in trigger:
            args += f"--cooldownperiod {trigger['cooldownperiod']} "

        if 'pollinginterval' in trigger:
            args += f"--pollinginterval {trigger['pollinginterval']} "

        if 'secret' in trigger:
            args += f"--secret {trigger['secret']} "


        p = subprocess.Popen(f"fission {r['trig_type']} update --name {trig_name} --namespace={user_name} {args}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        b = p.communicate()
        t = ''
        l = ''
        for s in b:
            if s != None:
                s_ = s.decode('utf-8')
                t += s_
                l = s_

        if 'updated' in t:

            response = requests.get(f"{fission_control}/v2/triggers/{t_type}/{trig_name}?namespace={user_name}", timeout=10)
            
            if response.status_code == 200:
                fission_meta = response.json()
                
                if 'managedFields' in fission_meta['metadata']:
                    fission_meta['metadata'].pop('managedFields')

                trigger_['fission_meta'] = fission_meta['metadata']
                trigger_['fission_spec'] = fission_meta['spec']
                trigger_['trig_uid'] = fission_meta['metadata']['uid']

                mongo.update('trigger', d, trigger_)

                if t_type == 'http':
                    trigger_['url'] = route_url+trigger_['url']
                
                if '_id' in trigger_:
                    trigger_.pop('_id')
                return jsonify(trigger_), 200
            else:
                return response.text, response.status_code
            
        else:
            return l, 406

        
    elif request.method == "DELETE":

        t_type = 'http'

        if trigger_ is not None:
            if 'httptrigger' == r['trig_type']:
                t_type = 'http'
            else:
                t_type = 'messagequeue'

            response = requests.delete(f"{fission_control}/v2/triggers/{t_type}/{trig_name}?namespace={user_name}")
        else:
            response = requests.delete(f"{fission_control}/v2/triggers/http/{trig_name}?namespace={user_name}")
            response = requests.delete(f"{fission_control}/v2/triggers/messagequeue/{trig_name}?namespace={user_name}")
        
        mongo.remove('trigger', d)

        return jsonify(d), response.status_code