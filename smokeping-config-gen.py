#!/usr/bin/python
# coding: utf-8
import sys
import os
import dns.query
import dns.zone
import shutil
from operator import itemgetter

host_list = []
a_records = []
domain = 'example.com'
nameserver = '192.168.1.100'

target_file_new = '/etc/smokeping/config.d/Targets.new'
target_file_old = '/etc/smokeping/config.d/Targets.old'
target_file_cur = '/etc/smokeping/config.d/Targets'

try:
  z = dns.zone.from_xfr(dns.query.xfr(nameserver, domain))
except:
  sys.stderr.write('Failed to fetch AXFR from the DNS server, quitting!')
  sys.exit(1)
names = z.nodes.keys()
for n in names:
  a_record = z[n].to_text(n)
  # A query object may include multiple answers, seperated by new lines.
  # Split such objects out, and split those individual lines into five i
  # tems in a list, and test if they are A records.
  a = a_record.split('\n')
  b = [c.split(' ', 5) for c in a]
  for host in b:
    if ('IN') in host and ('A') in host:
      a_records.append(host)

sorted_a_records = sorted(a_records, key=itemgetter(0))

targets_header = '''
*** Targets ***

probe = FPing

## You have to edit and uncomment all what you want below this.
# Please, refer to smokeping_config man page for more info
# The given adresses aren't real to avoid DoS.

menu = Top
title = Network Latency Grapher
remark = Welcome to the smokeping website.

+ Local

menu = Local
title = Local Network

++ LocalMachine

menu = Local Machine
title = This host
host = localhost

'''

domain_header = '+ ' + domain.replace('.', '_') + '\n'
domain_menu = 'menu = ' + domain + '\n'
domain_title = 'title = For the domain ' + domain + '\n'

try:
  with open(target_file_new, 'w') as t_file:
    t_file.write(targets_header)
    t_file.write(domain_header)
    t_file.write(domain_menu)
    t_file.write(domain_title)
    menu_item_previous = ''
    for a_record in sorted_a_records:
      try:
        # Build Targets File:
        # Skip if the current host is equal to the last host.
        # Menu items must be unique in smokeping.
        if a_record[0] == menu_item_previous:
            continue
        # Skip wildcard A records.
        if '*' in str(a_record[0]):
            continue
        # Replace any '.' (smokeping does not like) and write the file.
        menu_item = '++ ' + a_record[0].replace('.', '_')
        menu = 'menu = ' + a_record[0].replace('.', '_')
        title = 'title = ' + a_record[0].replace('.', '_')
        host = 'host = ' + a_record[4]

        t_file.write(menu_item + '\n')
        t_file.write(menu + '\n')
        t_file.write(title + '\n')
        t_file.write(host + '\n')
        menu_item_previous = a_record[0]
      except IndexError:
        sys.stderr.write('AXFR list number of items mis-match: '
                          + ''.join(str(i) for i in a_record))
        sys.exit(1)
      except:
        sys.stderr.write('AXFR list import error: '
                         + ''.join(str(i) for i in a_record))
        sys.exit(1)
  try:
    shutil.copyfile(target_file_cur, target_file_old)
  except IOError:
    sys.stdout.write('Smokeping Target file does not exist, creating.')
  shutil.copyfile(target_file_new, target_file_cur)
  t_file.close()
except IOError:
  sys.stderr.write('Unable to write new targets file: ' + targets_file_new)
  sys.exit(1)
