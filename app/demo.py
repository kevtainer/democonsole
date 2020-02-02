import os
import sys
import subprocess
import functools
import re
import json
import docker
import traceback
from os import path
from time import sleep

from subprocess import CalledProcessError, STDOUT
from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)

plist = ['cart_1','catalogue_1','dispatch_1','mongodb_1','mysql_1','payment_1','rabbitmq_1','ratings_1','redis_1','shipping_1','user_1','web_1',]
bp = Blueprint('/', __name__, url_prefix='/')

def on_json_loading_failed_return_dict(e):  
  return {}

@bp.route('/', methods=('GET', 'POST'))
def login():
  return render_template('demo/main.html')

## docker-compose (local)

@bp.route('/docker_info')
def docker_info():
  docker_status_obj = docker_status()
  compose_status_obj = compose_status()
  sys_info_obj = system_info()

  return {
    'docker':[
        docker_status_obj,
        compose_status_obj,
        sys_info_obj,
    ], 
    'dc_rs': dc_rs_status(),
    'dc_instana': [ dc_instana_status() ],
    'dc_load': [ dc_load_status() ]
  }

def system_info():
  try:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    info = client.info()

    memStr = "Memory: " + humanbytes(info['MemTotal'])
    memFail = False
    if info['MemTotal'] < 4000000000:
      memMsg = memStr + " (WARNING)"
      memFail = True
    else:
      memMsg = memStr
    
    cpuStr = "Cores: " + str(info['NCPU'])
    cpuFail = False
    if info['NCPU'] < 4:
      cpuMsg = cpuStr + " (WARNING)"
      cpuFail = True
    else:
      cpuMsg = cpuStr

    prependMsg = ""
    if cpuFail or memFail:
      status = False
      prependMsg = "WARNING: Insufficient Resources -- "
    else:
      status = True

    return {'comp': 'sysinfo', 'status':status, 'info': prependMsg + cpuMsg + ", " + memMsg }
  except:
    return {'comp': 'sysinfo', 'status':False, 'info':'unknown' }

def humanbytes(B):
   'Return the given bytes as a human friendly KB, MB, GB, or TB string'
   B = float(B)
   KB = float(1024)
   MB = float(KB ** 2) # 1,048,576
   GB = float(KB ** 3) # 1,073,741,824
   TB = float(KB ** 4) # 1,099,511,627,776

   if B < KB:
      return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
   elif KB <= B < MB:
      return '{0:.2f} KB'.format(B/KB)
   elif MB <= B < GB:
      return '{0:.2f} MB'.format(B/MB)
   elif GB <= B < TB:
      return '{0:.2f} GB'.format(B/GB)
   elif TB <= B:
      return '{0:.2f} TB'.format(B/TB)

def docker_status():
  try:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    ver = client.version()
    return {'comp': 'docker', 'status':True, 'info':'Docker version: ' + ver['Version'] + ', os: ' + ver['Os'] + ', kernel: ' + ver['KernelVersion'] }
  except:
    return {'comp': 'docker', 'status':False, 'info':'unknown' }

def compose_status():
  command = ["docker-compose", "--version"]
  try:
    result = subprocess.check_output(command, stderr=STDOUT).decode()
    return {'comp': 'docker-compose', 'status':True, 'info':result }
  except:
    return {'comp': 'docker-compose', 'status':False, 'info':'unknown' }

def dc_instana_status():
  return {
        'comp':'instana agent',
        'installed': dc_check_agent_installed(),
        'status': dc_check_agent_running()
    }

def dc_check_agent_installed():
  try:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    client.containers.get("instana-agent")
    return True
  except:
    return False

def dc_check_agent_running():
  try:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    instana_agent_obj = client.containers.get("instana-agent")
    return instana_agent_obj.attrs['State']['Running']
  except:
    return False

def dc_rs_status():
  dsMap = []
  client = docker.DockerClient(base_url='unix://var/run/docker.sock')

  for str in plist:
    try:
      rs_cont_obj = client.containers.get("robot-shop_" + str)
      dsMap.append({'comp':str, 'status':rs_cont_obj.attrs['State']['Running']})
    except:
      pass

  return dsMap

@bp.route('/dc_start_rs')
def dc_start_rs():
  pull_command = ["docker-compose", "pull"]
  up_command = ["docker-compose", "up", "-d", "--no-build"]
  try:
    os.chdir(os.getenv('ROBOT_SHOP_PATH', '/robot-shop'))

    subprocess.call(pull_command)
    subprocess.call(up_command)
  except:
    pass

  return { 'dc_rs': dc_rs_status() }

