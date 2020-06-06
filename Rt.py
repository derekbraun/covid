#!/usr/local/bin/python3 -u
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
import csv      # DELETE
import fileio   # DELETE
import argparse
import numpy
import pandas
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
    cases = pandas.read_csv(infile)

    # Integrity check
    if cases.columns[6] != 'Province_State' and cases.columns[11] != '1/22/20':
        print('   File format may have changed. Columns may be different or shifted.')
        exit()

    dates = numpy.array([numpy.datetime64("20{}-{}-{}".format(y, m.zfill(2), d.zfill(2))) for m, d, y in (s.split("/") for s in cases.columns[11:])])
    cases.drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Country_Region', \
             'Lat', 'Long_', 'Combined_Key'], axis=1, inplace=True)
    cases = cases.groupby(['Province_State']).sum().reset_index()
    cases.set_index('Province_State', inplace=True)
    cases.loc['United States'] = cases.sum()

    # Calculate Rt
    Rt = pandas.DataFrame(index = STATES + ['United States'], columns = dates)
    Rt.index.name = 'Province_State'
    for state in STATES + ['United States']:
        new_cases = []
        for i, date in enumerate(dates):
            # 1. find num of infectious cases on first day of sampling period
            #       defined as: number of new cases in the 14 days _preceding_
            #                   the first day of the sampling period
            if i == 0:
                infected = 0
            elif i < 14:
                infected = cases.loc[state][i] - cases.loc[state][0]
            else:
                infected = cases.loc[state][i] - cases.loc[state][i-14]

            # 2. calculate new cases
            if i == 0:
                new_cases += [cases.loc[state][i]]
            else:
                new_cases += [cases.loc[state][i]-cases.loc[state][i-1]]

            # 3. check that there are enough cases and length for a valid Rt calculation
            if cases.loc[state][i] > 20 and i > SAMPLING_LENGTH:
                #y = numpy.full(SAMPLING_LENGTH, infected)
                y = cases.loc[state][i-SAMPLING_LENGTH+1:i+1]
                log_y = numpy.log(y)
                x = list(range(SAMPLING_LENGTH))
                slope, intercept, r_value, p_value, std_err = stats.linregress(x,log_y)
                Rt.loc[state][i] = slope*SERIAL_INTERVAL
            else:
                Rt.loc[state][i] = numpy.nan

    # Internal integrity check
    for state in STATES + ['United States']:
        if len(dates) != len(cases.loc[state]) or len(dates) != len(Rt.loc[state]):
            print("Error! Number of rows aren't even. Check algorithm.")
            exit()

    print()
    print('   Estimated Rt as of {}'.format(numpy.datetime64(dates[-1]).item().strftime('%b %d')))
    print()
    print('   {:>20}   {:^9}   {:^5}'.format('Region', 'Cases', 'Rt'))
    print('   {:>20}   {:^9}   {:^5}'.format('-'*20, '-'*9, '-'*5))
    for state in STATES + ['United States']:
        print('   {:>20}   {:9,}   {:0.3f}'.format(state, cases.loc[state][-1], Rt.loc[state][-1]))

    print('Writing files...')
    for df, filename in zip([cases, Rt], ['cases.csv', 'Rt.csv']):
        outfile = os.path.join(args.output_path, filename)
        df.to_csv(os.path.join(outfile))
        print('   {}'.format(outfile))
    print('Done.\n')
