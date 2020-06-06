#!/bin/bash

# Johns Hopkins University Data
cd ~/Documents/dev/COVID-19
git pull
cd ~/Documents/dev/covid
./Rt.py ../COVID-19 .
./grapher.py Rt.csv
cp *.png ~/Desktop
