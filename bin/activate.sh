#!/usr/bin/env bash

npm_path=$(npm bin)
echo $npm_path
PATH=$PATH:`npm bin`
#source ve/bin/activate.sh
