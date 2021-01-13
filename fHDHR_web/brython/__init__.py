

from .brython import Brython
from .brython_stdlib import Brython_stdlib

from .brython_bry import Brython_bry


class fHDHR_Brython():

    def __init__(self, fhdhr):
        self.fhdhr = fhdhr

        self.brython = Brython(fhdhr)
        self.brython_stdlib = Brython_stdlib(fhdhr)

        self.brython_bry = Brython_bry(fhdhr)
