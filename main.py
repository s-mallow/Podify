from RequestToken import getaccesstoken,refreshtoken
from setmp3metadata import convert2MP3
import sounddevice as sd
import requests as req
import json
import time
import numpy as np
import RequestToken
import sys
import os
from scipy.io.wavfile import write

access_token = ''
current_url = 'https://api.spotify.com/v1/me/player'
trackdurations = []
trackuris = []
playlistname = ''

def startpremiumrec():
    global access_token
    currentid = 0
    auth = {'Authorization':'Bearer ' + access_token}
    req.put('https://api.spotify.com/v1/me/player/volume?volume_percent=100', headers=auth)
    sd.rec(int(1 * 48000), samplerate=48000, channels=2,blocking=True)
    lastrec = None
    while True:
        access_token = refreshtoken()
        auth = {'Authorization':'Bearer ' + access_token}
        duration = trackdurations[currentid]
        rec = sd.rec(int((duration + 10) * 48000), samplerate=48000, channels=2)
        startrec = time.time()
        data = json.dumps({'uris':[trackuris[currentid]]})
        while req.put('https://api.spotify.com/v1/me/player/play', data=data, headers=auth).status_code != 204:
            time.sleep(1)
            access_token = refreshtoken()
            auth = {'Authorization':'Bearer ' + access_token}
        if time.time() > startrec+7:
            time.sleep(1)
            req.put('https://api.spotify.com/v1/me/player/pause', headers=auth)
            time.sleep(2)
            continue

        while True:
            currentdict = json.loads(req.get('https://api.spotify.com/v1/me/player', headers=auth).content)
            if currentdict['is_playing']:
                break
        currentalbum = json.loads(req.get('https://api.spotify.com/v1/albums/' + currentdict['item']['album']['id'],headers=auth).content)
        if not lastrec is None:
            save(rec=lastrec, dict=lastdict, album=lastalbum)
            print('Saved ' + lastdict['item']['name'])
        sd.wait()
        currentid += 1
        if currentid >= len(trackdurations):
            break
        lastrec = rec
        lastdict = currentdict
        lastalbum = currentalbum
    save(rec=rec,dict=currentdict,album=currentalbum)
    print('Saved ' + currentdict['item']['name'])
    print('Saved all Songs!')
    sys.exit(0)



def startnormalrec(firsttrackrec, firstrecend, lasttimestamp, firstdict, firstalbum):
    global access_token
    currentid = 0 if firsttrackrec is None else 1
    lastrec = None
    while True:
        duration = trackdurations[currentid]
        print(int(time.time()*1000))
        rec = sd.rec(int(duration * 48000), samplerate=48000, channels=2)
        print(int(time.time()*1000))
        access_token = refreshtoken()
        auth = {'Authorization':'Bearer ' + access_token}
        while True:
            currentreq = json.loads(req.get('https://api.spotify.com/v1/me/player',headers=auth).content)
            if currentreq['timestamp'] != lasttimestamp:
                break
        print(currentreq['timestamp'])
        if not currentreq['is_playing']:
            time.sleep(2.5)
            save(lastrec,lastdict)
            sys.exit(0)

        if currentreq['currently_playing_type'] == 'ad':
            while True:
                currentreq = json.loads(req.get('https://api.spotify.com/v1/me/player',headers=auth).content)
                if currentreq['currently_playing_type'] != 'ad':
                    time.sleep(0.7)
                    rec = sd.rec(int(duration * 48000), samplerate=48000, channels=2)
                    print('adsong: ' + currentreq['item']['name'])
                    break

        currentalbum = json.loads(req.get('https://api.spotify.com/v1/albums/' + currentreq['item']['album']['id'],headers=auth).content)

        endrecord = currentreq['timestamp'] + currentreq['item']['duration_ms'] + 700
        if not firsttrackrec is None and int(firstrecend*1000) < endrecord - 20000:
            cur = time.time()
            if(firstrecend + 2.5 > cur):
                time.sleep((firstrecend-cur) + 2.5)
            save(firsttrackrec,firstdict,firstalbum)
            firsttrackrec = None
        if not lastrec is None:
            time.sleep(2.5)
            save(lastrec,lastdict,lastalbum)
        currentid += 1
        lasttimestamp = currentreq['timestamp']
        print('sleeping for ' + str((endrecord/1000-time.time())-0.5) + ' seconds...')
        time.sleep((endrecord/1000-time.time())-0.5)
        while int(time.time()*1000) < endrecord:
            pass
        lastrec = rec
        lastdict = currentreq
        lastalbum = currentalbum


