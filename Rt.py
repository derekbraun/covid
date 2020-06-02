#!/usr/local/opt/python@3.8/bin/python3 -u
# -*- coding: utf-8 -*-
# We generally follow PEP 8: http://legacy.python.org/dev/peps/pep-0008/

'''
Derek C. Braun
Analyzes Johns Hopkins CSSE time series data file for COVID-19 cases.
Calculates estimated Rt
Saves data in a data file format that is handled by fileio.py
Data file: ~/Documents/dev/COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv
'''

STATES = ['Alabama','Alaska','Arizona','Arkansas','California','Colorado',
          'Connecticut','Delaware','District of Columbia','Florida','Georgia',
          'Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas', 'Kentucky',
          'Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota',
          'Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire',
          'New Jersey','New Mexico','New York','North Carolina','North Dakota',
          'Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina',
          'South Dakota','Tennessee','Texas','Utah','Vermont','Virginia',
          'Washington','West Virginia','Wisconsin','Wyoming', 'Guam', 'Puerto Rico']

SERIAL_INTERVAL = 7     # days
SAMPLING_LENGTH = 7     # days

import sys
import os
import time
import csv
import fileio
import argparse
import numpy
from scipy import stats

#
#   MAIN ROUTINE
#
if __name__ == '__main__':
    # reading from the files
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('input_path',
                        help = 'path for data infile.')
    parser.add_argument('output_path',
                        help = 'path for data outfiles.')
    args=parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Make sure the file exists. Open the csv file.
    # Divide the data table into two cleaned up tables: 1. cases and 2. deaths
    print('Reading Johns Hopkins CSSE file...')
    infile = os.path.join(args.input_path,'csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv')
    if not os.path.isfile(infile):
        print('   File {} not found.'.format(infile))
        exit()

    print('   {}'.format(infile))
    f = open(infile,'r')
    rows = csv.reader(f)
    headers = next(rows)
    if headers[6] != 'Province_State' and headers[11] != '1/22/20':
        print('   File format may have changed. Columns may be different or shifted.')
        exit()

    #dates = numpy.array([time.strptime(d,'%m/%d/%y') for d in headers[11:]], dtype=numpy.datetime64)
    #print(headers[11:])
    #dates = [datetime.strptime(d,'%m/%d/%y') for d in headers[11:]]

    dates = numpy.array([numpy.datetime64("20{}-{}-{}".format(y, m.zfill(2), d.zfill(2))) for m, d, y in (s.split("/") for s in headers[11:])])
    #t1 = np.array([np.datetime64("{}-{}-{}".format(c[:4], b, a)) for a, b, c in (s.split("/", 2) for s in t)])

    # Import number of cases
    total_cases = {}
    for state in STATES:
        total_cases[state] = [0 for date in dates]
    for row in rows:
        for i, date in enumerate(dates):
            if row[6] in STATES:
                total_cases[row[6]][i] += int(row[i+11])

    # Add aggregate calculations for United States
    total_cases['United States'] = []
    for i in range(len(dates)):
        total_cases['United States'].append(sum(total_cases[state][i] for state in STATES))

    # Calculate new cases
    new_cases = {}
    for state in STATES + ['United States']:
        new_cases[state] = []
        for i, date in enumerate(dates):
            if i == 0:
                new_cases[state].append(total_cases[state][0])
            else:
                new_cases[state].append(total_cases[state][i]-total_cases[state][i-1])

    # Calculate infectious cases
    infectious_cases = {}
    for state in STATES + ['United States']:
        infectious_cases[state] = []
        for i, date in enumerate(dates):
            if i < 14:
                infectious_cases[state].append(sum(new_cases[state][0:i]))
            else:
                infectious_cases[state].append(sum(new_cases[state][i-14:i]))

    # Calculate Rt
    Rt = {}
    for state in STATES + ['United States']:
        Rt[state] = []
        for i, date in enumerate(dates):
            # calculate average infectious cases over sample
            baseline_infectious_cases = infectious_cases[state][i-SAMPLING_LENGTH]
            if baseline_infectious_cases > 20 and i >= SAMPLING_LENGTH:   #noise filter
                y = numpy.full(SAMPLING_LENGTH, baseline_infectious_cases)
                y += numpy.array(total_cases[state][i-SAMPLING_LENGTH:i])
                y -= total_cases[state][i-SAMPLING_LENGTH]
                log_y = numpy.log(y)
                x = list(range(SAMPLING_LENGTH))
                slope, intercept, r_value, p_value, std_err = stats.linregress(x,log_y)
                Rt[state].append(slope*SERIAL_INTERVAL)
            else:
                Rt[state].append(numpy.nan)

    # Internal integrity check
    numrows = len(dates)
    for state in STATES + ['United States']:
        if numrows != len(total_cases[state]) \
        or numrows != len(new_cases[state]) \
        or numrows != len(infectious_cases[state]) \
        or numrows != len(Rt[state]):
            print("Error! Number of rows aren't even. Check algorithm.")
            exit()

    print()
    print('   Estimated Rt as of {}'.format(numpy.datetime64(dates[-1]).item().strftime('%b %d')))
    print()
    print('   {:>20}   {:^5}   {:^9}   {:^9}   {:^9}'.format('Region', 'Rt', 'Total', 'New', 'Infectious'))
    print('   {:>20}   {:^5}   {:^9}   {:^9}   {:^9}'.format('-'*20, '-'*5, '-'*9, '-'*9, '-'*9))
    for state in STATES + ['United States']:
        print('   {:>20}   {:0.3f}   {:9,}   {:9,}   {:9,}'.format(state, Rt[state][-1], total_cases[state][-1], new_cases[state][-1], infectious_cases[state][-1]))

    print('Writing files...')
    Total_cases_obj = fileio.Table()
    Total_cases_obj.filename = os.path.join(args.output_path, 'total_cases.csv')
    print('   {}'.format(Total_cases_obj.filename))
    Total_cases_obj.headers = ['date'] + STATES + ['United States']
    Total_cases_obj.write_metadata(overwrite=True)
    for i in range(len(dates)):
        row = [dates[i]] + [total_cases[state][i] for state in STATES + ['United States']]
        Total_cases_obj.write([row])

    Rt_obj = fileio.Table()
    Rt_obj.filename = os.path.join(args.output_path, 'Rt.csv')
    print('   {}'.format(Rt_obj.filename))
    Rt_obj.headers = ['date'] + STATES + ['United States']
    Rt_obj.write_metadata(overwrite=True)
    for i in range(len(dates)):
        row = [dates[i]] + [Rt[state][i] for state in STATES + ['United States']]
        Rt_obj.write([row])


    print('Done.\n')
