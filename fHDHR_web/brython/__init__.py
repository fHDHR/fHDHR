

from .brython import Brython
from .brython_stdlib import Brython_stdlib


class fHDHR_Brython():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.brython = Brython(fhdhr)
        self.brython_stdlib = Brython_stdlib(fhdhr)
