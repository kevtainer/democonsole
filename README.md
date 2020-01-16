# democonsole

## Requrements
python3
<br>nginx
<br>uwsgi
<br>docker
<br>docker-compose

## update
sudo apt-get update

## install pip3, uwsgi
sudo apt-get install python3-dev python3-pip python3-setuptools
<br>sudo -H pip3 install --upgrade pip
<br>sudo -H pip3 install wheel
<br>sudo -H pip3 install uwsgi

## install python3-venv
sudo apt-get install python3-venv

## create venv
python3 -m venv demoenv

## use venv
source ./demoenv/bin/activate

## install packages
pip3 install Flask