def save(rec, dict,album):
    scaled = np.int16(rec / np.max(np.abs(rec)) * 32767)
    write('temp.wav', 48000, scaled)
    convert2MP3('temp.wav',dict,album,playlistname)
    os.remove('temp.wav')


def main():
    global access_token, trackdurations, trackuris, playlistname
    access_token = getaccesstoken()
    auth = {'Authorization':'Bearer ' + access_token}
    while True:
        res = req.get('https://api.spotify.com/v1/me/player',headers=auth)
        if res.status_code == 204:
            print('Please click on Play and then Pause again!')
            time.sleep(1)
            continue
        if res.status_code != 200:
            print('Something went wrong: Error Code ' + str(res.content))
            continue
        res = json.loads(res.content)
        if res['context'] is None or res['context']['type'] != 'playlist':
            print('Please select a Playlist!')
            time.sleep(1)
            continue
        break

    playlistid = res['context']['uri'].split('playlist:')[1]
    address = 'https://api.spotify.com/v1/playlists/' + playlistid + '/tracks'
    while True:
        trackj = json.loads(req.get(address, headers=auth).content)
        trackdurations += [x['track']['duration_ms']/1000 for x in trackj['items']]
        trackuris += [x['track']['uri'] for x in trackj['items']]
        if trackj['next'] is None:
            break
        address = trackj['next']
    playlistname = json.loads(req.get('https://api.spotify.com/v1/playlists/' + playlistid, headers=auth).content)['name']

    if json.loads(req.get('https://api.spotify.com/v1/me', headers=auth).content)['product'] == 'premium':
        print('Premium detected!')
        currentdict = json.loads(req.get('https://api.spotify.com/v1/me/player', headers=auth).content)
        if currentdict['is_playing']:
            req.put('https://api.spotify.com/v1/me/player/pause', headers=auth)
            time.sleep(2)
        startpremiumrec()

    if res['shuffle_state']:
        print('Please Turn off Shuffle-Mode before starting!')

    currenttrack = json.loads(req.get('https://api.spotify.com/v1/me/player',headers=auth).content)
    if currenttrack['currently_playing_type'] == 'ad':
        sd.rec(int(1 * 48000), samplerate=48000, channels=2,blocking=True)
        while not currenttrack['is_playing']:
            print('Please press Play')
            time.sleep(0.5)
            currenttrack = json.loads(req.get('https://api.spotify.com/v1/me/player',headers=auth).content)
        startnormalrec(None,None,None)
        sys.exit(0)

    while currenttrack['is_playing'] or currenttrack['progress_ms'] != 0:
        print('Please Pause, go to the Beginning of Track and wait')
        time.sleep(0.5)
        currenttrack = json.loads(req.get('https://api.spotify.com/v1/me/player',headers=auth).content)
    time.sleep(1)
    sd.rec(int(1 * 48000), samplerate=48000, channels=2,blocking=True)
    duration = currenttrack['item']['duration_ms'] / 1000 + 30
    firsttrackrec = sd.rec(int(duration * 48000), samplerate=48000, channels=2)
    firstrecend = time.time() + duration
    print('Please press Play')
    while not currenttrack['is_playing']:
        currenttrack = json.loads(req.get('https://api.spotify.com/v1/me/player',headers=auth).content)
    endrecord = currenttrack['timestamp'] + currenttrack['item']['duration_ms'] #+ 700
    firsttracktimestamp = currenttrack['timestamp']
    firsttrackalbum = json.loads(req.get('https://api.spotify.com/v1/albums/' + currenttrack['item']['album']['id'],headers=auth).content)
    print('sleeping for ' + str((endrecord/1000-time.time())-0.5) + ' seconds..')
    time.sleep((endrecord/1000-time.time())-0.5)
    while int(time.time()*1000) < endrecord:
        pass
    startnormalrec(firsttrackrec,firstrecend,firsttracktimestamp,currenttrack,firsttrackalbum)


if __name__ == '__main__':
    main()
