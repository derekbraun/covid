#!/bin/bash

# New York Times Data
#cd ~/Documents/dev/covid-19-data
#git pull
#./Re.py ../covid-19-data/us-states.csv ./Re_NYT.csv
#./grapher.py Re_NYT.csv

# Johns Hopkins University Data
cd ~/Documents/dev/COVID-19
git pull
cd ~/Documents/dev/covid
./Rt.py ../COVID-19 .
./grapher2.py Rt.csv
cp *.png ~/Desktop
