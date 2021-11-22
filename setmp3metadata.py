from pydub import AudioSegment 
import urllib.request
import json
import requests as req
import os
import time
from scipy.io.wavfile import write
import sounddevice as sd
import numpy as np
from pydub import AudioSegment

def detect_leading_silence(sound, silence_threshold=-50.0, chunk_size=10):
    '''
    sound is a pydub.AudioSegment
    silence_threshold in dB
    chunk_size in ms

    iterate over chunks until you find the first one with sound
    '''
    trim_ms = 0 # ms

    assert chunk_size > 0 # to avoid infinite loop
    while sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold and trim_ms < len(sound):
        trim_ms += chunk_size

    return trim_ms


def convert2MP3(inputfile:str,dic,dic_album,foldername) -> None:	#dictionary from "Currently Playing Context" API Object, album is a "Album Object (full)"
	track = dic['item']
	album = track['album']
	imgurl = album['images'][0]['url']
	coverpath = track['id'] + '.jpg'	#the path cover image
	urllib.request.urlretrieve(imgurl, coverpath)
	artists = [x['name'] for x in track['artists']]
	albumartist = [x['name'] for x in dic_album['artists']]
	artists = ', '.join(artists)
	genres = ', '.join(dic_album['genres'])
	songname = track['name']
	tags = 	{"album": album['name'], 
			 "artist": artists, 
			 "release_date": album['release_date'],
			 "track": track['track_number'],
			 "title": songname,
			 "genres": genres,
			 "albumartist": ', '.join(albumartist)}
	for c in ':/\\*?"<>|':
		songname = songname.replace(c,' ')
		foldername = foldername.replace(c, ' ')
	# print("Tags:\n",tags)
	sound = AudioSegment.from_wav(inputfile)
	start_trim = detect_leading_silence(sound)
	end_trim = detect_leading_silence(sound.reverse())

	duration = len(sound)
	trimmed_sound = sound[start_trim:duration-end_trim]
	trimmed_sound.export(foldername + '/' + songname + ' - ' + ', '.join(albumartist) + '.mp3', format="mp3", bitrate='320k', tags=tags, cover=coverpath)
	os.remove(coverpath)