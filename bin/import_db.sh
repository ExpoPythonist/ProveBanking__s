#! /bin/bash
sudo su root -c "cat $1 | docker import - db"
