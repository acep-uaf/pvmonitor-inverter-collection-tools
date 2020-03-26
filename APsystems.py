# APsystems
# Web page communications module
# Required class functions
#   setCapabilities()
#   setProfile()
##

class APsystems:
    def __init__(self):
        self.url = "https://apsystemsema.com/ema/index.action"

    def setCapabilities(self,cap):
        return cap

    # APsystems website does not use latest TLS 1.2 protocol
    ##
    def setProfile(self,pro):
        pro.set_preference("security.tls.version.min",1)
        return pro

