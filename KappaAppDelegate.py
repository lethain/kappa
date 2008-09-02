#
#  KappaAppDelegate.py
#  Kappa
#
#  Created by Will Larson on 9/1/08.
#  Copyright Will Larson 2008. All rights reserved.
#

import twitter
import os, objc, pickle, datetime, urllib2
from Foundation import *
from AppKit import *

"""
    From python-twitter documentation:

      >>> api.PostDirectMessage(user, text)
      >>> api.GetUser(user)
      >>> api.GetReplies()
      >>> api.GetUserTimeline(user)
      >>> api.GetStatus(id)
      >>> api.DestroyStatus(id)
      >>> api.GetFriendsTimeline(user)
      >>> api.GetFriends(user)
      >>> api.GetFollowers()
      >>> api.GetFeatured()
      >>> api.GetDirectMessages()
      >>> api.PostDirectMessage(user, text)
      >>> api.DestroyDirectMessage(id)
      >>> api.DestroyFriendship(user)
      >>> api.CreateFriendship(user)

"""

USER_PREFS_FILE = 'user.prefs'

class KappaAppDelegate(NSObject):
    mainWindow = objc.IBOutlet()
    inputWindow = objc.IBOutlet()
    prefsWindow = objc.IBOutlet()
    lastTimeLabel = objc.IBOutlet()
    nextTimeLabel = objc.IBOutlet()
    timeProgressIndicator = objc.IBOutlet()
    inputTextField = objc.IBOutlet()
    twitDictsController = objc.IBOutlet()
    
    prefs = None    # initialized in restorePreferences
    
    progressIndicatorTimer = None
    lastRetrieval = None
    nextRetrieval = None
    twits = []
    twitDicts = []
    api = None
        
    
    def restorePreferences(self):
        try:
            fin = open(self.pathForFile(USER_PREFS_FILE), 'r')
            self.prefs = NSMutableDictionary.dictionaryWithDictionary_(pickle.load(fin))
            fin.close()
        except IOError:
            defaults = {
                'retrievalInterval':10.0,
                'username':'',
                'password':'',
            }
            self.prefs = NSMutableDictionary.dictionaryWithDictionary_(defaults)
        
    def storePreferences(self):
        newDict = {}
        for key in self.prefs:
            newDict[key] = self.prefs[key]
    
        fout = open(self.pathForFile(USER_PREFS_FILE),'w')
        pickle.dump(newDict,fout)
        fout.close()
        
    def incrementProgressIndicator(self):
        if self.timeProgressIndicator.doubleValue() >= 100.0:
            self.progressIndicatorTimer.invalidate()
            self.resetTime()
        else:
            self.timeProgressIndicator.incrementBy_(1.0)
            
    def kappaTime(self,dt):
        'Takes a datetime and returns a string in "6:04 AM" format.'
        amPm = 'AM' if dt.hour < 12 or dt.hour == 24 else 'PM'
        hour = dt.hour - 12 if dt.hour > 12 else dt.hour
        minute = dt.minute if dt.minute >= 10 else u"0%s" % dt.minute
        return u"%s:%s %s" % (hour,minute,amPm)
    
    def resetTime(self):
        self.timeProgressIndicator.setDoubleValue_(100.0)
        self.checkForTweets()
    
        now = datetime.datetime.now()
        self.lastRetrieval = now
        self.nextRetrieval = now + datetime.timedelta(minutes=int(self.prefs['retrievalInterval']))
        
        # Update last retrieval label.
        self.lastTimeLabel.setStringValue_(self.kappaTime(self.lastRetrieval))
        
        # Update next retrieval label.
        self.nextTimeLabel.setStringValue_(self.kappaTime(self.nextRetrieval))
        
        # Reset progress indicator.
        self.timeProgressIndicator.setDoubleValue_(0.0)
        interval = (self.prefs['retrievalInterval']*60.0) / 100.0
        
        s = objc.selector(self.incrementProgressIndicator,signature="v@:")
        t = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(interval,self,s,None,True)
        self.progressIndicatorTimer = t
        
    def showPrefsWindow(self):
        NSLog(u"show prefs window")
        self.prefsWindow.makeKeyAndOrderFront_(self)

    ''' Wrappers for Twitter Functionality '''
    
    @objc.IBAction
    def submitTwit_(self,sender):
        NSLog(u"submitting tweet")
        #self.postMessage(self.inputTextField.stringValue())
        self.inputTextField.setStringValue_(u"")
        self.inputWindow.setTitle_(u"140")
    
    def postMessage(self, msg):
        self.recentTwit = self.api.PostUpdate(msg)
        
    def updateTwitDict(self):
        def convertTwit(tweet):
            objcDict = {} #NSMutableDictionary.alloc().init()
            objcDict['time'] = self.kappaTime(datetime.datetime.utcfromtimestamp(tweet.created_at_in_seconds))
            objcDict['user'] = tweet.user
            objcDict['text'] = tweet.text
            return NSDictionary.dictionaryWithDictionary_(objcDict)
            return objcDict

        NSLog(u"self.twits: %s" % self.twits)
        self.twitDicts = [ convertTwit(x) for x in self.twits[:50] ]
        NSLog(u"self.twitDicts: %s" % self.twitDicts)

        
    def checkForTweets(self):
        if self.api is not None:
            try:
                newTweets = self.api.GetFriendsTimeline()
                self.integrateTweets(newTweets)
            except urllib2.URLError:
                pass
                
            self.updateTwitDict()
            NSLog(u"updated twit dict")
            self.twitDictsController.rearrangeObjects()
            NSLog(u"rearranged array controller")
                        
    def integrateTweets(self,tweets):
        for tweet in tweets:
            self.integrateTweet(tweet)
        NSLog(u"tweets: %s" % self.twits)
            
    def integrateTweet(self,tweet):
        tweets = self.twits
        wasInserted = False
        for i in xrange(0,len(tweets),1):
            stored = tweets[i]
            if tweet.id == stored.id:
                break
            elif tweet.created_at_in_seconds > stored.created_at_in_seconds:
                tweets.insert(i,tweet)
                wasInserted = True
        if not wasInserted:
            tweets.insert(-1,tweet)
    
    def login(self):
        if self.prefs['username'] and self.prefs['password']:
            self.api = twitter.Api(username=self.username(),password=self.password())
            return True
        return False

            
    
    ''' Application Delegate Methods '''   
    
    def awakeFromNib(self):
        self.restorePreferences()
                            
    def applicationWillTerminate_(self,sender):
        self.storePreferences()
    
    def applicationDidFinishLaunching_(self, sender):
        if self.login():
            self.resetTime()
        else:
            self.showPrefsWindow()
            
    def resizeInput(self):
        mainFrame = self.mainWindow.frame()        
        frameRect = NSMakeRect(mainFrame.origin.x,mainFrame.origin.y-40, mainFrame.size.width, 40)
        self.inputWindow.setFrame_display_(frameRect, True)
    
    def windowDidBecomeMain_(self,sender):
        self.inputWindow.orderFront_(self)
        self.resizeInput()
        
    def windowDidResignMain_(self,sender):
        self.inputWindow.orderOut_(self)
        
    def windowDidMove_(self,notification):
        self.resizeInput()
        
    def windowDidResize_(self,notification):
        self.resizeInput()
        
    ''' NSControl delegate methods '''
    
    def controlTextDidChange_(self,notification):
        txt = self.inputTextField.stringValue()
        self.inputWindow.setTitle_(u"%s" % unicode(140-len(txt)))
    
    ''' Application Delegate Utility Methods '''
            
    def applicationSupportFolder(self):
        paths = NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory,NSUserDomainMask,True)
        basePath = (len(paths) > 0 and paths[0]) or NSTemporaryDirectory()
        fullPath = basePath.stringByAppendingPathComponent_("Kappa")
        if not os.path.exists(fullPath):
            os.mkdir(fullPath)
        return fullPath
        
    def pathForFile(self,filename):
        return self.applicationSupportFolder().stringByAppendingPathComponent_(filename)
        
    ''' Accessors and mutators '''
    
    def username(self):
        return self.prefs['username']
        
    def setUsername_(self,val):
        self.prefs['username'] = val
        self.login()
        
    def password(self):
        return self.prefs['password']
        
    def setPassword_(self,val):
        self.prefs['password'] = val
        self.login()
        
    def retrievalInterval(self):
        return self.prefs['retrievalInterval']
        
    def setRetrievalInterval(self,val):
        self.prefs['retrievalInterval'] = val


