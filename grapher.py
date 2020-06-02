#!/usr/local/bin/python3 -u
# -*- coding: utf-8 -*-
# We generally follow PEP 8: http://legacy.python.org/dev/peps/pep-0008/

'''
Derek C. Braun, Brienna K. Herold
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
          'Washington','West Virginia','Wisconsin','Wyoming', 'Guam', 'Puerto Rico']


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

        yformat = '{x:.2}'

        # get the data
        X = numpy.array(Re.select('date'), dtype='datetime64')
        Ya = numpy.array(list(zip(*Re.data[1:])), dtype=float)
        Y_USA = numpy.array(Re.select('United States'), dtype=float)

        # remove all-nan slices since this generates warnings
        for i, Y in enumerate(Ya):
            if False in numpy.isnan(Y):
                break
        X = X[i:]
        Ya = Ya[i:]
        Y_USA = Y_USA[i:]

        Ys = list(numpy.nanpercentile(Ya, [100-2*i for i in range(50)], axis=1))

        plt.clf()
        fig = plt.figure()

        plt.axis('off')
        grid = plt.GridSpec(1,10, wspace=0)
        ax1 = fig.add_subplot(grid[0,:9])
        ax2 = fig.add_subplot(grid[0,9], sharey=ax1)
        ax1.locator_params(axis='x', nbins=4)
        ax1.set_ylim(0,3.5)
        ax1.set_xlim(numpy.datetime64('2020-03-15'),X[-1])
        ax1.set_ylabel(r'$\mathcal{R}$', rotation=0)
        ax1.set_axisbelow(True)
        ax1.set_title('Estimated Rate of Spread, $\mathcal{R}$, of COVID-19 in the United States', ha='center')
        ax1.grid(which='major', linestyle=':', linewidth=0.6, color='gray', axis='x')
        ax1.grid(which='minor', linestyle=':', linewidth=0.2, color='gray', axis='x')

        #shade in between
        min_alpha = 0.3
        alpha_increm = (1.-min_alpha)/25.
        for i in range(49):
            ax1.fill_between(X, Ys[i], Ys[i+1], color=BUFF, lw=0, alpha=(min_alpha+i*alpha_increm if i<=25 else 1.+(25-i)*alpha_increm))

        #ax1.fill_between(X, Y_100, Y_98, color=BUFF, lw=0, alpha=0.6)
        #ax1.fill_between(X, Y_98, Y_75, color=BUFF, lw=0, alpha=0.8)
        #ax1.fill_between(X, Y_75, Y_25, color=BUFF, lw=0, alpha=1)
        #ax1.fill_between(X, Y_25, Y_2, color=BUFF, lw=0, alpha=0.8)
        #ax1.fill_between(X, Y_2, Y_0, color=BUFF, lw=0, alpha=0.6)
        #ax1.plot(X, Y_100, color=BLUE, lw=0.2)
        ax1.plot(X, Y_USA, color=BLUE, lw=1)
        #ax1.plot(X, Y_0, color=BLUE, lw=0.2)

        # do the ax2 violin plot
        #ax2.violinplot(Ya[-1], showmeans = False, showmedians = True,
        #              showextrema = False)
        #ax2.vlines([1], Y_25[-1], Y_75[-1], linestyle='-', lw=4)
        #ax2.vlines([1], Y_2[-1], Y_98[-1], linestyle='-', lw=1)
        #ax2.text(1.2, Y_2[-1], yformat.format(x=Y_2[-1]),
        #                va='center', ha='left')
        #ax2.text(1.3, Y_50[-1], yformat.format(x=Y_50[-1]),
        #        va='center', ha='left')
        #ax2.text(1.2, Y_98[-1], yformat.format(x=Y_98[-1]),
        #        va='center', ha='left')
        ax2.axis('off')

        ax1.axhline(1, linestyle=':', lw=0.5)
        ax2.axhline(1, linestyle=':', lw=0.5)
        ax2.text(0.05, 0.95, 'When $\mathcal{R}$ > 1, the\nepidemic is growing.\n',
                 va='bottom', ha='left', fontsize = '6')
        ax2.text(0.05, 0.95, 'When $\mathcal{R}$ < 1, the\nepidemic is shrinking.\n',
                 va='top', ha='left', fontsize = '6')

        ax2.text(0.05, 0.40, 'The shaded area shows the\n'\
                             'range for the 50 states.',
                 va='bottom', ha='left', fontsize = '6')
#                     xy=(0.05,0.95), xycoords='data', xytext=(0.1, 1.0), textcoords='data',
#                     arrowprops=dict(facecolor='black', shrink=0.05),
#             va='bottom', ha='left')
        ax2.text(0.05, Y_USA[-1], 'The blue line shows\n' \
                                  '$\mathcal{R}$ for the United States.',
                         va='center', ha='left', fontsize = '6')

        ax1.text (0.05,-0.1,'$\mathcal{R}$ was estimated by log-linear regression of the previous 7 days of case data with a\n'
                           'serial interval of 7 days. Data source: Johns Hopkins CSSE. Analysis: Derek Braun, Ph.D.',
                  fontsize = '6', va='top', transform=ax1.transAxes)

        # format x axis (dates, by week)
        days = matplotlib.dates.DayLocator()
        weeks = matplotlib.dates.WeekdayLocator(byweekday=matplotlib.dates.SU)
        date_fmt = matplotlib.dates.DateFormatter('%b %d')   # https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
        ax1.xaxis.set_major_locator(weeks)
        ax1.xaxis.set_major_formatter(date_fmt)
        ax1.xaxis.set_minor_locator(days)

        plt.savefig(filename, transparent=False, dpi=600)
        plt.close()
    print('   {}'.format(filename))
    print("Done.\n")
