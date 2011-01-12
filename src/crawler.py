'''
Created on Dec 29, 2010

@author: rucney
'''
# pylint: disable-msg=W0311

import urllib
import csv
import StringIO
import redis
import time
import re
import settings

r = redis.Redis(host='localhost', port=6379, db=0)

def _get_data():
  """get info csv"""
  url = settings.CSV_HAPROXY
  sock = urllib.urlopen(url) 
  csv_source = sock.read()
  csv_source = '\n'.join(csv_source.split('\n')[:-1])
  sock.close()
  return csv_source

def get_all_data():
  """get all"""
  pids = []
  data = []
  while len(pids) < 4:
    csv_source = _get_data()
    string = StringIO.StringIO(csv_source)
    csv_reader = csv.reader(string)
    fields = csv_reader.next()
    all = [] 
    for row in csv_reader:
      item = dict(zip(fields, row))
      all.append(item)   
    pid = all[0].get('pid')
    if pid not in pids:    
      pids.append(pid)
      data.append(all)
  return data

def get_info():
  """get indo html"""
  url = settings.HTML_HAPROXY
  sock = urllib.urlopen(url) 
  html = sock.read()
  nbproc = re.compile('nbproc\ =\ (\d)')
  nbproc = re.findall(nbproc, html)[0]
  process = re.compile('process #(\d)')
  process = re.findall(process, html)[0]
  uptime = re.compile('uptime = </b> (.*)<br>')
  uptime = re.findall(uptime, html)[0] 
  ulimit = re.compile('ulimit-n = (.*)<br>')
  ulimit = re.findall(ulimit, html)[0]
  msock = re.compile('maxsock = </b> (.*); <b>maxconn')
  msock = re.findall(msock, html)[0]
  mconn = re.compile('maxconn = </b> (.*);')
  mconn = re.findall(mconn, html)[0]
  mpipes = re.compile('maxpipes = </b>(.*)<br>')
  mpipes = re.findall(mpipes, html)[0]
  cpipes = re.compile('current pipes = (.*)<br>')
  cpipes = re.findall(cpipes, html)[0]
  pids = []
  processes = []
  l_cconns = []
  l_rtasks1 = []
  l_rtasks2 = []
  while len(processes) < nbproc:
    url = settings.HTML_HAPROXY
    sock = urllib.urlopen(url) 
    html = sock.read()
    process = re.compile('process #(\d)')
    process = re.findall(process, html)[0]  
    cconns = re.compile('current conns = (.*);')
    cconns = re.findall(cconns, html)[0]
    rtasks1 = re.compile('Running tasks: (.*)/')
    rtasks1 = re.findall(rtasks1, html)[0]
    rtasks2 = re.compile('Running tasks: .*/(.*)<')
    rtasks2 = re.findall(rtasks2, html)[0]
    pid = re.compile('pid = </b> (.*) \(')
    pid = re.findall(pid, html)[0]
    
    if process not in processes:
      processes.append(process)
      l_cconns.append(cconns)
      l_rtasks1.append(rtasks1)
      l_rtasks2.append(rtasks2)
      pids.append(pid)      
      
  t_cconns = sum(float(x) for x in l_cconns)
  t_rtasks1 = sum(float(x) for x in l_rtasks1)
  t_rtasks2 = sum(float(x) for x in l_rtasks2)
  
  list1 = {'ulimit': ulimit, 'uptime': uptime, 'msock': msock, 'mconn': mconn, 'mpipes': mpipes, 'cpipes': cpipes}
  list2 = {'cconns': t_cconns, 'running': t_rtasks1, 'tasks': t_rtasks2}
  list1.update(list2)
  pids.sort()
  list1.update({'pids': ', '.join(pids)})
  r.set('list', list1)
  
if __name__ == "__main__":
  while True:
    try:
      print "Getting data..."
      data = get_all_data()
      get_info()
      r.set("data", data)
    except:
      pass
    print "Sleeping..."
    time.sleep(6)
      