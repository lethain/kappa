#
#  KappaAppDelegate.py
#  Kappa
#
#  Created by Will Larson on 9/1/08.
#  Copyright Will Larson 2008. All rights reserved.
#

import twitter
import os, objc, pickle, datetime, urllib2, re
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
    timeProgressIndicator = objc.IBOutlet()
    inputTextField = objc.IBOutlet()
    twitDictsController = objc.IBOutlet()
    searchField = objc.IBOutlet()
    publicTimelineMenu = objc.IBOutlet()
    friendsTimelineMenu = objc.IBOutlet()
    atRepliesMenu = objc.IBOutlet()
    tableView = objc.IBOutlet()
    
    prefs = None    # initialized in restorePreferences
    
    progressIndicatorTimer = None
    lastRetrieval = None
    nextRetrieval = None
    twits = []
    twitDicts = []
    api = None    
    retrievedOwnTimeline = False
    
    ''' IBActions for picking feeds. '''
    def toggleMenuItem(self,menuItem):
        if menuItem.state() == 0:
            menuItem.setState_(1)
        else:
            menuItem.setState_(0)
    
    @objc.IBAction
    def togglePublicTimeline_(self,sender):
        self.toggleMenuItem(self.publicTimelineMenu)
        self.prefs['fetch_public_timeline'] = 1 if self.prefs['fetch_public_timeline'] == 0 else 0
        
        
    @objc.IBAction        
    def toggleFriendsTimeline_(self,sender):
        self.toggleMenuItem(self.friendsTimelineMenu)
        self.prefs['fetch_friends_timeline'] = 1 if self.prefs['fetch_friends_timeline'] == 0 else 0
        
    @objc.IBAction
    def toggleAtReplies_(self,sender):
        self.toggleMenuItem(self.atRepliesMenu)
        self.prefs['fetch_at_replies'] = 1 if self.prefs['fetch_at_replies'] == 0 else 0
    
    ''' Serialization '''
    
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
                'fetch_at_replies':0,
                'fetch_public_timeline':0,
                'fetch_friends_timeline':1,
            }
            self.prefs = NSMutableDictionary.dictionaryWithDictionary_(defaults)
            
    def restoreTweets(self):
        try:
            fin = open(self.pathForFile("twits.serialized"),'r')
            self.twits = pickle.load(fin)
            fin.close()
        except IOError:
            self.twits = []
        
    def storePreferences(self):
        newDict = {}
        for key in self.prefs:
            newDict[key] = self.prefs[key]
    
    
        fout = open(self.pathForFile(USER_PREFS_FILE),'w')
        pickle.dump(newDict,fout)
        fout.close()
        
    def storeTweets(self):
        fout = open(self.pathForFile("twits.serialized"),'w')
        pickle.dump(self.twits,fout)
        fout.close()
        
    def incrementProgressIndicator(self):
        self.inputTextField.setBackgroundColor_(self.normalBackground)
        if self.timeProgressIndicator.doubleValue() >= 100.0:
            self.progressIndicatorTimer.invalidate()
            self.resetTime()
        else:
            self.timeProgressIndicator.incrementBy_(1.0)

    def resetTime(self):
        self.timeProgressIndicator.setDoubleValue_(100.0)
        self.checkForTweets()
    
        now = datetime.datetime.now()
        self.lastRetrieval = now
        self.nextRetrieval = now + datetime.timedelta(minutes=int(self.prefs['retrievalInterval']))
        
        # Reset progress indicator.
        self.timeProgressIndicator.setDoubleValue_(0.0)
        interval = (self.prefs['retrievalInterval']*60.0) / 100.0
        
        s = objc.selector(self.incrementProgressIndicator,signature="v@:")
        t = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(interval,self,s,None,True)
        self.progressIndicatorTimer = t
        
    def showPrefsWindow(self):
        self.prefsWindow.makeKeyAndOrderFront_(self)

    ''' Wrappers for Twitter Functionality '''
    
    @objc.IBAction
    def submitTwit_(self,sender):
        self.postMessage(self.inputTextField.stringValue())
    
    def postMessage(self, msg):
        try:
            status = self.api.PostUpdate(msg)
            self.integrateTweets([status])
            self.inputTextField.setStringValue_(u"")
            self.inputWindow.setTitle_(u"140")
            self.inputTextField.setBackgroundColor_(self.normalBackground)
        except urllib2.URLError:            
            self.inputTextField.setBackgroundColor_(self.warningBackground)
            self.inputWindow.setTitle_(u"Couldn't connect To internet (%s)" % (int(140) - int(len(msg))))
            NSLog(u"Kappa: Couldn't connect to internet to send tweet.")
        
    def updateTwitDict(self,tweets=None):
        if tweets is None:
            tweets = self.twits[:50]
    
        def convertTwit(tweet):
            objcDict = {}
            objcDict['time'] = NSDate.dateWithTimeIntervalSince1970_(tweet.created_at_in_seconds)
            objcDict['user'] = tweet.user.screen_name
            objcDict['text'] = tweet.text
            return NSDictionary.dictionaryWithDictionary_(objcDict)
        self.twitDicts = [ convertTwit(x) for x in tweets ]
        self.twitDictsController.rearrangeObjects()

        
    def checkForTweets(self):
        if self.api is not None:
            try:
                if self.retrievedOwnTimeline == False:
                    ownTweets = self.api.GetUserTimeline(self.username())
                    self.integrateTweets(ownTweets)
                newTweets = []
                if self.prefs['fetch_friends_timeline']:
                    newTweets = newTweets + self.api.GetFriendsTimeline()
                if self.prefs['fetch_at_replies']:
                    newTweets = newTweets + self.api.GetReplies()
                if self.prefs['fetch_public_timeline']:
                    newTweets = newTweets + self.api.GetPublicTimeline()
                self.integrateTweets(newTweets)
            except urllib2.URLError:
                NSLog(u"Kappa: Couldn't connect to Twitter to retrieve tweets.")
            self.updateTwitDict()
                        
    def integrateTweets(self,tweets):
        for tweet in tweets:
            self.integrateTweet(tweet)
            
    def integrateTweet(self,tweet):
        tweets = self.twits
        wasInserted = False
        length = len(tweets)
        for i in xrange(0,length,1):
            stored = tweets[i]
            if tweet.id == stored.id:
                break
            elif tweet.id > stored.id:
                tweets.insert(i,tweet)
                break

        if length == 0:
            tweets.insert(-1,tweet)
    
    def login(self):
        if self.prefs['username'] and self.prefs['password']:
            self.api = twitter.Api(username=self.username(),password=self.password())
            return True
        return False

    ''' Application Delegate Methods '''   
    
    def awakeFromNib(self):
        # load serialized data from disk
        self.restorePreferences()
        self.restoreTweets()
        
        # setup menus on/off state
        if self.prefs['fetch_at_replies']:
            self.toggleMenuItem(self.atRepliesMenu)
        if self.prefs['fetch_friends_timeline']:
            self.toggleMenuItem(self.friendsTimelineMenu)
        if self.prefs['fetch_public_timeline']:
            self.toggleMenuItem(self.publicTimelineMenu)        
        
        # setup background stuff
        self.normalBackground = self.inputTextField.backgroundColor()
        self.warningBackground = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.7, 0.65, 0.6, 0.9)
        self.warningBackground.retain()
        
        self.initializedResizing = False
                            
    def applicationWillTerminate_(self,sender):
        self.storePreferences()
        self.storeTweets()
    
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
        
        if self.initializedResizing == True:        
            scrollView = self.tableView.superview().superview()
            f = scrollView.frame()
            #f.origin.y = f.origin.y - 0
            f.size.height = f.size.height - 30
            scrollView.setFrame_(f)
            scrollView.setNeedsDisplay_(True)
            self.searchField.setHidden_(False)
        else:
            self.initializedResizing = True
        

        
    def windowDidResignMain_(self,sender):
        self.inputWindow.orderOut_(self)
        self.searchField.setHidden_(True)
        
        scrollView = self.tableView.superview().superview()
        f = scrollView.frame()
        #f.origin.y = f.origin.y + 0
        f.size.height = f.size.height + 30
        scrollView.setFrame_(f)
        scrollView.setNeedsDisplay_(True)
        
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
        
    ''' Support for NSSearchField '''
    
    
    
    @objc.IBAction
    def search_(self, searchField):
        searchStr = searchField.stringValue()
        if searchStr == u"":
            self.updateTwitDict()
            return
        try:
            SEARCH_RE = re.compile(searchStr, re.MULTILINE|re.IGNORECASE)
            searchField.setTextColor_(NSColor.blackColor())
            def match_search(tweet):
                if SEARCH_RE.match(tweet.user.screen_name) is not None:
                    return True
                if SEARCH_RE.match(tweet.text) is not None:
                    return True
                return False
            matches = [ x for x in self.twits if match_search(x) ]
            self.updateTwitDict(matches)
            
        except re.error:
            searchField.setTextColor_(NSColor.redColor())
            NSLog(u"Kappa: '%s' is not a valid regular expression." % searchStr)
        
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


