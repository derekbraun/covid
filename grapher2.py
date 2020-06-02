#!/usr/local/bin/python3 -u
# -*- coding: utf-8 -*-
# We generally follow PEP 8: http://legacy.python.org/dev/peps/pep-0008/

'''
Derek C. Braun
Produces graphs for the data files created by Re.py for COVID-19 cases.
'''


#   TO DO
#   3. Add annotation arrow to shaded area (most complex)
#      https://matplotlib.org/3.1.1/tutorials/text/annotations.html#annotating-with-arrow

STATES = ['Alabama','Alaska','Arizona','Arkansas','California','Colorado',
          'Connecticut','Delaware','District of Columbia','Florida','Georgia',
          'Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas', 'Kentucky',
          'Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota',
          'Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire',
          'New Jersey','New Mexico','New York','North Carolina','North Dakota',
          'Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina',
          'South Dakota','Tennessee','Texas','Utah','Vermont','Virginia',
          'Washington','West Virginia','Wisconsin', 'Wyoming', 'Guam', 'Puerto Rico']

import os
import sys
import csv
import argparse
import numpy
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt, lines
import fileio

#see: http://matplotlib.sourceforge.net/users/customizing.html
BLUE = '#00457c'
BUFF = '#e8d4a2'

#
#   MAIN ROUTINE
#
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                    formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('filename',
                        help = 'filename for data file')
    parser.add_argument('-o', '--output_file',
                        action='store',
                        default = None,
                        help = 'the output filename ')
    parser.add_argument('-r', '--rcfname',
                        action='store',
                        default = 'print.rc',
                        help = 'the rcf file to use. Must exist in directory')
    parser.add_argument('-t','--title',
                        action='store',
                        default = None,
                        help = 'user-specified title for plot')
    parser.add_argument('--ylabel',
                        action='store',
                        default = None,
                        help = 'user-specified axis label')
    parser.add_argument('--ylim',
                        action='store',
                        type = float,
                        default = None,
                        help = 'manual y limit')
    args=parser.parse_args()
    print('Reading file...')
    if os.path.isfile(args.filename):
        Re = fileio.Table(args.filename)
        print('   {}'.format(args.filename))
    else:
        print('   File {} not found.'.format(args.filename))
        exit()

    print('Writing multiline plot using {}'.format(args.rcfname))
    if args.output_file:
        filename = args.output_file
    else:
        filename = os.path.splitext(args.filename)[0] + \
               '.plot.{args.rcfname}.png'.format(**locals())

    with matplotlib.rc_context(fname=args.rcfname):

        days = matplotlib.dates.DayLocator()
        weeks = matplotlib.dates.WeekdayLocator(byweekday=matplotlib.dates.SU)
        months = matplotlib.dates.MonthLocator()
        date_fmt = matplotlib.dates.DateFormatter('%b')   # https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior

        def rt_plot(ax, X, Ya, Y_highlight, highlight_name):
            #ax.locator_params(axis='x', nbins=4)
            ax.set_ylim(0,5.0)
            ax.set_xlim(numpy.datetime64('2020-03-15'),X[-1])
            ax.set_axisbelow(True)
            ax.set_title(highlight_name, ha='center')
            #ax.grid(which='major', linestyle=':', linewidth=0.6, color='gray', axis='x')
            ax.grid(which='minor', linestyle=':', linewidth=0.6, color='gray', axis='x')
            #shade in between
            ax.fill_between(X, Ya[0], Ya[1], color=BUFF, lw=0)
            ax.plot(X, Y_highlight, color=BLUE, lw=1)
            ax.axhline(1, linestyle=':', lw=0.5)
            # format x axis (dates, by week)


            ax.xaxis.set_major_locator(months)
            ax.xaxis.set_major_formatter(date_fmt)
            ax.xaxis.set_minor_locator(weeks)

        # get the data
        X = numpy.array(Re.select('date'), dtype='datetime64')
        Ya = numpy.array(list(zip(*Re.data[1:])), dtype=float)

        # remove all-nan slices since this generates warnings
        for i, Y in enumerate(Ya):
            if False in numpy.isnan(Y):
                break
        X = X[i:]
        Ya = Ya[i:]
        Ys = list(numpy.nanpercentile(Ya, [0, 100], axis=1))


        plt.clf()
        plt.axis('off')
        ncols = 6
        nrows = int(numpy.ceil(len(STATES + ['United States']) / ncols))
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(15,3*nrows))
        fig.suptitle('Estimated Rate of Spread, $\mathcal{R}_t$, of COVID-19 in the United States', ha='center')

        for j, state in enumerate(STATES + ['United States']):
            Y_highlight = numpy.array(Re.select(state), dtype=float)[i:]
            rt_plot(axes.flat[j], X, Ys, Y_highlight, state)
            if j % ncols == 0:
                axes.flat[j].set_ylabel(r'$\mathcal{R}_t$', rotation=0)
        plt.savefig(filename, transparent=False, dpi=600)
        plt.close()
    print('   {}'.format(filename))
    print("Done.\n")
