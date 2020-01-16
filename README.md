# Demo Console
<img width="1125" alt="democonsole" src="https://user-images.githubusercontent.com/16640750/72549779-af178d80-38d4-11ea-9f68-e313d2d673dc.png">

## Prerequisites
### softwate installation
<li> nginx
<li> docker
<li> docker-compose

## Steps

### Download robot-shop
git clone https://github.com/instana/robot-shop.git

### Download this repository
git clone https://github.com/ShaunPark/democonsole.git

### update
sudo apt-get update

### install pip3, uwsgi
sudo apt-get install python3-dev python3-pip python3-setuptools
<br>sudo -H pip3 install --upgrade pip
<br>sudo -H pip3 install wheel
<br>sudo -H pip3 install uwsgi
<br>sudo apt-get install uwsgi-plugin-python

### install python3-venv
sudo apt-get install python3-venv

### create venv
python3 -m venv demoenv

### use venv
source ./demoenv/bin/activate

### install packages
pip3 install Flask


### modify directories in config file
<ul>
<li> democonsole/demoapp.service - WorkingDirectory, ExecStart </li>
  <li> democonsole/app/app.ini - home, virtualenv, env</li>
</ul>

### copy nginx config files
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.origin
<br>sudo cp ~/democonsole/nginx.conf /etc/nginx/nginx.conf
<br>sudo cp ~/democonsole/default.conf /etc/nginx/conf.d/demo.conf

### copy uwsgi service config file
sudo cp ~/democonsole/demoapp.service /etc/systemd/system/demoapp.service

### make log directory
sudo mkdir /var/log/uwsgi

### start nginx and democonsole
sudo systemctl start nginx
sudo systemctl start demoapp




