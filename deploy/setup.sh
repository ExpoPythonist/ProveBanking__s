#!/bin/bash

CODE_ROOT="/mnt/"
DEPLOYING_USER=${USER}
NGINX_DIR="/etc/nginx/"
POSTGRES_DIR="/etc/postgresql/"
NODE_VERSION=0.10.15

function setup_code_directories {
  echo '========== Setting up code directory =============='
  if [ ! -d "$CODE_ROOT" ]; then
    sudo -u DEPLOYING_USER mkdir $CODE_ROOT
  else
    echo 'code directory already exists'
  fi 
}

function install_nginx {
  echo '=========== Installing nginx ================='
  if [ ! -d "$NGINX_DIR" ]; then
    sudo apt-get install nginx
    echo '---------- successfully installed nging ----------'
  else
    echo 'nginx already installed, skipping'
  fi
}

function get_postgres_repo_key {
  echo '============ Updating postgres repo info=================='
  echo ' Adding the SSH key'
  wget -O - http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc | sudo apt-key add -
  echo ' Successfully added postgresql repo key '
  if [ ! -f "/etc/apt/sources.list.d/pgdg.list" ]; then
    sudo touch /etc/apt/sources.list.d/pgdg.list
    echo "deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main" | sudo tee -a /etc/apt/sources.list.d/pgdg.list
   fi
}


function install_all {
  sudo apt-get install python-software-properties
  if [ ! -d "$POSTGRES_DIR" ]; then
    sudo add-apt-repository ppa:pitti/postgresql
    sudo apt-get install postgresql-9.2 postgresql-server-dev-9.2 pgbouncer
  else
    echo ' postgres already installed, skipping'
  fi
  sudo apt-get update
  sudo apt-get install build-essential python2.7 python-pip python-virtualenv python-dev libjpeg62 libjpeg-dev zlib1g-dev imagemagick libevent-dev redis-server libfreetype6-dev libxml2 libxslt1-dev libxml2-dev libxslt-dev python-nltk python-numpy
  
  sudo apt-get install curl
  sudo apt-get install git-core

  sudo pip install pip -U
  sudo pip install virtualenv -U
  sudo pip install virtualenvwrapper -U
}

function symlink_pil {
  echo "symlink the pil library"
  if [ ! -f "/usr/lib/x86_64-linux-gnu/libjpeg.so" ]; then
    sudo ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib/
  fi

  if [ ! -f "/usr/lib/x86_64-linux-gnu/libz.so" ]; then
    sudo ln -s /usr/lib/x86_64-linux-gnu/libz.so /usr/lib/
  fi

  if [ ! -f "/usr/lib/x86_64-linux-gnu/libfreetype.so" ]; then
    sudo ln -s /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib/
  fi
}

function install_nodejs {
  echo "installing nodejs"
  curl https://raw.github.com/creationix/nvm/master/install.sh | sh
  source ~/.nvm/nvm.sh
  nvm install $NODE_VERSION
}

function change_ownership {
  echo '======== change code directory ownership to www-data ========='
  sudo chown -cR www-data:www-data $CODE_ROOT

  echo '======== change default home directory for www-data user ========'
  sudo usermod -m -d /mnt www-data

  echo '======== change default shell for www-data user ========'
  sudo chsh -s /bin/bash www-data
}

function create_project_dir {
  sudo su - www-data
  cd
  mkdir thevetted && cd thevetted
  mkdir NewsWithFriends
  git clone git@github.com:jlamba/NewsWithFriends.git NewsWithFriends
}

# MAIN FUNCTION
setup_code_directories
install_nginx
get_postgres_repo_key
install_all
symlink_pil
install_nodejs

change_ownership
create_project_dir