@bp.route('/dc_stop_rs')
def dc_stop_rs():
  os.chdir(os.getenv('ROBOT_SHOP_PATH', '/robot-shop'))

  down_command = ["docker-compose", "down"]
  try:
    subprocess.call(down_command)
  except:
    pass

  return { 'dc_rs': dc_rs_status() }

@bp.route('/dc_install_agent', methods=['POST'])
def dc_install_agent():
  request.on_json_loading_failed = on_json_loading_failed_return_dict
  data = request.get_json()

  ## the management console in instana drops a bunch of whitespace in the key, which will cause registry login to fail
  key = re.sub(r"[\n\t\s]*", "", data['key'])
  name = data['name']
  ep = data['endpoint'].strip()

  if not ep:
    ep = os.getenv('DEFAULT_INSTANA_ENDPOINT', 'ingress-red-saas.instana.io')
  if not name:
    name = os.getenv('DEFAULT_CLUSTER_NAME', 'democonsole-dc')

  try:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    client.login('_', password=key, registry='containers.instana.io')
    client.images.pull('containers.instana.io/instana/release/agent/static:latest')

    if dc_check_agent_installed():
      dc_remove_agent()

    client.containers.run('containers.instana.io/instana/release/agent/static:latest',
                          name="instana-agent",
                          detach=True,
                          network_mode="host",
                          pid_mode="host",
                          privileged=True,
                          environment=[
                            "INSTANA_AGENT_ENDPOINT_PORT=443",
                            "INSTANA_AGENT_ENDPOINT=" + ep,
                            "INSTANA_AGENT_KEY=" + key,
                            "INSTANA_ZONE=" + name
                          ],
                          volumes={
                            '/var/run': {'bind': '/var/run', 'mode': 'ro'},
                            '/run': {'bind': '/run', 'mode': 'ro'},
                            '/dev': {'bind': '/dev', 'mode': 'ro'},
                            '/sys': {'bind': '/sys', 'mode': 'ro'},
                            '/var/log': {'bind': '/var/log', 'mode': 'ro'}
                          }
    )
    sleep(3)
  except:
    pass

  return { 'dc_instana': [ dc_instana_status() ] }

@bp.route('/dc_stop_agent')
def dc_stop_agent():
  try:
    apiClient = docker.APIClient(base_url='unix://var/run/docker.sock')
    apiClient.stop('instana-agent', 10)
    sleep(3)
  except:
    pass

  return { 'dc_instana': [ dc_instana_status() ] }

@bp.route('/dc_start_agent')
def dc_start_agent():
  try:
    apiClient = docker.APIClient(base_url='unix://var/run/docker.sock')
    apiClient.start('instana-agent')
    sleep(3)
  except:
    pass

  return { 'dc_instana': [ dc_instana_status() ] }

@bp.route('/dc_remove_agent')
def dc_remove_agent():
  try:
    apiClient = docker.APIClient(base_url='unix://var/run/docker.sock')
    apiClient.remove_container('instana-agent', force=True)
    sleep(3)
  except:
    pass

  return { 'dc_instana': [ dc_instana_status() ] }

@bp.route('/dc_start_load')
def dc_start_load():
  try:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    client.images.pull('robotshop/rs-load:0.4.12')

    client.containers.run('robotshop/rs-load:0.4.12',
                          name="loadgen",
                          detach=True,
                          remove=True,
                          network_mode="host",
                          environment=[
                            "HOST=http://localhost:8080",
                            "NUM_CLIENTS=1",
                            "RUN_TIME=0",
                            "SILENT=0",
                            "ERROR=0"
                          ]
    )
    sleep(3)
  except:
    pass

  return { 'dc_load': [ dc_load_status() ] }

@bp.route('/dc_stop_load')
def dc_stop_load():
  try:
    apiClient = docker.APIClient(base_url='unix://var/run/docker.sock')
    apiClient.stop('loadgen', 10)
    sleep(3)
  except:
    pass

  return { 'dc_load': [ dc_load_status() ] }

def dc_check_load():
  try:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    client.containers.get("loadgen")
    return True
  except:
    pass

  return False

def dc_load_status():
  return { 'comp':'load generator', 'status': dc_check_load() }

## k8s (cloud)

