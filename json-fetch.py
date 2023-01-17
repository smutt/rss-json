#!/usr/bin/env python3

import os
import stat
import re
import requests
from bs4 import BeautifulSoup
from urllib3 import util as Util
from datetime import datetime, date

# Where we start
TOP_URL = 'https://root-servers.org/archives/'
TOP_DIR = 'json/'

# Return dict of files existing locally on disk
# Whitespaces in files are escaped with %20
# top_dir is where to start recursive walk
def get_local_files(top_dir):
  rv = {}
  for dirp, _, files in os.walk(top_dir):
    for ff in files:
      rv[(os.path.join(dirp, ff)).lstrip(top_dir)] = True
  return rv

# Grab links in tags matching regex
# URL => the URL to grab and parse
# regex => regex for matching the links
# tags => a list of [html_tag, attribute] to match regex against
# Returns deduplicated list of links
def get_links(URL, regex, tags=['a', 'href']):
  links = []
  url_t = Util.parse_url(URL)
  
  try:
    req = requests.get(URL)
  except requests.RequestException:
    print("err:req_exception:" + URL)
    return []
  
  if req.status_code == 200:
    soup = BeautifulSoup(req.text, 'html.parser')
    for tag in soup.find_all(tags[0]):
      link = tag.get(tags[1])
      if link is None:
        continue
      for reg in regex:
        if reg.match(link):
          link = link.split('?')[0] # Strip any trailing garbage
          if Util.parse_url(link).host is None:
            links.append(url_t.scheme + '://' + url_t.host + link)
          else:
            links.append(link)
    return list(dict.fromkeys(links))

# Grab a file and write to disk
# Takes a remote URL and a local filename
def download(URL, fname):
  if os.path.exists(fname):
    return

  try:
    req = requests.get(URL, stream=True)
    if req.status_code == 200:
      with open(fname, 'wb') as f:
        for chunk in req.iter_content(chunk_size=1024):
          if chunk: # filter out keep-alive new chunks
            f.write(chunk)
      os.chmod(fname, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH) # 0644
    else:
      print("err:dl_bad_response:" + URL)
  except requests.RequestException:
    print("err:req_exception:" + URL)


###################
# BEGIN EXECUTION #
###################
local_files = get_local_files(TOP_DIR)
for jdate in get_links(TOP_URL, [re.compile('2022.*$')]):
  for jfile in get_links(TOP_URL + jdate, [re.compile('.*\.json$')]):
    jpath = jdate + jfile
    if jpath in local_files:
      continue

    if not os.path.exists(TOP_DIR + jdate):
      os.mkdir(TOP_DIR + jdate)
      os.chmod(TOP_DIR + jdate, stat.S_IRUSR | stat.S_IWUSR |stat.S_IXUSR | \
               stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH) # 0755
    print(jpath)
    download(TOP_URL + jpath, TOP_DIR + jpath)

    
