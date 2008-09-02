#
#  KappaAppDelegate.py
#  Kappa
#
#  Created by Will Larson on 9/1/08.
#  Copyright Will Larson 2008. All rights reserved.
#

import twitter
import os, objc, pickle, datetime
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
    
    prefs = {
        'retrievalInterval':10.0,
        'username':None,
        'password':None,
    }
    
    progressIndicatorTimer = None
    lastRetrieval = None
    nextRetrieval = None
    twits = []
    recentTwit = None
    api = None
    
    def restorePreferences(self):
        try:
            fin = open(self.pathForFile(USER_PREFS_FILE), 'r')
            self.prefs = pickle.load(fin)
            fin.close()
        except IOError:
            pass
        
    def storePreferences(self):
        fout = open(self.pathForFile(USER_PREFS_FILE),'w')
        pickle.dump(self.prefs,fout)
        fout.close()
        
    def incrementProgressIndicator(self):
        if self.timeProgressIndicator.doubleValue() >= 100.0:
            self.progressIndicatorTimer.invalidate()
            self.checkForTweets()
            self.resetTime()
        else:
            self.timeProgressIndicator.incrementBy_(1.0)
    
    def resetTime(self):
        now = datetime.datetime.now()
        self.lastRetrieval = now
        self.nextRetrieval = now + datetime.timedelta(minutes=int(self.prefs['retrievalInterval']))
        
        # Update last retrieval label.
        hour = self.lastRetrieval.hour
        minute = self.lastRetrieval.minute
        minute = minute if minute >= 10 else u"0%s" % minute
        amPM = 'AM' if hour > 12 else 'PM'
        hour = hour - 12 if hour > 12 else hour        
        self.lastTimeLabel.setStringValue_(u"%s:%s %s" % (hour,minute, amPM))
        
        
        # Update next retrieval label.
        hour = self.nextRetrieval.hour
        minute = self.nextRetrieval.minute
        minute = minute if minute >= 10 else u"0%s" % minute
        amPM = 'AM' if hour > 12 else 'PM'
        hour = hour - 12 if hour > 12 else hour        
        self.nextTimeLabel.setStringValue_(u"%s:%s %s" % (hour,minute, amPM))
        
        # Reset progress indicator.
        self.timeProgressIndicator.setDoubleValue_(0.0)
        interval = (self.prefs['retrievalInterval']*60.0) / 100.0
        s = objc.selector(self.incrementProgressIndicator,signature="v@:")
        t = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(interval,self,s,None,True)
        self.progressIndicatorTimer = t

    ''' Wrappers for Twitter Functionality '''
    
    def postMessage(self, msg):
        self.recentTwit = self.api.PostUpdate(msg)
        
    def checkForTweets(self):
        newTweets = self.api.GetUserTimeline(self.username)
        NSLog(u"new tweets: %s" % newTweets)
    
    def login(self):
        if self.prefs['username'] and self.prefs['password']:
            self.api = twitter.Api(username=self.username,password=self.password)
            return True
        return False

            
    
    ''' Application Delegate Methods '''        
                            
    def applicationWillTerminate_(self,sender):
        self.storePreferences()
    
    def applicationDidFinishLaunching_(self, sender):
        self.restorePreferences()
        success = self.login()
        
        self.resetTime()
        
        
        
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


