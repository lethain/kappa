#
#  main.py
#  Kappa
#
#  Created by Will Larson on 9/1/08.
#  Copyright __MyCompanyName__ 2008. All rights reserved.
#

#import modules required by application
import objc
import Foundation
import AppKit

from PyObjCTools import AppHelper

# import modules containing classes required to start application and load MainMenu.nib
import KappaAppDelegate
import KAPProgressIndicator
import KAPTwitFormatter
import twitter
import simplejson

# pass control to AppKit
AppHelper.runEventLoop()
