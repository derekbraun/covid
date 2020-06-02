#!/usr/local/opt/python@3.8/bin/python3 -u
# -*- coding: utf-8 -*-
# We generally follow PEP 8: http://legacy.python.org/dev/peps/pep-0008/

'''
Derek C. Braun
Analyzes Johns Hopkins CSSE time series data file for COVID-19 cases.
Calculates estimated R (Re)
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
          'Washington','West Virginia','Wisconsin','Wyoming']

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
    parser.add_argument('infile',
                        help = 'filename for data infile.')
    parser.add_argument('outfile',
                        help = 'filename for data infile.')
    args=parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Make sure the file exists. Open the csv file.
    # Divide the data table into two cleaned up tables: 1. cases and 2. deaths
    print('Reading Johns Hopkins CSSE file...')
    if not os.path.isfile(args.infile):
        print('   File {} not found.'.format(args.infile))
        exit()
    else:
        print('   {}'.format(args.infile))
        f = open(args.infile,'r')
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

        cases = {}
        for state in STATES:
            cases[state] = [0 for date in dates]

        for row in rows:
            for i, date in enumerate(dates):
                if row[6] in STATES:
                    cases[row[6]][i] += int(row[i+11])
        print('   Last updated {}'.format(numpy.datetime64(dates[-1]).item().strftime('%b %d')))


    # Add aggregate calculations for United States
    cases['United States'] = []
    for i in range(len(dates)):
        cases['United States'].append(0)
        for state in STATES:
            cases['United States'][i] += cases[state][i]

    # Calculate Re
    Re = {}
    for state in STATES + ['United States']:
        Re[state] = [numpy.nan]*6
        for i in range(len(dates))[6:]:
            if cases[state][i-6] > 35:
                # noise filter, because:
                # cases = 0 causes an error; and
                # a low number of cases causes Re to jump around too much
                # Re is being calculated by log-linear regression
                x = list(range(7))
                y = numpy.log(cases[state][i-6:i+1])
                slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
                Re[state].append(slope*6)
            else:
                Re[state].append(numpy.nan)

    # Internal integrity check
    numrows = len(dates)
    for state in STATES + ['United States']:
        if numrows != len(cases[state]) or numrows != len(Re[state]):
            print("Error! Number of rows aren't even. Check algorithm.")
            exit()

    print()
    print('   Estimated R as of {}'.format(numpy.datetime64(dates[-1]).item().strftime('%b %d')))
    print()
    print('   {:>20}   {:^5}   {:^9}'.format('Region', 'R', 'Cases'))
    print('   {:>20}   {:^5}   {:^9}'.format('-'*20, '-'*5, '-'*9))
    for state in STATES + ['United States']:
        print('   {:>20}   {:0.3f}   {:9,}'.format(state, Re[state][-1], cases[state][-1]))

    Re2 = fileio.Table()
    Re2.filename = args.outfile
    Re2.headers = ['date'] + STATES + ['United States']
    Re2.write_metadata(overwrite=True)
    for i in range(len(dates))[6:]:
        row = [dates[i]] + [Re[state][i] for state in STATES + ['United States']]
        Re2.write([row])
    print('Done.\n')
