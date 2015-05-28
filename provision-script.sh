#!/usr/bin/env bash

apt-get update
apt-get install -y python python-setuptools git screen python-pip
cd /vagrant
python setup.py develop
screen -d -m /usr/local/bin/pluserman

echo pluserman is now running
