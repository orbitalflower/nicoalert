#!/usr/bin/env python

import requests, re, socket, sys
from datetime import datetime
from bs4 import BeautifulSoup

def san(string):
  return re.sub("[^a-zA-Z0-9,_\-\.]", "", string)

def main():
  USERNAME = "user@example.com"
  PASSWORD = "yourpasswordhere"

  # log in, API v2, to get subscriptions only
  r = requests.post("https://secure.nicovideo.jp/secure/login?site=nicoalert",
    data={"mail":USERNAME, "password":PASSWORD})
  ticket = san(BeautifulSoup(r.text).ticket.string)

  r = requests.post("http://api.alert.nicovideo.jp/v2/login", data={"firstRun":"1", "ticket":ticket})
  xml = BeautifulSoup(r.text)
  user_id = san(xml.login.userid.string)
  alert_ticket = san(xml.login.ticket.string)

  r = requests.get("http://api.alert.nicovideo.jp/v2/subscriptions?userId={}&ticket={}".format(user_id, alert_ticket))

  subbed_communities = []
  subbed_users = []
  for sub in BeautifulSoup(r.text).find_all("subscription"):
    if sub.userid:
      subbed_users.append(san(sub.userid.string))
    elif sub.communityid:
      subbed_communities.append(san(sub.communityid.string))

  # log in, old API
  r = requests.post("https://secure.nicovideo.jp/secure/login?site=nicolive_antenna",
    data={"mail":USERNAME, "password":PASSWORD})
  ticket = san(BeautifulSoup(r.text).ticket.string)
  print "[NICO] Logged in."

  # get alert status
  r = requests.get("http://live.nicovideo.jp/api/getalertstatus?ticket={}".format(ticket))
  alertstatus = BeautifulSoup(r.text)

  user_id = san(alertstatus.user_id.string)
  user_hash = san(alertstatus.user_hash.string)

  addr = san(alertstatus.ms.addr.string)
  port = int(san(alertstatus.ms.port.string))
  thread = san(alertstatus.ms.thread.string)

  # read alerts
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect((addr,port))
  sock.sendall('<thread thread="{}" version="20061206" res_from="-1"/>\0'.format(thread))
  print "[NICO] Listening for subscriptions."

  # main alert loop.
  while True:
    rec = sock.recv(4096)
    for (live,com,usr) in re.findall("<chat[^>]*>(\w+),(\w+),(\w+)</chat>", rec):
      (live,com,usr) = (san(live), san(com), san(usr))

      if com in subbed_communities or usr in subbed_users:
        print "========================================"
        print "[NICO] User {} has started a broadcast at {} on {}. <http://live.nicovideo.jp/watch/lv{}>".format(usr,com,datetime.now(),live)
        print "========================================"

    sys.stdout.flush() # force print

if __name__ == "__main__":
  main()