@bp.route('/k8s_info')
def k8s_info():
  k8s_status_obj = k8s_status()

  return {
    'k8s':[
      k8s_status_obj['client'],
      k8s_status_obj['server'],
      k8s_status_obj['helm']
    ],
    'k8s_rs': [ k8s_rs_status() ],
    'k8s_load': [ k8s_load_status() ],
    'k8s_instana': k8s_instana_status()
  }

def k8s_status():
  client_obj = { 'comp': 'kubectl (client)', 'info': 'n/a', 'status': False }
  server_obj = { 'comp': 'kubectl (server)', 'info': 'n/a', 'status': False }
  helm_obj   = { 'comp': 'helm', 'info': 'n/a', 'status': False }

  try:
    client_cmd = [ "kubectl", "--client", "-o=json", "version" ]
    result = subprocess.check_output(client_cmd, stderr=STDOUT).decode()
    client_json = json.loads(result)

    client_obj['info'] = client_json['clientVersion']['gitVersion'] + " (" + client_json['clientVersion']['platform'] + ")"
    client_obj['status'] = True
  except:
    pass

  try:
    server_cmd = ["kubectl", "--kubeconfig=/config/kubeconfig", "-o=json", "version"]
    result = subprocess.check_output(server_cmd, stderr=STDOUT).decode()
    server_json = json.loads(result)

    server_obj['info'] = server_json['serverVersion']['gitVersion'] + " (" + server_json['serverVersion']['platform'] + ")"
    server_obj['status'] = True
  except:
    pass

  try:
    helm_cmd = ["helm", "version", "--short"]
    res = subprocess.check_output(helm_cmd, stderr=STDOUT).decode()
    helm_obj['info'] = res
    helm_obj['status'] = True
  except:
    pass

  return { 'helm': helm_obj, 'client': client_obj, 'server': server_obj }

def k8s_rs_status():
  try:
    command = ["helm", "--output=json", "--kubeconfig=/config/kubeconfig", "--namespace=robot-shop", "status", "robot-shop"]
    result = subprocess.check_output(command, stderr=STDOUT).decode()
    res_json = json.loads(result)
    if res_json['info']['status'] == 'deployed':
      status_bool = True
    else:
      status_bool = False

    return { 'comp': res_json['name'], 'info': res_json['version'], 'status': status_bool }
  except:
    return { 'comp': 'not installed', 'info': 'n/a', 'status': False }

def k8s_instana_status():
  try:
    command = ["helm", "--output=json", "--kubeconfig=/config/kubeconfig", "--namespace=instana-agent", "status", "instana-agent"]
    result = subprocess.check_output(command, stderr=STDOUT).decode()
    res_json = json.loads(result)
    if res_json['info']['status'] == 'deployed':
      return True
  except:
    pass

  return False

def k8s_load_status():
  try:
    command = ["kubectl", "--kubeconfig=/config/kubeconfig", "--namespace=robot-shop", "get", "deployments", "load"]
    subprocess.check_call(command)
    return { 'comp': 'deployment.apps/load', 'status': True }
  except:
    return { 'comp': 'deployment.apps/load', 'status': False }

@bp.route('/k8s_start_rs')
def k8s_start_rs():
  rs_base_dir = os.getenv('ROBOT_SHOP_PATH', '/robot-shop')
  os.chdir(rs_base_dir + '/K8s/helm')

  result = subprocess.call(["kubectl", "--kubeconfig=/config/kubeconfig", "get", "namespace", "robot-shop"])
  
  if result == 1:
    result = subprocess.call(["kubectl", "--kubeconfig=/config/kubeconfig", "create", "namespace", "robot-shop"])

    if result == 1:
      return { 'error':'unable to create robot-shop namespace' }

  command = ["helm", "--kubeconfig=/config/kubeconfig", "--namespace=robot-shop", "install", "robot-shop", "."]
  subprocess.call(command)
  sleep(3)
  return k8s_info()

