#! /usr/bin/env bash

if [ "$#" -ne 1 ]
then
  echo "Usage: deploy.sh branch-name"
  exit 1
fi

cd "$(dirname "$0")/../"
git checkout $1
git pull origin $1
source ve/bin/activate
python manage.py collectstatic --noinput & python manage.py migrate_schemas
wait
circusctl restart
