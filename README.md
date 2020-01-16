# democonsole

# Prerequisites
## installation
<br>nginx
<br>uwsgi
<br>docker
<br>docker-compose

## Download robot-shop
git clone https://github.com/instana/robot-shop.git


# Steps
## update
sudo apt-get update

## install pip3, uwsgi
sudo apt-get install python3-dev python3-pip python3-setuptools
<br>sudo -H pip3 install --upgrade pip
<br>sudo -H pip3 install wheel
<br>sudo -H pip3 install uwsgi
<br>sudo -H pip3 install Flask

## install python3-venv
sudo apt-get install python3-venv

## create venv
python3 -m venv demoenv

## use venv
source ./demoenv/bin/activate

## install packages



