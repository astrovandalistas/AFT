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
from math import sqrt, ceil
from re import sub

## What to search for
SEARCH_TERMS = ['#ciudadposible', '#mextropoli','ciudad posible']
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

def displayWholePhrase(phrase,bgndColor=(255,255,255),textColor=(0,0,0)):
    _clearScreen(bgndColor)
    font = pygame.font.Font("./data/arial.ttf", 200)
    mRect = pygame.Rect((0,0), screen.get_size())

    screenArea = float(mRect.height*mRect.width)
    phraseArea = float(font.size(phrase.decode('utf8'))[0]*font.size(phrase.decode('utf8'))[1])
    newFontSize = 0.75*sqrt(screenArea/phraseArea)*font.size(phrase.decode('utf8'))[1];
    font = pygame.font.Font("./data/arial.ttf", int(newFontSize))
    fontHeight = font.size(phrase.decode('utf8'))[1]

    y = mRect.top
    i = 0
    text = phrase
    lineSpacing = -2

    while (len(text) > 0):
        # determine if the row of text will be outside our area
        # this shouldn't happen !!!
        if ((y+fontHeight) > mRect.bottom):
            break

        # determine maximum width of line
        while ((font.size(text[:i])[0] < mRect.width) and (i < len(text))):
            i += 1

        # adjust the wrap to the last word
        if (i < len(text)):
            i = text.rfind(" ", 0, i) + 1

        # render on surface
        mSurface = font.render(text[:i].decode('utf8'), 1, textColor, bgndColor)
        background.blit(mSurface, (mRect.left, y))
        y += fontHeight + lineSpacing
        text = text[i:]

    # render on screen
    screen.blit(background, (0, (mRect.height-y)/2))
    pygame.display.flip()

def _clearScreen(bgndColor=(0,0,0)):
    background.fill(bgndColor)
    screen.blit(background, (0,0))
    pygame.display.flip()

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
    phrase = phrase.replace(",","").replace(".","").replace("?","").replace("!","").replace("#","").replace("@","")

    ## then remove accents and nonAscii characters
    phrase = _removeNonAscii(_removeAccents(phrase))
    toSay = (FESTIVALCMD+FESTIVALBIN).replace("LANG",FESTIVAL_ES)
    toSay = toSay.replace("XXXXX",phrase)
    subprocess.call(toSay, shell=True)

def setup():
    global myTwitterStream, streamThread
    global background, screen, font
    global logFile
    secrets = {}

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
    subprocess.call("amixer set PCM -- -100", shell=True)

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
    global myTwitterStream, streamThread

    if(myTwitterStream.qsize() > 0):
        tweet = myTwitterStream.get().lower()
	
        tweet = sub(r'(^[rR][tT] )', '', tweet)
        #solo quitar links:
        tweet = sub(r'(http://\S+)', '', tweet)
        ## clean, tag and send text
        cleanText(tweet)
        #mostrar en pantalla y megafono al mismo tiempo
        displayWholePhrase(tweet)
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
