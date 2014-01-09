#!/usr/bin/env python
"""Merges Business License and Property Owners CSV files.
"""

# pylint: disable-msg=R0902,R0903,R0201

import os
import csv
import sys
import shutil
import datetime
import operator
import syslog
import stat

# Address that count as Strathcona. Examples: 
#  Railway St includes the 300, 400 and 500 blocks.
#  Georgia St includes only the 12000 block.
VALID_ADDR = {

    # West-East
    'railway': [3, 4, 5],
    'alexander': [3, 4, 5, 6, 7],
    'powell': [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
    'cordova': [3, 4, 5, 6, 7, 8, 9, 10],
    'hastings': [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
    'franklin': [11, 12],
    'pender': [10, 11, 12],
    'frances': [12, 13],
    'keefer': [10],
    'georgia': [10, 11, 12],
    'adanac': [12],
    'union': [10, 11],
    'venables': [10, 11, 12, 13],

    # North-South
    'gore': [0, 1, 2, 3, 4],
    'dunlevy': [0, 1, 2, 3, 4],
    'jackson': [0, 1, 2, 3, 4],
    'princess': [1, 2, 3, 4],
    'heatley': [1, 2, 3, 4],
    'hawks': [1, 2, 3, 4],
    'campbell': [3, 4],
    'raymur': [2, 3, 4, 5, 6, 7, 8],
    'glen': [2, 3, 4, 5, 6, 7, 8],
    'vernon': [2, 3, 4, 5, 6, 7, 8],
    'clark': [2, 3, 4, 5, 6, 7, 8]
}

# Countries that Mailing Address has been seen in 
COUNTRIES = ['usa', 'hong kong']

# Business License Types to ignore
INVALID_LICENSE_TYPE = ['one family dwelling']

# Business names to ignore
INVALID_BUSINESS_NAME = ['provincial rental housing corporation']

# Business address to property owners address
ADDRESS_OWNERS = {

        '1227 adanac': '1219 adanac',
        '1228 adanac': '1255 venables',
        '1311 adanac': '790 clark',

        '302 alexander': '300 alexander',
        '310 alexander': '320 alexander',
        '362 alexander': '360 alexander',
        '397 alexander': '395 alexander',
        '472 alexander': '450 alexander',
        '720 alexander': '716 alexander',

        '526 clark': '1305 frances',
        '530 clark': '1305 frances',
        '550 clark': '1305 frances',
        '560 clark': '1305 frances',
        '570 clark': '1305 frances',
        '590 clark': '1305 frances',
        '777 clark': '775 clark',
        '823 clark': '1255 venables',

        '385 cordova': '255 dunlevy',
        '742 cordova': '731 cordova',
        '876 cordova': '889 cordova',
        '1007 cordova': '252 raymur',
        '1009 cordova': '252 raymur',
        '1019 cordova': '252 raymur',
        '1021 cordova': '252 raymur',
        '1055 cordova': '252 raymur',

        '37 dunlevy': '45 dunlevy',
        '49 dunlevy': '45 dunlevy',
        '55 dunlevy': '395 alexander',
        '402 dunlevy': '406 hastings',
        '406 dunlevy': '406 hastings',
        '408 dunlevy': '406 hastings',
        '418 dunlevy': '406 hastings',

        '1221 frances': '1223 frances',
        '1231 frances': '1223 frances',
        '1258 frances': '1254 frances',

        '1104 franklin': '1102 franklin',
        '1146 franklin': '1180 franklin',
        '1198 franklin': '1180 franklin',

        '1138 georgia': '1134 georgia',

        '326 hastings': '330 hastings',
        '328 hastings': '330 hastings',
        '336 hastings': '334 hastings',
        '339 hastings': '337 hastings',
        '380 hastings': '427 dunlevy',
        '384 hastings': '427 dunlevy',
        '388 hastings': '427 dunlevy',
        #'392 hastings': '427 dunlevy',
        #'398 hastings': '427 dunlevy',
        '398 hastings': '392 hastings',
        '408 hastings': '406 hastings',
        '410 hastings': '406 hastings',
        '412 hastings': '406 hastings',
        '420 hastings': '422 hastings',
        '431 hastings': '437 hastings',
        '432 hastings': '430 hastings',
        '439 hastings': '437 hastings',
        '441 hastings': '440 hastings',
        '461 hastings': '459 hastings',
        '463 hastings': '459 hastings',
        '502 hastings': '408 jackson',
        '504 hastings': '408 jackson',
        '505 hastings': '501 hastings',
        '509 hastings': '501 hastings',
        '531 hastings': '527 hastings',
        '604 hastings': '600 hastings',
        '606 hastings': '600 hastings',
        '643 hastings': '641 hastings',
        '649 hastings': '647 hastings',
        '651 hastings': '647 hastings',
        '708 hastings': '702 hastings',
        '745 hastings': '717 hastings',
        '786 hastings': '782 hastings',
        '823 hastings': '821 hastings',
        '825 hastings': '821 hastings',
        '852 hastings': '848 hastings',
        '862 hastings': '848 hastings',
        '869 hastings': '877 hastings',
        '873 hastings': '877 hastings',
        '879 hastings': '877 hastings',
        '881 hastings': '877 hastings',
        '884 hastings': '882 hastings',
        '961 hastings': '955 hastings',
        '965 hastings': '955 hastings',
        '1121 hastings': '1127 hastings',
        '1125 hastings': '1127 hastings',
        '1129 hastings': '1127 hastings',
        '1133 hastings': '1131 hastings',
        '1278 hastings': '1268 hastings',
        '1283 hastings': '1279 hastings',
        '1291 hastings': '1279 hastings',
        '1299 hastings': '1279 hastings',
        '1190 hastings': '403 vernon',
        '1192 hastings': '403 vernon',

        '250 hawks': '837 cordova',

        '405 heatley': '401 heatley',
        '407 heatley': '401 heatley',
        '409 heatley': '401 heatley',
        '417 heatley': '401 heatley',
        '419 heatley': '401 heatley',

        '28 jackson': '20 jackson',
        '370 jackson': '501 hastings',

        '1218 pender': '1222 pender',
        '1220 pender': '1222 pender',
        '1202 pender': '1222 pender',
        '1206 pender': '1222 pender',
        '1212 pender': '1222 pender',
        '1310 pender': '1305 frances',
        '1320 pender': '1305 frances',

        '318 powell': '316 powell',
        '346 powell': '342 powell',
        '348 powell': '342 powell',
        '350 powell': '342 powell',
        '394 powell': '347 powell',
        '356 powell': '358 powell',
        '362 powell': '358 powell',
        '368 powell': '370 powell',
        '376 powell': '374 powell',
        '415 powell': '411 powell',
        '429 powell': '427 powell',
        '435 powell': '427 powell',
        '439 powell': '437 powell',
        '469 powell': '467 powell',
        '475 powell': '473 powell',
        #'453 powell': '451 powell',
        '543 powell': '537 powell',
        '578 powell': '215 princess',
        '580 powell': '215 princess',
        '582 powell': '215 princess',
        '683 powell': '687 powell',
        '686 powell': '209 heatley',
        '758 powell': '756 powell',
        '784 powell': '1302 powell',
        '811 powell': '807 powell',
        '827 powell': '825 powell',
        '836 powell': '838 powell',
        '1132 powell': '1130 powell',
        '1142 powell': '1130 powell',
        '1160 powell': '1159 franklin',

        '120 princess': '1302 powell',
        '420 princess': '600 hastings',

        '329 railway': '325 railway',
        '380 railway': '45 dunlevy',
        '397 railway': '395 railway',
        '435 railway': '439 railway',
        '495 railway': '485 railway',
        '505 railway': '503 railway',

        '258 raymur': '252 raymur',
        '260 raymur': '252 raymur',
        '266 raymur': '252 raymur',

        '1103 union': '1101 union',
        '1113 union': '1111 union',
        '1121 union': '1111 union',

        '1100 venables': '1101 venables',
        '1275 venables': '1255 venables',
        '1233 venables': '1255 venables',
        '1299 venables': '1255 venables',

        '510 vernon': '1222 pender',
        '520 vernon': '1222 pender',
        '530 vernon': '1222 pender',
        '704 vernon': '700 vernon'
        }

REGISTRY = {}


class ErrorManager(object):
    """Records invalids rows"""

    def __init__(self):
        self.errors = []

    def add(self, obj, msg):
        """Record that 'obj' was rejected for reason 'msg'"""
        self.errors.append((obj, msg))

    def report(self, filename):
        """Write a report of all errors to filename"""

        writer = csv.writer(open(filename, 'wt'))

        for obj, msg in self.errors:
            writer.writerow([msg] + obj.original_record)


class InvalidAddress(Exception):
    """Raised when AddressManager can't parse given address"""
    pass


class InvalidInput(Exception):
    """Raised when one of the input files doesn't look right."""
    pass


class AddressManager(object):
    """Checks addresses"""

    def __init__(self):
        self.valid_addresses = VALID_ADDR

    def get_block(self, street_num):
        """Takes a street address such as 1209 or 305 and returns
        the block number, i.e. 12 or 3 in these examples"""
        return street_num / 100

    def clean(self, address, is_strong=False):
        """Returns given address changed to:
        - lowercase
        - 'E' or 'W' removed
        - ', vancouver' removed
        """

        address = address.strip().lower()
        address = address\
                    .replace(', vancouver', '')\
                    .replace(' e ', ' ')\
                    .replace(' w ', ' ')
        if address.endswith(' e') or address.endswith(' w'):
            address = address[:-2]

        if is_strong:

            address = address + ' '
            address = address\
                        .replace(' st ', '')\
                        .replace(' av ', '')\
                        .replace(' ave ', '')\
                        .replace(' drive', '')\
                        .replace(' dr', '')\
                        .replace(' diversion', '')\
                        .strip()

            # Remove unit number
            parts = address.split()
            try:
                # Is the second part street number, 
                #  implying first was unit number?
                int(parts[1])
                address = address[address.index(' ') + 1 : ]
            except ValueError:
                pass

        return address.strip()

    def extract_unit_num_street(self, address):
        """Takes a street address and returns tuple of (unit, num, street).
        For example '101 305 pender st' comes back as (101, 305, 'pender st').
        Missing fields are returned as None, and Unit is usually None.

        @raises InvalidAddress
        """

        unit = street_num = street = None

        address_parts = self.clean(address).split()

        try:
            street_num = int(address_parts[1])
            street = address_parts[2]
            unit = int(address_parts[0])

        except IndexError:
            raise InvalidAddress(address)

        except ValueError:

            try:
                street_num = int(address_parts[0])
            except ValueError:
                # Not even a number
                raise InvalidAddress(address)

            street = address_parts[1]

        return (unit, street_num, street)

    def is_in_location(self, address):
        """Is the given address in one of the blocks and 
        streets defined in VALID_ADDR"""

        try:
            _, street_num, street = self.extract_unit_num_street(address)
        except InvalidAddress:
            return False

        block = self.get_block(street_num)

        try:
            valid_blocks = self.valid_addresses[street]
        except KeyError:
            return False

        return block in valid_blocks

    def previous_neighbour(self, address):
        """Return the address two before this one.
        So for '318 powell st' it returns '316 powell st'.
        We expect address has already been through 'clean'.
        """

        _, street_num, _ = self.extract_unit_num_street(address)
        street_num -= 2

        return str(street_num) + ' ' + ' '.join(address.split()[1:])


class PropertyOwner(object):
    """Owner of a property, identified by address"""

    @staticmethod
    def load(filename):
        """Reads property owners from a CSV file and returns
        an array of PropertyOwner"""

        owners = []

        address_manager = REGISTRY['address_manager']
        error_manager = REGISTRY['error_manager']

        reader = csv.reader(open(filename, 'rU'))
        try:
            headers = reader.next()   # Text column headers
        except StopIteration:
            syslog.syslog('merge.py: Empty file %s' % filename)
            return owners

        if len(headers) != 11:
            raise InvalidInput('Property Owners file should have ' +
                'exactly 11 columns. Found %d.' % len(headers))

        for line in reader:
            property_owner = PropertyOwner(line)
            if address_manager.is_in_strathcona(property_owner.civic):
                owners.append(property_owner)
            else:
                error_manager.add(property_owner, 
                                  'Not in Strathcona or invalid address')

        owners.sort(key=operator.attrgetter('folio'))

        return owners

    def __init__(self, arr):

        self.original_record = arr

        self.folio = arr[0].strip()
        self.civic = arr[1].strip()
        self.name1 = arr[2].strip()
        self.name2 = arr[3].strip()
        self.mailing = arr[4].strip()
        self.total_assess = arr[5].strip()
        self.included_assess = arr[6].strip()
        self.annual_charge = arr[7].strip()
        self.unit = arr[8].strip()
        self.house = arr[9].strip()
        self.street = arr[10].strip()

        # Business licences at this address
        self.licenses = []

        address_manager = REGISTRY['address_manager']

        try:
            self.unit, self.street_num, self.street = \
                    address_manager.extract_unit_num_street(self.civic)
        except InvalidAddress:
            self.unit = self.street_num = self.street = ''

        # Split mailing address

        mailing_parts = self.mailing.split('\n')
        self.mailing_street_1 = None
        self.mailing_street_2 = None
        self.mailing_street_3 = None

        try:
            self.mailing_street_1 = mailing_parts[0]
            self.mailing_street_2 = mailing_parts[1]
        except IndexError:
            pass

        self.mailing_country = 'CANADA'

        if mailing_parts[-1].lower() in COUNTRIES:
            self.mailing_country = mailing_parts[-1]
            del mailing_parts[-1]

        if len(mailing_parts) > 2:
            self.mailing_street_3 = ', '.join(mailing_parts[2:])

    def __repr__(self):
        return unicode(self)

    def __str__(self):
        return unicode(self)

    def __unicode__(self):
        return "%s - %s" % (self.folio, self.civic)

    @property
    def key(self):
        """Unique key for this item"""
        return self.account_name()

    def civic_no_city(self):
        """The street address without city part"""
        return self.civic.replace(', VANCOUVER', '')

    def property_address(self):
        """Full address of this property"""
        return self.civic + ', B.C., CANADA'

    def account_name(self):
        """Name to use on the Salesforce account"""
        return self.civic_no_city()

    def output_to(self, writer):
        """ Writes this object out to a CSV file
        @param writer a csv.Writer object
        """
        record = [
            self.civic_no_city(),   # Property address
            'PROPERTY OWNER',   # License type
            self.street_num,    # House
            self.street,        # Street
            self.folio,         # License / Folio
            self.civic,         # Civic address
            self.name1,         # Business name 1
            self.name2,         # Business name 2
            self.mailing,       # Mailing address 1
            '',                 # Mailing address 2
            self.total_assess,
            self.included_assess,
            self.annual_charge,
            ''                  # Unit
        ]

        writer.writerow(record)

        for b_l in self.licenses:
            b_l.output_to(writer)

    def output_salesforce_to(self, writer, remove_date=''):
        """Writes this object to a CSV writer object,
        in a format we can import into Salesforce.
        @param writer a csv.Writer object
        """

        record = [
            'System Admin',         # Record Owner
            self.account_name(),    # Account Name
            '',                     # Parent Account
            '',                     # Phone
            'Property Owner',       # Business License Type
            '',                     # License Number
            self.folio,             # Folio Number
            self.total_assess,      # Total Assessment
            self.included_assess,   # Included Assessment
            self.annual_charge,     # Annual Charge
            self.name1,             # Business Name
            self.name2,             # Business Name 2
            self.street,            # Street Name
            self.unit,              # Unit
            self.civic_no_city(),   # Billing Street
            'Vancouver',            # Billing City
            'B.C.',                 # Billing State
            '',                     # Billing Postal Code
            'Canada',               # Billing Country
            self.mailing_street_1,  # Shipping Street 1
            self.mailing_street_2,  # Shipping Street 2
            self.mailing_street_3,  # Shipping Street 3
            self.mailing_country,   # Shipping Country
            remove_date             # Removed
        ]

        writer.writerow(record)

        if not remove_date:     # We don't include children of removed items
            for b_l in self.licenses:
                b_l.output_salesforce_to(writer)


class BusinessLicense(object):
    """Operator of a business, identified by business license number,
    and by address."""

    @classmethod
    def load(cls, filename):
        """Reads CSV file of business licenses, returns an 
        array of BusinessLicense. """

        licenses = []

        address_manager = REGISTRY['address_manager']
        error_manager = REGISTRY['error_manager']

        license_numbers = []

        reader = csv.reader(open(filename, 'rU'))
        try:
            headers = reader.next()   # Text column headers
        except StopIteration:
            syslog.syslog('merge.py: Empty file %s' % filename)
            return licenses
 
        if len(headers) != 15:
            raise InvalidInput('Business License file should have ' +
                'exactly 15 columns. Found %d.' % len(headers))

        for line in reader:
            business_license = BusinessLicense(line)

            if business_license.license_number in license_numbers:
                # Silently skip duplicates
                #error_manager.add(business_license,
                #                'Duplicate license number')
                continue

            license_numbers.append(business_license.license_number)

            if not business_license.is_valid_license_type():
                error_manager.add(business_license,
                                  'Invalid license type')
                continue
            if not business_license.is_valid_business_name():
                error_manager.add(business_license,
                                    'Business name is on ignore list')
                continue

            if address_manager.is_in_strathcona(business_license.address):
                licenses.append(business_license)
            else:
                error_manager.add(business_license,
                                  'Not in Strathcona or invalid address')

        licenses.sort(key=operator.attrgetter('license_number'))

        return licenses

    def __init__(self, arr):

        self.original_record = arr

        self.record = arr[0].strip()
        self.license_number = arr[1].strip()
        self.address = arr[2].strip()
        self.license_type = arr[3].strip()
        self.status = arr[4].strip()
        self.license_year = arr[5].strip()
        self.business_name = arr[6].strip()
        self.business_trade_name = arr[7].strip()
        self.data_from = arr[8].strip()
        self.mail_address_1 = arr[9].strip()
        self.mail_address_2 = arr[10].strip()
        self.mail_address_3 = arr[11].strip()
        self.mail_address_4 = arr[12].strip()
        self.work_phone_1 = arr[13].strip()
        self.work_phone_2 = arr[14].strip()

        self.owner = None

        address_manager = REGISTRY['address_manager']

        try:
            self.unit, self.street_num, self.street = \
                    address_manager.extract_unit_num_street(self.address)
        except InvalidAddress:
            self.unit = self.street_num = self.street = ''

    def __repr__(self):
        return unicode(self)

    def __str__(self):
        return unicode(self)

    def __unicode__(self):
        return "%s - %s" % (self.license_number, self.address)

    @property
    def key(self):
        """Unique key for this item"""
        return self.account_name()

    def is_valid_license_type(self):
        """Is this license type one we want to include"""
        clean = self.license_type.lower().replace('-', ' ')
        return clean not in INVALID_LICENSE_TYPE

    def is_valid_business_name(self):
        """Should we skip this business?"""
        return self.business_name.lower() not in INVALID_BUSINESS_NAME

    def other_mail_address(self):
        """Mailing address fields 2, 3 and 4 concatenated"""
        return (self.mail_address_2 + ' ' + 
                self.mail_address_3 + ' ' +
                self.mail_address_4)

    def account_name(self):
        """Name to use on the Salesforce account"""

        name1 = self.business_trade_name
        name2 = self.business_name

        if not name1 and not name2:
            return 'NAME MISSING - ' + self.license_number
        elif name1 and not name2:
            return name1
        elif name2 and not name1:
            return name2
        else:
            return name1 + ' (' + name2 + ')'

    def output_to(self, writer):
        """ Writes this object out to a CSV file
        @param writer a csv.Writer object
        """

        record = [
            self.address,               # Property address
            self.license_type,          # License type
            self.street_num,            # House
            self.street,                # Street
            self.license_number,        # License / Folio
            self.address,               # Civic address
            self.business_trade_name,   # Business name 2
            self.business_name,         # Business name 1
            self.mail_address_1,        # Mailing address 1
            self.other_mail_address(),  # Mailing address 2
            '',                         # Total Assess
            '',                         # Included Assess
            '',                         # Annual Charge
            self.unit                   # Unit
        ]

        writer.writerow(record)

    def output_salesforce_to(self, writer, remove_date=''):
        """Writes this object to a CSV writer object,
        in a format we can import into Salesforce.
        @param writer a csv.Writer object
        """

        if self.owner:
            parent_account = self.owner.civic_no_city()
        else:
            parent_account = ''

        record = [
            'System Admin',              # Record Owner
            self.account_name(),         # Account Name
            parent_account,              # Parent Account
            self.work_phone_1,           # Phone
            self.license_type,           # Business License Type
            self.license_number,         # License Number
            '',                          # Folio Number
            '',                          # Total Assessment
            '',                          # Included Assessment
            '',                          # Annual Charge
            self.business_trade_name,    # Business Name
            self.business_name,          # Business Name 2
            self.street,            # Street Name
            self.unit,              # Unit
            self.address,           # Billing Street
            'Vancouver',            # Billing City
            'B.C.',                 # Billing State
            '',                     # Billing Postal Code
            'Canada',               # Billing Country
            self.mail_address_1,    # Shipping Street 1
            self.mail_address_2,    # Shipping Street 2
            # Shipping Street 3
            self.mail_address_3 + ', ' + self.mail_address_4,  
            '',                     # Shipping Country
            remove_date             # Removed
        ]

        writer.writerow(record)


def merge(owners, licenses):
    """
    Adds business licenses to property owners.

    @param owners Array of PropertyOwner
    @param licenses Array of BusinessLicense
    """

    def get_normal(addr):
        """Looks for exact match of business address in property owners list"""
        try:
            return o_map[addr]
        except KeyError:
            return None

    def get_manual(addr):
        """Looks for match on business address in ADDRESS_OWNERS 
        hard coded list"""
        try:
            property_addr = ADDRESS_OWNERS[addr]
            return get_normal(property_addr)
        except KeyError:
            return None

    address_manager = REGISTRY['address_manager']
    error_manager = REGISTRY['error_manager']

    o_map = {}
    for owner in owners:
        addr = address_manager.clean(owner.civic, is_strong=True)
        o_map[addr] = owner

    for business_license in licenses:
        addr = address_manager.clean(business_license.address, is_strong=True)

        owner = get_normal(addr)
        if not owner:
            owner = get_manual(addr)

        if owner:
            owner.licenses.append(business_license)
            business_license.owner = owner
        else:
            error_manager.add(business_license, 'No match in property owners')


def output(owners, filename):
    """Write out final CSV file of owners and licenses"""

    out = open(filename, 'wb')
    writer = csv.writer(out)
    writer.writerow([
        'Property Address',
        'License Type',
        'House',
        'Street',
        'License / Folio number',
        'Civic address',
        'Business name 1',
        'Business name 2',
        'Mail address 1',
        'Mail address 2',
        'Total Assess',
        'Included Assess',
        'Ann Chg',
        'Unit'
    ])

    for owner in owners:
        owner.output_to(writer)


def output_salesforce(owners, filename):
    """Write out CSV file of owners and licenses,
    with headers for import into Salesforce."""

    out = open(filename, 'wb')
    writer = csv.writer(out)
    writer.writerow([
        'Record Owner',
        'Account Name',
        'Parent Account',
        'Phone',
        'Business License Type',
        'License Number',
        'Folio Number',
        'Total Assessment',
        'Included Assessment',
        'Annual Charge',
        'Business Name',
        'Business Name 2',
        'Street Name',
        'Unit',
        'Billing Street 1',
        'Billing City',
        'Billing State',
        'Billing Postal Code',
        'Billing Country',
        'Shipping Street 1',
        'Shipping Street 2',
        'Shipping Street 3',
        'Shipping Country',
        'Removed'
        #'Shipping City',
        #'Shipping State',
        #'Shipping Postal Code',
    ])

    for owner in owners:
        owner.output_salesforce_to(writer)

    # Now add removed items

    today = datetime.date.today()
    remove_date = '%s/%s/%s 12:00 PM' % (today.day, today.month, today.year)
    root = os.path.abspath(os.path.dirname(sys.argv[0]))

    removed_po_filename = '%s/removed_cache_PO.csv' % root
    removed_po = wrapped(PropertyOwner.load, [removed_po_filename], True)
    for obj in removed_po:
        obj.output_salesforce_to(writer, remove_date=remove_date)

    removed_bl_filename = '%s/removed_cache_BL.csv' % root
    removed_bl = wrapped(BusinessLicense.load, [removed_bl_filename], True)
    for obj in removed_bl:
        obj.output_salesforce_to(writer, remove_date=remove_date)


def archive(po_filename, bl_filename):
    """Moves the uploaded Property Owners and 
    Business Licenses files to an archive file"""

    # Store archive in same dir as this script
    root = os.path.abspath(os.path.dirname(sys.argv[0]))

    po_archive = root + '/po.csv.%s' % datetime.date.today()
    bl_archive = root + '/bl.csv.%s' % datetime.date.today()

    shutil.move(po_filename, po_archive)
    shutil.move(bl_filename, bl_archive)

    perms = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
    os.chmod(po_archive, perms)
    os.chmod(bl_archive, perms)


def wrapped(func, args, is_quiet):
    """Runs func within a try except
    which catches all exceptions, logs to syslog,
    and output if not in quiet mode.
    @param func Function to run
    @param args Array of arguments to func
    @param is_quiet Boolean, if True doesn't print anything to stdout.

    If there was an exception, this exits with return code 1.
    """

    try:
        ret = func(*args)       # pylint: disable-msg=W0142
    except Exception, exc:      # pylint: disable-msg=W0703
        syslog.syslog('merge.py ' +
                'Exception running %s: %s' % (func.__name__, unicode(exc)))
        import traceback
        syslog.syslog(traceback.format_exc())
        if not is_quiet:
            print(exc)
        sys.exit(1)

    return ret


def main():
    """Main"""

    if not len(sys.argv) in [6, 7]:
        print('%d arguments, expected 6 or 7' % len(sys.argv))
        print('Usage: merge.py <property_owners.csv> ' +
                              '<business_licenses.csv> ' +
                              '<output.csv> ' +
                              '<error.csv> ' +
                              '<salesforce.csv>' +
                              '[--quiet]')
        syslog.syslog('merge.py: Wrong number of arguments to script')
        sys.exit(1)

    is_quiet = False
    if len(sys.argv) == 7 and sys.argv[-1] == '--quiet':
        is_quiet = True

    # Currying. Saves us from always passing 'is_quiet' when calling 'wrapped'.
    wrap = lambda x, y: wrapped(x, y, is_quiet)

    owners = wrap(PropertyOwner.load, [sys.argv[1]])

    licenses = wrap(BusinessLicense.load, [sys.argv[2]])

    wrap(merge, [owners, licenses])

    wrap(output, [owners, sys.argv[3]])

    error_manager = REGISTRY['error_manager']
    wrap(error_manager.report, [sys.argv[4]])

    wrap(output_salesforce, [owners, sys.argv[5]])

    wrap(archive, [sys.argv[1], sys.argv[2]])


REGISTRY['address_manager'] = AddressManager()
REGISTRY['error_manager'] = ErrorManager()


if __name__ == '__main__':
    main()
