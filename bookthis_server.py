'''
The MIT License (MIT)
Copyright (c) 2013 Dave P.
'''

import signal
import sys
import ssl
from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer, SimpleSSLWebSocketServer
from optparse import OptionParser
from collections import defaultdict
import json

# username - client
clients = {} 
offline_client_data = defaultdict(list)

class SimpleEcho(WebSocket):

   def handleMessage(self):
       print('\n' + '*'*80 + '\n')
       # types of messages...
        # 1 - username/password auth
        # 2 - tab data sent
       data = json.loads(self.data)
       if data['kind'] == 'auth':
           print('received auth')
           print(data)
           username = data['username']
           # check to make sure client isn't already on
           if username not in clients:
               clients[username] = self
               # check if any data to pass to user
               if len(offline_client_data[username]) != 0:
                   print('{} tabs to send {}'.format(len(offline_client_data[username]), username))
                   print(offline_client_data[username])
                   for tab in offline_client_data[username]:
                       self.sendMessage(json.dumps({'kind':'tab', 'data': tab}))
                   # clear the data queue after sending
                   offline_client_data[username].clear() 
           else:
                print('ERROR: {} is already logged in!'.format(username))
           print(clients)

       elif data['kind'] == 'tab':
           print('recieved tab')
           print(data)
           target = self.data['username']
           tab = self.data['tab'] 
           # look for target user
             # if not signed on, store to be synced on connection
           if target not in clients:
               print('{} is not logged on, saving data'.format(target))
               offline_client_data[target].append(tab)
             # if signed on, send data
           else:
               print('{} is logged on, sending data'.format(target))
               clients[target].sendMessage(json.dumps({'kind':'tab', 'data':tab}))

       else:
           print('UH OH, UNRECOGNIZED MESSAGE TYPE')
           print(data)
       print('\n' + '*'*80 + '\n')


   def handleConnected(self):
       print('\n' + '*'*80 + '\n')
       print("{0} connected!".format(self.address))
       # request the client's user_name
       self.sendMessage(json.dumps({'kind': 'auth'}))
       print('\n' + '*'*80 + '\n')

   def handleClose(self):
       # TODO more elegant way of removing self?? 
       print('\n' + '*'*80 + '\n')
       print('removing user')
       print(self)
       for username in clients:
            if self == clients[username]:
                del clients[username]
       print(clients)
       print('\n' + '*'*80 + '\n')


if __name__ == "__main__":

   parser = OptionParser(usage="usage: %prog [options]", version="%prog 1.0")
   parser.add_option("--host", default='', type='string', action="store", dest="host", help="hostname (localhost)")
   parser.add_option("--port", default=8000, type='int', action="store", dest="port", help="port (8000)")
   parser.add_option("--example", default='echo', type='string', action="store", dest="example", help="echo, chat")
   parser.add_option("--ssl", default=0, type='int', action="store", dest="ssl", help="ssl (1: on, 0: off (default))")
   parser.add_option("--cert", default='./cert.pem', type='string', action="store", dest="cert", help="cert (./cert.pem)")
   parser.add_option("--ver", default=ssl.PROTOCOL_TLSv1, type=int, action="store", dest="ver", help="ssl version")

   (options, args) = parser.parse_args()

   cls = SimpleEcho

   server = SimpleWebSocketServer(options.host, options.port, cls)

   def close_sig_handler(signal, frame):
      server.close()
      sys.exit()

   signal.signal(signal.SIGINT, close_sig_handler)

   server.serveforever()
