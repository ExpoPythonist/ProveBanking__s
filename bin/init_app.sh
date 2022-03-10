#! /bin/bash

PROJECT_ROOT=$(readlink -f .)
sudo docker rm app_container
sudo docker run -t -i -p 8000:8000 --name="app_container" --link db_container:db -v $PROJECT_ROOT:/home/vetted/src app /prepare_container.sh   #change dir to your project dir
