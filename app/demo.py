import os
import subprocess
import functools
import re
from time import sleep

from subprocess import CalledProcessError

from flask import (
  Blueprint, flash, g, redirect, render_template, request, session, url_for
)

bp = Blueprint('/', __name__, url_prefix='/')

def getOStype():
  try:
    ds = subprocess.check_output('which yum', shell=True)
    return 'yum'
  except:
    try:
      ds = subprocess.check_output('which apt', shell=True)
      return 'apt'
    except:
      return ''


@bp.route('/', methods=('GET', 'POST'))
def login():
  return render_template('demo/main.html')

@bp.route('/docker')
def getDocker():
  dStr = getDockerStatus()
  dcStr = getDockerComposeStatus()
  dcList = []
  dStatus = checkDockerRunning()
  if dStatus == 'True':
    try:
      dcList = getDockerComposePs()
    except:
      dStatus = 'False'
  ag = checkAgent()
  agStatus = 'N/A'
  lg = checkLoadGen()
  if ag :
    agStatus = 'Error'
    try:
      agStatus = checkAgentRunning()
    except:
      agStatus = 'Error'
  return {'docker':[{'comp':'docker', 'ver':dStr, 'status':dStatus}, {'comp':'docker compose', 'ver':dcStr, 'status':'N/A'}, ], 'ps':dcList, 'agent':[{'ps':'instana agent', 'status':agStatus}], 'agentinstalled':str(ag), 'loadgen':lg}

def checkDockerRunning():
  try:
    ds = subprocess.check_output('ps -ef | grep dockerd | grep -v grep', shell=True)
    return 'True'
  except:
    return 'False'

def getDockerStatus():
#    ds = os.system('docker --version')
#    print(ds)
  ds = subprocess.check_output('sudo docker --version', shell=True)
  ds = ds.decode('utf-8')
  if not ds.startswith("Docker"):
    ds = 'Docker is not installed'
  return ds

def getDockerComposeStatus():
#    ds = os.system('docker --version')
#    print(ds)
  ds = subprocess.check_output('sudo docker-compose --version', shell=True)
  ds = ds.decode('utf-8')
  if not ds.startswith("docker-compose"):
    ds = 'Docker is not installed'
  return ds

plist = [
'cart_1',
'catalogue_1',
'dispatch_1',
'mongodb_1',
'mysql_1',
'payment_1',
'rabbitmq_1',
'ratings_1',
'redis_1',
'shipping_1',
'user_1',
'web_1',]

def startDockerD():
  ds = subprocess.check_output('sudo systemctl start docker', shell=True)
  ds = ds.decode('utf-8')
  return ds

def checkAgent():
  return str(os.path.isfile('/opt/instana/agent/bin/start'))

def checkAgentRunning():
  try:
    ds = subprocess.check_output('sudo /opt/instana/agent/bin/status', shell=True)
    ds = ds.decode('utf-8')
    return ds
  except CalledProcessError as ex:
    print(ex)
    return 'Error'

def getDockerComposePs():
  os.chdir(os.getenv('ROBOT_SHOP_PATH', '/Users/shpark/Downloads/robot-shop-master'))
  ds = subprocess.check_output('sudo docker-compose ps', shell=True)
  ds = ds.decode('utf-8')
  dsList = ds.split("\n")
  dsMap = []
  for str in dsList:
    tempStr = re.sub(' +', ' ', str)
    strs = tempStr.split(" ")
    if len(strs) >= 2 :
      for p in plist:
        if strs[0].endswith(p) and 'Up' in strs:
          dsMap.append({'ps':strs[0], 'status':'Up'})
  return dsMap

@bp.route('/dockerstart')
def startDocker():
  retMsg = False
  dStr =  getDockerStatus();
  dcStr =  getDockerComposeStatus();
  try:
    subprocess.check_output('sudo systemctl start docker', shell=True)
    dStatus = checkDockerRunning()
    return {'docker':[{'comp':'docker', 'ver':dStr, 'status':dStatus}, {'comp':'docker compose', 'ver':dcStr, 'status':'N/A'}, ]}
  except CalledProcessError as ex:
    print(ex)
    return {'docker':[{'comp':'docker', 'ver':dStr, 'status':'False'}, {'comp':'docker compose', 'ver':dcStr, 'status':'N/A'}, ]}

@bp.route('/appstart')
def startDockerCompose():
  os.chdir(os.getenv('ROBOT_SHOP_PATH', '/Users/shpark/Downloads/robot-shop-master'))
  subprocess.check_output('sudo docker-compose up -d', shell=True)
  dcList = []
  dStatus = checkDockerRunning()
  if dStatus == 'True':
    try:
      dcList = getDockerComposePs()
    except:
      dStatus = 'False'
  return {'ps':dcList}

@bp.route('/appstop')
def stopDockerCompose():
  os.chdir(os.getenv('ROBOT_SHOP_PATH', '/Users/shpark/Downloads/robot-shop-master'))
  subprocess.check_output('sudo docker-compose down', shell=True)
  dcList = []
  dStatus = checkDockerRunning()
  if dStatus == 'True':
    try:
      dcList = getDockerComposePs()
    except:
      dStatus = 'False'
  return {'ps':dcList}

def on_json_loading_failed_return_dict(e):  
  return {}
