#! /bin/bash

PROJECT_ROOT=$(readlink -f .)
POSTGRES_ROOT=$PROJECT_ROOT'/postgres/'
sudo service postgresql stop
sudo docker rm db_container
sudo docker run -t -i -p 5432:5432 --name="db_container" -v $POSTGRES_ROOT:/data db /prepare_container.sh
