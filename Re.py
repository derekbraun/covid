#!/usr/local/bin/python3 -u
# -*- coding: utf-8 -*-
# We generally follow PEP 8: http://legacy.python.org/dev/peps/pep-0008/

'''
Derek C. Braun
Analyzes NYT data file for COVID-19 cases.
Calculates Re
Saves data in a more standardized data file format that is handled by fileio.py
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
    print('Reading NYT formatted file...')
    if not os.path.isfile(args.infile):
        print('   File {} not found.'.format(filename))
        exit()
    else:
        print('   {}'.format(args.infile))
        f = open(args.infile,'r')
        rows = csv.reader(f)
        next(rows)
        dates, cases, deaths = [], {}, {}
        for state in STATES:
            cases[state], deaths[state] = [],[]
        last_date = None
        unreported_states = list(STATES)
        for row in rows:
            if row[0] != last_date:
                if last_date is not None:
                    for st in unreported_states:
                        cases[st].append(0)
                        deaths[st].append(0)
                unreported_states = list(STATES)
                last_date = row[0]
                dates.append(last_date)
            if row[1] in STATES:
                cases[row[1]].append(int(row[3]))
                deaths[row[1]].append(int(row[4]))
                unreported_states.remove(row[1])
        for st in unreported_states:
            cases[st].append(0)
            deaths[st].append(0)
        print('   Last updated {}'.format(numpy.datetime64(last_date).item().strftime('%b %d')))

    # Add aggregate calculations for United States
    cases['United States'], deaths['United States'] = [], []
    for i in range(len(dates)):
        cases['United States'].append(0)
        deaths['United States'].append(0)
        for state in STATES:
            cases['United States'][i] += cases[state][i]
            deaths['United States'][i] += deaths[state][i]

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
        if numrows != len(cases[state]) or numrows != len(deaths[state]) or numrows != len(Re[state]):
            print("Error! Number of rows aren't even. Check algorithm.")
            exit()

    print()
    print('   Estimated R as of {}'.format(numpy.datetime64(dates[-1]).item().strftime('%b %d')))
    print()
    print('   {:>20}   {:^5}   {:^9}'.format('Region', 'R', 'Cases'))
    print('   {:>20}   {:^5}   {:^9}'.format('-'*20, '-'*5, '-'*9))
    for state in ['United States']:
        print('   {:>20}   {:0.3f}   {:9,}'.format(state, Re[state][-1], cases[state][-1]))

    Re2 = fileio.Table()
    Re2.filename = args.outfile
    Re2.headers = ['date'] + STATES + ['United States']
    Re2.write_metadata(overwrite=True)
    for i in range(len(dates))[6:]:
        row = [dates[i]] + [Re[state][i] for state in STATES + ['United States']]
        Re2.write([row])
    print('Done.\n')
