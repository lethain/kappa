#
#  KAPProgressIndicator.py
#  Kappa
#
#  Created by Will Larson on 9/2/08.
#  Copyright (c) 2008 __MyCompanyName__. All rights reserved.
#


from Foundation import *
from AppKit import NSApp,NSProgressIndicator

class KAPProgressIndicator(NSProgressIndicator):
    def mouseDown_(self,sender):
        NSApp.delegate().resetTime()
