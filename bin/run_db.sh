#! /bin/bash

PROJECT_ROOT=$(readlink -f .)
POSTGRES_ROOT=$PROJECT_ROOT'/postgres/'
sudo service postgresql stop

sudo docker start db_container
sudo docker attach db_container
