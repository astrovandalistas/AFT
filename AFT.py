# -*- coding: utf-8 -*-

import getopt, pygame, subprocess
from time import time, sleep, strptime, strftime, localtime, gmtime
from sys import exit
from calendar import timegm
from threading import Thread
from Queue import Queue
from cPickle import dump, load
from twython import TwythonStreamer
from string import printable
from re import sub

## What to search for
SEARCH_TERMS = ['arquitectura', '#ciudadposible', '#mextropoli','ciudad de méxico']
FESTIVAL_EN = "voice_kal_diphone"
FESTIVAL_ES = "voice_cstr_upc_upm_spanish_hts"
FESTIVALBIN = "./festival"
FESTIVALCMD = "echo \"(LANG) (SayText \\\"XXXXX\\\")\" | "

class TwitterStreamReceiver(TwythonStreamer):
    def __init__(self, *args, **kwargs):
        super(TwitterStreamReceiver, self).__init__(*args, **kwargs)
        self.tweetQ = Queue()
    def on_success(self, data):
        ## no re-tweets
        if (('text' in data) and (self.tweetQ.qsize() < 30)):
            self.tweetQ.put(data['text'].encode('utf-8'))
            print "received %s" % (data['text'].encode('utf-8'))
    def on_error(self, status_code, data):
        print status_code
    def empty(self):
        return self.tweetQ.empty()
    def get(self):
        return self.tweetQ.get()
    def qsize(self):
        return self.tweetQ.qsize()


def displayPhrase(phrase):
    phrase = phrase.replace('\0',' ')
    words = phrase.split()
    for (index,w) in enumerate(words):
        _checkEvent()
        _fadeTextInOut(w)
        index += 1

def _checkEvent():
    for event in pygame.event.get():
        if ((event.type == pygame.QUIT) or
            (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE)):
            raise KeyboardInterrupt

def _fadeTextInOut(txt,bgndColor=(0,0,0),textColor=(255,255,255)):
    mSurface = font.render(txt.decode('utf8')+" ", 1, textColor, bgndColor)
    mRect = mSurface.get_rect()
    scale = min(float(background.get_width())/mRect.width, float(mRect.width)/background.get_width())
    mSurface = pygame.transform.scale(mSurface,(int(scale*mRect.width),int(scale*mRect.height)))
    mRect = mSurface.get_rect(centerx=background.get_width()/2,
                              centery=background.get_height()/2)

    background.fill(bgndColor)
    background.blit(mSurface, mRect)
    screen.blit(background, (0,0))
    pygame.display.flip()
    sleep(0.33)
    background.fill(bgndColor)
    screen.blit(background, (0,0))
    pygame.display.flip()

def _removeNonAscii(s):
    return "".join(i for i in s if i in printable)
def _removeAccents(txt):
    ## hack! to make festival say accents
    txt = txt.replace("á","aa")
    txt = txt.replace("é","ee")
    txt = txt.replace("í","ii")
    txt = txt.replace("ó","oo")
    txt = txt.replace("ú","uu")
    txt = txt.replace("ñ","ny")
    return txt

def sayPhrase(phrase):
    ## clean up ?
    phrase = phrase.replace(",","").replace(".","").replace("?","").replace("!","")

    ## then remove accents and nonAscii characters
    phrase = _removeNonAscii(_removeAccents(phrase))
    toSay = (FESTIVALCMD+FESTIVALBIN).replace("LANG",FESTIVAL_ES)
    toSay = toSay.replace("XXXXX",phrase)
    subprocess.call(toSay, shell=True)

def setup():
    global lastTwitterCheck, myTwitterStream, streamThread
    global background, screen, font
    global logFile
    secrets = {}
    lastTwitterCheck = time()

    flags = pygame.FULLSCREEN|pygame.DOUBLEBUF|pygame.HWSURFACE
    ##flags = pygame.DOUBLEBUF|pygame.HWSURFACE

    pygame.init()
    screen = pygame.display.set_mode((0, 0),flags)
    pygame.display.set_caption('AFT')
    pygame.mouse.set_visible(False)

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0,0,0))

    font = pygame.font.Font("./data/arial.ttf", 800)
    screen.blit(background, (0, 0))
    pygame.display.flip()

    ## read secrets from file
    inFile = open('./data/oauth.txt', 'r')
    for line in inFile:
        (k,v) = line.split()
        secrets[k] = v

    ## start Twitter stream reader
    myTwitterStream = TwitterStreamReceiver(app_key = secrets['CONSUMER_KEY'],
                                            app_secret = secrets['CONSUMER_SECRET'],
                                            oauth_token = secrets['ACCESS_TOKEN'],
                                            oauth_token_secret = secrets['ACCESS_SECRET'])
    streamThread = Thread(target=myTwitterStream.statuses.filter, kwargs={'track':','.join(SEARCH_TERMS)})
    streamThread.start()

    ## open new file for writing log
    logFile = open("data/"+strftime("%Y%m%d-%H%M%S", localtime())+".log", "a")

    ## turn up the volume
    #subprocess.call("amixer set PCM -- -100", shell=True)

def cleanText(text):
    ## removes punctuation
    text = sub(r'[.,;:!?*/+=\-&%^/\\_$~()<>{}\[\]]', ' ', text)
    ## replaces double-spaces with single space
    text = sub(r'( +)', ' ', text)

    ## log
    logFile.write(strftime("%Y%m%d-%H%M%S", localtime())+"***"+text+"\n")
    logFile.flush()

def loop():
    _checkEvent()
    global lastTwitterCheck, myTwitterStream, streamThread
    """
    if(myTwitterStream.qsize() > 2):
        tweetA = myTwitterStream.get().lower()
        tweetV = myTwitterStream.get().lower()

        tweetV = sub(r'(^[rR][tT] )', '', tweetV)
        ## removes hashtags, arrobas and links
        tweetV = sub(r'(#\S+)|(@\S+)|(http://\S+)', '', tweetV)
        ## clean, tag and send text
        cleanText(tweetV)
        displayPhrase(tweetV)

        tweetA = sub(r'(^[rR][tT] )', '', tweetA)
        ## removes hashtags, arrobas and links
        tweetA = sub(r'(#\S+)|(@\S+)|(http://\S+)', '', tweetA)
        ## clean, tag and send text
        cleanText(tweetA)
        sayPhrase(tweetA)
        """

    if(myTwitterStream.qsize() > 1):
        tweet = myTwitterStream.get().lower()

        tweet = sub(r'(^[rR][tT] )', '', tweet)
        ## removes hashtags, arrobas and links
        tweet = sub(r'(#\S+)|(@\S+)|(http://\S+)', '', tweet)
        ## clean, tag and send text
        cleanText(tweet)
        displayPhrase(tweet)
        sayPhrase(tweet)

if __name__=="__main__":
    setup()

    try:
        while(True):
            ## keep it from looping faster than ~60 times per second
            loopStart = time()
            loop()
            loopTime = time()-loopStart
            if (loopTime < 0.016):
                sleep(0.016 - loopTime)
        exit(0)
    except KeyboardInterrupt:
        logFile.close()
        myTwitterStream.disconnect()
        streamThread.join()
        exit(0)
