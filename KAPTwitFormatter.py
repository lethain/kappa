#
#  KAPTwitFormatter.py
#  Kappa
#
#  Created by Will Larson on 9/2/08.
#  Copyright (c) 2008 __MyCompanyName__. All rights reserved.
#

from Foundation import *

class KAPTwitFormatter(NSFormatter):
    
    def stringForObjectValue_(self,obj):
        return obj
        
    def getObjectValue_forString_errorDescription_(self,obj,string,error):
        return (True,string,error)
        
    def getObjectValue_forString_range_error_(self,obj,string,rangep,error):
        return (True, obj,error)
    
    def isPartialStringValid_newEditingString_errorDescription_(self,partialString, newString, error):
        if len(partialString) <= 140:
            return (True,partialString,error)
        else:
            return (False,partialString[:140],error)