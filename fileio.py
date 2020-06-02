#!/usr/local/bin/python3 -u
# -*- coding: utf-8 -*-
# We generally follow PEP 8: http://legacy.python.org/dev/peps/pep-0008/

'''
Derek C. Braun
Analyzes NYT data file for COVID-19 cases.

Contains routines to standardize file I/O and to select columns and
metadata from the resulting csv files. Greatly simplifies coding
elsewhere.
'''


METADATA = ['date']

import os
import time
import csv


def create_folder(path):
    '''
        Creates a folder, as needed.

        Accepts
            path        a folder

        Returns
            True        if a folder was created
            False       if a folder was not created
    '''
    if not os.path.isdir(path):
        os.makedirs(path)
        return True
    else:
        return False

class Table:
    '''
        This class is a container for table data.
        It has methods for reading and saving data to csv files, as well
        as for quick statistics and recovering data columns.

        This code is written to be very flexible. The names of the metadata
        headers are stored in the global variable METADATA.
    '''
    def __init__(self, filename=None, **kwargs):
        '''
            If a filename is defined, that file will be opened and the file
            data will populate this class. Metadata in the file will
            become variables in the class scope.

            If a filename is not defined, then metadata should be passed
            to __init__ as kwargs. They will become variables
            in the class scope.
        '''

        if filename is None:
            for key in METADATA:
                if key in list(kwargs.keys()):
                    setattr(self, key, kwargs[key])
                else:
                    setattr(self, key, None)
            self.date = time.strftime('%Y %b %d')
            self.headers = None
        elif filename is not None and len(kwargs) == 0:
            self.filename = filename
            self._read()
        elif filename is not None and len(kwargs) > 0:
            raise BaseException('You cannot pass both a filename and metadata'\
                                 ' to Table.__init__.')


    def write_metadata(self, overwrite=False):
        '''
            Writes metadata and headers to self.filename.

            Accepts:
                overwrite:      True or False

            Returns True if the file is written.
        '''
        if os.path.isfile(self.filename) and not overwrite:
            return False
        else:
            h = []
            for param in METADATA:
                h += [['# {} = {}'.format(param, getattr(self, param))]]
            h += [self.headers]
            f = open(self.filename,'w')
            o = csv.writer(f)
            o.writerows(h)
            f.close()
            return True

    def metadata(self):
        '''
            Returns a string with all the metadata.
        '''
        s = 'Table metadata:\n'
        for param in METADATA:
            if hasattr(self, param):
                s += '   {} = {}\n'.format(param, getattr(self, param))
        return s


    def write(self, rows):
        '''
            Appends a block of data to an existing .tsv file. Should be
            called repeatedly as more data become available.

            Accepts:    rows    a list of rows of columns

            Returns:    True    if successful
                        False   if self.filename file doesn't exist
        '''
        if os.path.isfile(self.filename):
            f = open(self.filename,'a')
            o = csv.writer(f)
            o.writerows(rows)
            f.close()
            return True
        else:
            return False


    def _read(self):
        '''
            Internal method to extract data and metadata from a
            tsv file. Populates the class with data.

            Returns:    True    if successful
                        False   if file not found
        '''
        if os.path.isfile(self.filename):
            f = open(self.filename,'r')
            rows = csv.reader(f)
            self.data = []
            for row in rows:
                if '#' in row[0] and '=' in row[0]:
                    key = row[0].replace('#','').split('=')[0].strip()
                    value = row[0].replace('#','').split('=')[1].strip()
                    if not hasattr(self, key):
                        setattr(self, key, value)
                    continue
                if not hasattr(self, 'headers'):
                    self.headers = row
                else:
                    self.data += [row]
            # This clever Python shorthand transposes a table. It will cause data
            # truncation if the table does not have consistent dimensions.
            self.data = list(zip(*self.data))
            return True
        return False


    def select(self, param, row=None):
        '''
            Selects data columns with name param. Optional row argument allows
            for selection of both a column and a row.

            Accepts
                param           the field to be selected
                row             an optional row index

            Returns a tuple of strings.
        '''
        if param == '*':
            return self.data
        else:
            return self.data[self.headers.index(param)]


    def select_endpoint(self, param):
        '''
            Convenience function to select the endpoint data.

            Accepts
                param         the field to be selected

            Returns a tuple of strings.
        '''
        return self.select(param)[-1]
