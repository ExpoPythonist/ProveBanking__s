#!/usr/bin/env bash

mkdir ve
virtualenv --distribute ve
source ve/bin/activate
mkdir med_social/media
pip install -r requirements.txt --allow-unverified PIL --allow-external PIL
