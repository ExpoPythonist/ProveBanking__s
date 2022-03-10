#! /bin/bash

PROJECT_ROOT=$(readlink -f .)
sudo docker start app_container
sudo docker attach app_container