@bp.route('/installagent', methods=['POST'])
def installAgent():
  request.on_json_loading_failed = on_json_loading_failed_return_dict
  data = request.get_json()
  print(data)
  key = data['key']
  ep = data['endpoint'].strip()
  
  rPath = os.getenv('ROBOT_SHOP_PATH', '/Users/shpark/Downloads/robot-shop-master')
  os.chdir(rPath)
  cmd1 = 'curl -o setup_agent.sh https://setup.instana.io/agent'
  cmd2 = 'chmod 700 ' + rPath + '/setup_agent.sh'
  cmd3 = 'sudo ' + rPath + '/setup_agent.sh -a \'' + key + '\' -t dynamic -l us -y'
  if len(ep) > 0:
    cmd3 = 'sudo ' + rPath + '/setup_agent.sh -a \'' + key + '\' -t dynamic -e ' + ep + ' -y'
  subprocess.check_output(cmd1, shell=True)
  subprocess.check_output(cmd2, shell=True)
  subprocess.check_output(cmd3, shell=True)
  ag = checkAgent()
  return {'agent':[{'ps':'instana agent',  'status':'Not Running'}], 'agentinstalled':str(ag)}

@bp.route('/removeagent')
def removeAgent():
  try:
    print('remove agent 1')
    ds = subprocess.check_output('sudo /opt/instana/agent/bin/status', shell=True)
    print('remove agent 2')
    ag = checkAgent()
    return {'agent':[{'ps':'instana agent',  'status':'Not Running'}], 'agentinstalled':str(ag)}
  except:
    try:
      print('remove agent 3')
      if packageType == 'yum':
        ds = subprocess.check_output('sudo yum list installed instana*', shell=True)
        sleep(1)
        ds = subprocess.check_output('sudo rm -rf /opt/instana', shell=True)
        ds = subprocess.check_output('sudo yum -y remove instana-agent-dynamic.x86_64', shell=True)
        return {'agent':[{'ps':'instana agent',  'status':'Not Running'}], 'agentinstalled':'False'}
      else:
        ds = subprocess.check_output('sudo apt list --installed instana*', shell=True)
        sleep(1)
        ds = subprocess.check_output('sudo rm -rf /opt/instana', shell=True)
        ds = subprocess.check_output('sudo apt -y purge instana-agent-dynamic.x86_64', shell=True)
        return {'agent':[{'ps':'instana agent',  'status':'Not Running'}], 'agentinstalled':'False'}

    except:
      ag = checkAgent()
      return {'agent':[{'ps':'instana agent',  'status':'Not Running'}], 'agentinstalled':str(ag)}


@bp.route('/startagent')
def startAgent():
  print('startagent 1')
  msg = []
  ag = checkAgent()
  try:
    os.chdir('/opt/instana/agent/bin')
    ds = subprocess.check_output('sudo /opt/instana/agent/bin/start', shell=True)
    sleep(3)
    ds = subprocess.check_output('sudo /opt/instana/agent/bin/status', shell=True)
    print('startagent 2')
    ds = ds.decode('utf-8')
    msg.append('Started successfully.')
    return {'agent':[{'ps':'instana agent', 'status':ds}], 'installed':str(ag), 'message':msg}
  except CalledProcessError as ex:
    print('startagent 3')
    print(ex)
    msg.append('fail to start ' + str(ex))
    return {'agent':[{'ps':'instana agent', 'status':'Unknown'}], 'agentinstalled':str(ag), 'message':msg}
  
@bp.route('/stopagent')
def stopAgent():
  msg = []
  ag = checkAgent()
  try:
    os.chdir('/opt/instana/agent/bin')
    ds = subprocess.check_output('sudo /opt/instana/agent/bin/stop', shell=True)
    sleep(3)
    try:
      ds = subprocess.check_output('sudo /opt/instana/agent/bin/status', shell=True)
      msg.append('fail to stop ' + str(ex))
      return {'agent':[{'ps':'instana agent', 'status':'Unknown'}], 'agentinstalled':str(ag), 'message':msg}
    except:
      ds = ds.decode('utf-8')
      msg.append('Stopped successfully.')
      return {'agent':[{'ps':'instana agent', 'status':ds}], 'installed':str(ag), 'message':msg}
  except CalledProcessError as ex:
    print(ex)
    msg.append('fail to stop ' + str(ex))
    return {'agent':[{'ps':'instana agent', 'status':'Unknown'}], 'agentinstalled':str(ag), 'message':msg}
  
@bp.route('/startloadgen')
def startLoadGen():
  try:
    ds = subprocess.check_output('sudo docker run -it -d --name loadgen --rm --network=host -e HOST=http://localhost:8080 -e NUM_CLIENTS=1 -e RUN_TIME=0 -e SILENT=0 -e ERROR=0 robotshop/rs-load:0.4.12', shell=True)
    sleep(3)
    return { 'loadgen':checkLoadGen() }
  except:
    return {'loadgen':[{'ps':'load generator', 'status':'Unknown'}]}

def checkLoadGen():
  try:
    ds = subprocess.check_output('sudo docker inspect loadgen', shell=True)
    return [{'ps':'load generator', 'status':'Running'}]
  except:
    return [{'ps':'load generator', 'status':'Not Running'}]

@bp.route('/stoploadgen')
def stopLoadGen():
  try:
    subprocess.check_output('sudo docker stop loadgen', shell=True)
    sleep(3)
    return { 'loadgen':checkLoadGen() }
  except:
    return {'loadgen':[{'ps':'load generator', 'status':'Unknown'}]}
