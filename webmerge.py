#!/usr/bin/env python
""" CGI script.
- Receives uploaded CSV files
- writes them to disk
- calls merge.py
- write result.html
- redirects to it
"""

import cgi
import cgitb
import tempfile
import os
import subprocess
import datetime
import sys
import time
import glob
import re

PO_LENGTH = 11
PO_COLS = ["Folio", "Civic", "Name 1",
            "Name 2", "Mailing", "Total Assess",
            "Included Assess", "Ann Chg", "Unit",
            "House", "Street"]

BL_LENGTH = 15
BL_COLS = ["RECORD", "LICENSE NUMBER", "ADDRESS",
            "LICENSE TYPE", "STATUS", "LICENSE YEAR",
            "BUSINESS NAME", "BUSINESS TRADE NAME", "DATA FROM",
            "MAIL ADDRESS1", "MAIL ADDRESS2", "MAIL ADDRESS3",
            "MAIL ADDRESS4", "WORK PHONE1", "WORK PHONE2"]

WEB_ROOT = '/var/www/sbia.goodenergy.ca/'
SCRIPT_ROOT = '/usr/local/SBIA/'

OUT = WEB_ROOT + 'out.csv'
ERR = WEB_ROOT + 'err.csv'
FORCE = WEB_ROOT + 'salesforce.csv'

RESULT_TMPL = SCRIPT_ROOT + 'result_template.html'
RESULT = WEB_ROOT + 'result.html'

MERGE = SCRIPT_ROOT + 'merge.py'
DIFF = SCRIPT_ROOT + 'differences.py'

cgitb.enable()


class MergeException(Exception):
    """Raised when external merge script fails"""
    pass


def save_files(form):
    """Writes the uploaded files out to disk"""

    (po_file_desc, po_filename) = tempfile.mkstemp(suffix='.csv')
    po_file = os.fdopen(po_file_desc, "wt")

    po_data = form.getvalue('property_owners')
    po_file.write(po_data)
    po_file.close()

    (bl_file_desc, bl_filename) = tempfile.mkstemp(suffix='.csv')
    bl_file = os.fdopen(bl_file_desc, "wt")

    bl_data = form.getvalue('business_licenses')
    bl_file.write(bl_data)
    bl_file.close()

    return (po_filename, bl_filename)


def merge(po_filename, bl_filename):
    """Shells to the merge script"""

    args = [MERGE, po_filename, bl_filename, OUT, ERR, FORCE, '--quiet']
    retcode = subprocess.call(args)

    if retcode != 0:
        raise MergeException('Return code %d. ' % retcode +
                'Merge script failed. ' +
                'Possibly invalid input files')


def differences(obj_type, current_filename, previous_filename):
    """Shells to the differences script.
    Returns the differences as HTML"""

    args = [DIFF, obj_type, current_filename, previous_filename]
    return subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]


def write_result(po_differences_html, bl_differences_html):
    """Creates the result.html file to display and link the results"""

    tmpl_file = open(RESULT_TMPL, 'rt')
    tmpl = tmpl_file.read()
    tmpl_file.close()

    now = datetime.datetime.utcnow()
    today = datetime.date.today()

    result = tmpl.format(
                    last_updated=now,
                    last_updated_date=today,
                    po_differences_html=po_differences_html,
                    bl_differences_html=bl_differences_html)

    result_file = open(RESULT, 'wt')
    result_file.write(result)
    result_file.close()


def redirect():
    """Return an HTML redirect to result page"""
    print('Status: 302')
    print('Location: result.html\n')


def validate(form):
    """Checks the uploaded form is OK.
    @return None if everything is OK, an error string if not
    """

    bl_name_re = re.compile('BL\-\d{2}\-\d{2}\-\d{2}.csv')
    po_name_re = re.compile('PO\-\d{2}\-\d{2}\-\d{2}.csv')

    err = []

    # First check for basic errors

    if 'property_owners' not in form:
        err.append('Property Owners list missing.')
    else:
        po_filename = form['property_owners'].filename
        if not po_filename.lower().endswith('.csv'):
            err.append('Property Owners must be a CSV file, ' +
                    'with .csv extension. In Excel Save it as CSV')
        if not po_name_re.match(po_filename):
            err.append('Property Owners must have file name in this ' +
                    'format: "PO-mm-dd-yy.csv"')

    if 'business_licenses' not in form:
        err.append('Business Licences list missing.')
    else:
        bl_filename = form['business_licenses'].filename
        if not bl_filename.lower().endswith('.csv'):
            err.append('Business Licenses must be a CSV file, ' +
                    'with .csv extension. In Excel Save it as CSV')
        if not bl_name_re.match(bl_filename):
            err.append('Business Licenses must have file name in this ' +
                    'format: "BL-mm-dd-yy.csv"')

    if err:
        return '<br>'.join(err)

    # No basic errors. Look at data.

    po_data = form.getvalue('property_owners').splitlines()
    po_line1_len = len(po_data[0].split(','))
    if po_line1_len != PO_LENGTH:
        err.append('Property Owners file has wrong number of fields. ' +
                'Got %d, expected %d.' % (po_line1_len, PO_LENGTH))
        err.append('Expected these columns: <b>%s</b>' % \
                    ', '.join(PO_COLS))
        err.append('Got these columns: <b>%s</b>' % po_data[0])

    bl_data = form.getvalue('business_licenses').splitlines()
    bl_line1_len = len(bl_data[0].split(','))
    if bl_line1_len != BL_LENGTH:
        err.append('Business License file has wrong number of fields. ' +
                'Got %d, expected %d.' % (bl_line1_len, BL_LENGTH))
        err.append('Expected these columns: <b>%s</b>' % \
                    ', '.join(BL_COLS))
        err.append('Got these columns: <b>%s</b>' % bl_data[0])

    return '<br>'.join(err)


def output_error(err):
    """Prints error HTML output"""

    reply = ['Content-Type: text/html\n\n']
    reply.append('<html><body>')
    reply.append(err)
    reply.append('</body></html>')

    result = '\n'.join(reply) + '\n\n'
    print(result)


def most_recent(directory, prefix):
    """Finds the most recent file in directory
    that starts with prefix. directory must end with
    a slash.
    @return Filename of most recent file in 'directory' that
    start with 'prefix'."""

    options = []
    for filename in glob.glob(directory + prefix + '*'):
        last_mod = time.localtime(os.stat(filename)[8])
        options.append((last_mod, filename))

    options.sort(reverse=True)
    return options[0][1]


def main():
    """Main"""

    form = cgi.FieldStorage()

    err = validate(form)
    if err:
        output_error(err)
        sys.exit(1)

    po_filename, bl_filename = save_files(form)

    previous_po_filename = most_recent(SCRIPT_ROOT, 'po.csv.20')
    previous_bl_filename = most_recent(SCRIPT_ROOT, 'bl.csv.20')

    po_diff_html = differences('PO', po_filename, previous_po_filename)
    bl_diff_html = differences('BL', bl_filename, previous_bl_filename)

    try:
        merge(po_filename, bl_filename)
    except MergeException, exc:
        output_error(unicode(exc))
        sys.exit(1)

    write_result(po_diff_html, bl_diff_html)

    redirect()


main()

