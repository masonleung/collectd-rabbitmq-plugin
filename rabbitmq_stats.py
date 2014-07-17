'''
collectd plugin for RMQ stats
'''

import collectd
import subprocess
import requests

RABBITMQCTL = '/usr/sbin/rabbitmqctl'
NAME = 'rabbitmq'
USERNAME = 'some_username'
PASSWORD = 'some_password'
PORT = 15672

def configure_callback(conf):
  global RABBITMQCTL, USERNAME, PASSWORD, PORT
  for node in conf.children:
    if node.key == 'Rmqctl':
      RABBITMQCTL = node.values[0]
    elif node.key == 'Username':
      USERNAME = node.values[0]
    elif node.key == 'Password':
      PASSWORD = node.values[0]
    elif node.key == 'Port':
      PORT = node.values[0]
    else:
      collectd.warning('unknown key: %s' % node.key)

'''
get messages processed per second via rabbit admin api
'''
def get_message_process_rate():
  url = "http://localhost:%s/api/queues" % int(PORT)

  try:
    data = requests.get(url=url, auth=(USERNAME, PASSWORD)).json()
  except:
    collectd.error('failed: %s', RABBITMQCTL)
    return {}

  message_process_rate = {}
  wants = {'ack_details': 'ack', 'publish_details': 'incoming', 'deliver_get_details': 'deliver', 'redeliver_details': 'redeliver'}

  for d in data:
    if 'message_stats' in d.keys():
      qname = d['name']
      message_process_rate[qname] = {}
      message_stats = d['message_stats']

      for want, value in wants.iteritems():
        if want in message_stats.keys():
          message_process_rate[qname][value] = int(message_stats[want]['rate'])
  return message_process_rate

'''
get queue stats
'''
def get_system_stats():
  args = [RABBITMQCTL, '-q', 'list_queues', 'name', 'messages', 'memory']
  system_stats = {}

  try:
    stats = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  except:
    collectd.error('failed: %s', RABBITMQCTL)
    return {}

  for line in stats.stdout.readlines():
    elements = line.split()
    qname = elements[0]
    system_stats[qname] = {'messages': elements[1], 'memory': elements[2]}

  return system_stats

def get_stats():

  stats = get_system_stats()
  message_process_rate = get_message_process_rate()

  for qname in message_process_rate.keys():
    if stats[qname]:
      stats[qname].update(message_process_rate[qname])
  return stats

def read_callback():
  stats = get_stats()
  if stats:
    for qname in stats:
      data = stats[qname]
      for key in data:
        val = collectd.Values(plugin="%s.%s" % (NAME, q))
        val.type = 'gauge'
        val.type_instance = key
        val.values = [int(data[key])]
        val.dispatch()
    return
  collectd.error('epic fail: no stats yo!!')

collectd.register_config(configure_callback)
collectd.register_read(read_callback)
