'''
Created on Jan 3, 2011

@author: rucney
'''
# pylint: disable-msg=W0311, E1101

import redis
import bottle
import pprint
import operator
import itertools

r = redis.Redis(host='localhost', port=6379, db=0)

def humanize_time(secs):
  """convert datetime""" 
  mins, secs = divmod(int(secs), 60)
  hours, mins = divmod(mins, 60)
  days, hours = divmod(hours, 24)
  if mins == 0:
    return '%ds' % (secs)
  elif hours == 0:
    return '%dm:%ds' % (mins, secs)      
  elif days == 0:
    return '%dh:%dm' % (hours, mins)
  else:
    return '%dd%dh' % (days, hours)

def group(number):
  """prcess number"""
  s = '%d' % number
  groups = []
  while s and s[-1].isdigit():
    groups.append(s[-3:])
    s = s[:-3]
  return s + ' '.join(reversed(groups))
  
def parsing(data):
  """parsing data"""
  results = []
  for i in range(len(data[0])):
    items = {}
    for key in data[0][0].keys():
      res = []
      for n in range(0, 4):
        res.append(data[n][i][key])
      items[key] = res
    results.append(items)
  
  info = []
  for i in results:
    items = {}
    for key in i.keys():
      values = i[key]
      if len(set(values)) == 1:
        items[key] = values[0]
      else:
        if values[0].isdigit() == True:
          if key != 'lastchg':
            items[key] = sum([int(x) for x in values])
            items[key] = group(items[key])
          else:
            items[key] = values[-1]
        
    info.append(items)
  return info
  
def info_data():
  raw_data = eval(r.get("data")) 
  info = parsing(raw_data)
#  pprint.pprint(info)
  info.sort(key=operator.itemgetter('# pxname'))
#  pprint.pprint(info)
  list1 = []
  for key, item in itertools.groupby(info, operator.itemgetter('# pxname')):
    list1.append(list(item))
#  pprint.pprint(list1)
  info = list1
  
  for k in info:
    for i in k:
      a = i['lastchg'].replace(' ', '')
      b = i['downtime'].replace(' ', '')
      if a.isdigit() == True:
        i['lastchg'] = humanize_time(a)  
        i['downtime'] = humanize_time(b)
  return info

maps = {'haproxy': 'web.html', 'haproxy;up': 'web_hidedown'}
map1 = {'haproxy;norefresh': 'web_norefresh', 'haproxy;up;norefresh': 'web_hidedown_norefresh'}
maps.update(map1)
r.mset(maps)
@bottle.route('/:names')
def main(names):
  top = eval(r.get('list'))
  info = info_data()
  return bottle.jinja2_template(r.get(names), info = info, top = top)
@bottle.route('/haproxy;csv;norefresh')  
def csv():
  return r.get("csv")

#####################
if __name__ == "__main__":
  bottle.debug(True)
  bottle.run(port=8088)

  