@bp.route('/k8s_install_agent', methods=['POST'])
def k8s_install_agent():
  request.on_json_loading_failed = on_json_loading_failed_return_dict
  data = request.get_json()

  ## the management console in instana drops a bunch of whitespace in the key, which will cause registry login to fail
  key = re.sub(r"[\n\t\s]*", "", data['key'])
  name = data['name']
  ep = data['endpoint'].strip()

  if not key:
    return {'error': 'agent key is not defined'}
  if not ep:
    ep = os.getenv('DEFAULT_INSTANA_ENDPOINT', 'ingress-red-saas.instana.io')
  if not name:
    name = os.getenv('DEFAULT_CLUSTER_NAME', 'democonsole-k8s')

  result = subprocess.call(["kubectl", "--kubeconfig=/config/kubeconfig", "get", "namespace", "instana-agent"])

  if result == 1:
    result = subprocess.call(["kubectl", "--kubeconfig=/config/kubeconfig", "create", "namespace", "instana-agent"])

    if result == 1:
      return {'error':'unable to create instana-agent namespace'}

  ## install the registry secret for the static agent
  ## containers.instana.io/instana/release/agent/static:latest
  #command = [
  #    "kubectl", "--kubeconfig=/config/kubeconfig",
  #    "--namespace=instana-agent",
  #    "create", "secret", "docker-registry", "regcred",
  #    "--docker-server=https://containers.instana.io",
  #    "--docker-username=_",
  #    "--docker-password=" + key
  #]
  #subprocess.call(command)

  try:
    command = ["helm", "repo", "add", "stable", "https://kubernetes-charts.storage.googleapis.com/"]
    subprocess.check_call(command)
    command = ["helm", "repo", "update"]
    subprocess.check_call(command)
    command = [
      "helm", "--kubeconfig=/config/kubeconfig", "--namespace=instana-agent",
      "install", "instana-agent", "stable/instana-agent",
      "--set", "agent.key=" + key,
      "--set", "agent.endpointHost=" + ep,
      "--set", "cluster.name=" + name,
      "--set", "agent.endpointPort=443"
      #"--set", "agent.image.name=containers.instana.io/instana/release/agent/static"
    ]
    subprocess.check_call(command)
    sleep(3)
    ## patch the service account to enable agent pull
    #command = ["kubectl", "--kubeconfig=/config/kubeconfig", "--namespace=instana-agent",
    #"patch", "serviceaccount", "instana-agent", "-p", "{\"imagePullSecrets\":[{\"name\":\"regcred\"}]}"]
    #subprocess.check_call(command)
  except:
    pass

  return k8s_info()

@bp.route('/k8s_remove_agent')
def k8s_remove_agent():
  command = ["helm", "--kubeconfig=/config/kubeconfig", "--namespace=instana-agent", "uninstall", "instana-agent"]
  subprocess.call(command)
  sleep(3)
  subprocess.call(["kubectl", "--kubeconfig=/config/kubeconfig", "delete", "namespace", "instana-agent"])
  #command = ["kubectl", "--kubeconfig=/config/kubeconfig", "--namespace=instana-agent", "delete", "secret/regcred"]
  #subprocess.call(command)
  return k8s_info()

@bp.route('/k8s_stop_rs')
def k8s_stop_rs():
  command = ["helm", "--kubeconfig=/config/kubeconfig", "--namespace=robot-shop", "uninstall", "robot-shop"]
  subprocess.call(command)
  sleep (3)
  subprocess.call(["kubectl", "--kubeconfig=/config/kubeconfig", "delete", "namespace", "robot-shop"])
  return k8s_info()

@bp.route('/k8s_start_load')
def k8s_start_load():
  rs_base_dir = os.getenv('ROBOT_SHOP_PATH', '/robot-shop')
  os.chdir(rs_base_dir + '/K8s')

  command = ["kubectl", "--kubeconfig=/config/kubeconfig", "--namespace=robot-shop", "create", "-f", "load-deployment.yaml"]
  subprocess.call(command)
  sleep(3)

  return k8s_info()

@bp.route('/k8s_stop_load')
def k8s_stop_load():
  rs_base_dir = os.getenv('ROBOT_SHOP_PATH', '/robot-shop')
  os.chdir(rs_base_dir + '/K8s')

  command = ["kubectl", "--kubeconfig=/config/kubeconfig", "--namespace=robot-shop", "delete", "-f", "load-deployment.yaml"]
  subprocess.call(command)
  sleep(3)

  return k8s_info()

@bp.route('/k8s_add_config', methods=['POST'])
def k8s_add_config():
  request.on_json_loading_failed = on_json_loading_failed_return_dict
  data = request.get_json()

  kubeconfig = data['kubeconfig']

  try:
    kc_file_obj = open("/config/kubeconfig", "w")
    kc_file_obj.write(kubeconfig)
    kc_file_obj.close()
  except:
    pass

  return k8s_info()

@bp.route('/k8s_del_config')
def k8s_del_config():
  try:
    os.remove("/config/kubeconfig")
  except:
    print('failed removing kubeconfig')
    pass

  return k8s_info()
