#!/usr/bin/env python
"""Shows differences between two property owners lists,
or two business licenses lists.
"""

import sys
import syslog
import operator
import csv
import datetime
import os
import stat

from merge import PropertyOwner, BusinessLicense, wrapped

PO_IGNORE_FIELDS = ['original_record', 
                    'total_assess', 
                    'included_assess', 
                    'annual_charge',
                    'house',
                    'street_num',
                    'mailing_street_1',
                    'mailing_street_2',
                    'mailing_street_3']

BL_IGNORE_FIELDS = ['original_record', 
                    'status', 
                    'record', 
                    'license_year', 
                    'license_number']


def diff(current_arr, previous_arr, ignore_fields):
    """Takes two arrays and computes differences.
    """

    # Middle brackets are 'generator comprehension'
    current_map = dict(((obj.key, obj) for obj in current_arr))
    previous_map = dict(((obj.key, obj) for obj in previous_arr))

    added = []
    changed = []

    for key, val in current_map.items():
        if key in previous_map:
            prev = previous_map[key]

            differences = compare_objects(val, prev, ignore_fields)
            if differences:
                changed.append((key, val, differences))

            del previous_map[key]
        else:
            added.append(val)

    removed = previous_map.values()

    added.sort(key=operator.attrgetter('key'))
    changed.sort(key=operator.itemgetter(0))
    removed.sort(key=operator.attrgetter('key'))

    return (added, changed, removed)


def compare_objects(obj1, obj2, ignore_fields):
    """Compares two objects.
    @param ignore_fields Attributes of those objects to not compare
    @return Array of tuple (field, new, old) where field is the name
    of a field which has changed, new is current value, and 
    old is previous value.
    """

    differences = []

    d_obj1 = obj1.__dict__
    d_obj2 = obj2.__dict__

    for field, new in d_obj1.items():

        if field in ignore_fields:
            continue

        old = d_obj2[field]

        new_test = new
        old_test = old
        try:
            new_test = new.lower()
            old_test = old.lower()
        except AttributeError:
            pass

        if old_test != new_test:
            differences.append((field, new, old))
            
    return differences


def output_html_list(title, records, extra=None):
    """Prints pretty HTML of a simple list"""

    print('<h3>%s</h3>' % title)
    if extra:
        print('<p>%s</p>' % extra)
    print('<ul>')
    for record in records:
        print('<li>%s</li>' % record)
    print('</ul>')


def output_html_changes(changed):
    """Prints HTML for changed records"""

    print('<h3>Changes</h3>')
    print('<ul>')
    for key, _, differences in changed:
        print('<li><b>%s</b>' % key)
        print('<table>')
        #print('<tr><th>Field</th><th>Old</th><th>New</th></tr>')
        for field, new, old in differences:
            print('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' %
                    (field, old, new))
        print('</table></li>')

    print('</ul>')


def output_csv_diff(compare_type, added, changed, removed):
    """Prints out differences.csv with the diff."""

    # Filename is: differences[BL|PO].YYYY-MM-DD.csv
    filename = ('differences%s.%s.csv' % (compare_type, datetime.date.today()))
    out = csv.writer(open(filename, 'wb'))

    for obj in added:
        record = ['Added'] + obj.original_record
        out.writerow(record)

    for obj in removed:
        record = ['Removed'] + obj.original_record
        out.writerow(record)

    for _, obj, differences in changed:
        record = ['Changed'] + obj.original_record
        out.writerow(record)
        for field, new, old in differences:
            record = ['', field, old, new]
            out.writerow(record)

    perms = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
    os.chmod(filename, perms)


def output_remove_cache(compare_type, removed):
    """Writes out the removed rows, so that merge.py can load them
    and include them in the salesforce import csv."""

    script_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
    filename = '%s/removed_cache_%s.csv' % (script_dir, compare_type)
    out = csv.writer(open(filename, 'wb'))

    for obj in removed:
        out.writerow(obj.original_record)


def main():
    """Main"""

    if len(sys.argv) != 4:
        print('%d arguments, expected 4' % len(sys.argv))
        print('Usage: differences.py [PO|BL] ' +
                'current.csv previous.csv')
        syslog.syslog('differences.py: Wrong number of arguments to script')
        sys.exit(1)

    compare_type = sys.argv[1]

    if compare_type == 'PO':
        load_func = PropertyOwner.load
        ignore_fields = PO_IGNORE_FIELDS

    elif compare_type == 'BL':
        load_func = BusinessLicense.load
        ignore_fields = BL_IGNORE_FIELDS

    else:
        msg = ('differences.py: Invalid first argument of %s.' % compare_type +
                'Expected PO or BL')
        syslog.syslog(msg)
        print(msg)
        sys.exit(1)

    current = wrapped(load_func, [sys.argv[2]], False)
    previous = wrapped(load_func, [sys.argv[3]], False)

    (added, changed, removed) = diff(current, previous, ignore_fields)

    if added:
        output_html_list('New records', added)
    if removed:
        output_html_list('Old records', 
                    removed,
                    extra='These need to be removed manually from Salesforce')
    if changed:
        output_html_changes(changed)

    output_csv_diff(compare_type, added, changed, removed)
    output_remove_cache(compare_type, removed)

if __name__ == '__main__':
    main()

