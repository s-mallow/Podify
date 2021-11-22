import requests
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer
import random
import sys
import string
import os
import threading
import json
import datetime
import time

refresh_token = ''
access_token = ''
token_expire = datetime.datetime.now()
port = 8420
auth_url = 'https://accounts.spotify.com/authorize'
access_url = 'https://accounts.spotify.com/api/token'
client_id = <client-id>
client_secret = <client-secret>
redirect_uri = 'http://localhost' + ':' + str(port)
state = ''.join(random.choice(string.ascii_lowercase) for i in range(20))



class GetHandler(BaseHTTPRequestHandler):
    code = 'return value of user login'  # has to be set according to answer

    # Handle GETS
    def do_GET(self):
        URL = 'https://' + self.address_string() + self.path
        parsed_url = urlparse(URL)
        query = parse_qs(parsed_url.query)
        # check which response we got
        self.send_error(401, message="Temporary implementation of the Server", explain="2lazy4HTML")
        if 'code' in query:
            # we got the authprozation code
            if str(query['state'][0]) != state:
                print("Fatal: states did not match.")
                sys.exit(1)
            GetHandler.code = query['code'][0]
            time.sleep(4)
            assassin = threading.Thread(target=self.server.shutdown)
            assassin.daemon = True
            assassin.start()
        # if query.has_key('refresh_token'):
        # we just got the token or refreshed
        elif 'error' in query:
            # error handling routine
            print("[-]There was an error with the Authorization request. Did the user decline?")
            sys.exit(1)


def request_authorization():
    response_type = 'code'
    scope = 'user-read-playback-state user-modify-playback-state user-read-private  user-read-recently-played'

    payload1 = {'client_id': client_id,
                'response_type': response_type,
                'redirect_uri': redirect_uri,
                'state': state,
                'scope': scope}
    print("[*]Request Authorization ...")
    s1 = requests.get(auth_url, params=payload1)
    os.startfile(s1.url)


def request_token(code):
    global refresh_token, access_token, token_expire
    grant_type = "authorization_code"

    payload2 = {'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': grant_type,
                'code': code,
                'redirect_uri': redirect_uri}
    while True:
        s2 = requests.post(access_url, data=payload2)
        if s2.status_code == 200:
            content = json.loads(s2.content)
            if 'access_token' in content:
                break
    access_token = content['access_token']
    refresh_token = content['refresh_token']
    token_expire = datetime.datetime.now() + datetime.timedelta(seconds = content['expires_in'])
    with open("SpoDo.cfg",'w') as file:
        file.write(refresh_token)


def dorefresh_token():
    global refresh_token, access_token, token_expire

    payload3 = {'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token}
    while True:
        s3 = requests.post(access_url, data=payload3)
        time.sleep(1)
        if s3.status_code == 200:
            break
    content = json.loads(s3.content)
    access_token = content['access_token']
    token_expire = datetime.datetime.now() + datetime.timedelta(seconds=content['expires_in'])


def getaccesstoken():
    if not restoretoken():
        #print("This is the state ", state)
        request_authorization()
        # setup server for reply
        server = HTTPServer(('', port), GetHandler)
        print('[*]Starting server')
        server.serve_forever()
        print('[*]Server terminated')
        request_token(GetHandler.code)
        print('[*]Got AcessToken: ',access_token)
    print('[*]Token valid until: ',token_expire)
    return access_token

def restoretoken():
    global refresh_token
    try:
        with open("SpoDo.cfg",'r') as file:
            refresh_token = file.read()
            if len(refresh_token) > 0:
                refreshtoken()
                return True
            else:
                return False
    except:
        return False

def refreshtoken():
    if token_expire - datetime.timedelta(minutes=20) < datetime.datetime.now():
        print('[*]Refreshing Token')
        dorefresh_token()
    return access_token


