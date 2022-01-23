
from fHDHR.exceptions import TunerError

# TODO write this method


class Direct_HardWare_Stream():
    """
    A method to stream from /dev/ hardware devices directly.
    """

    def __init__(self, fhdhr, stream_args, tuner):
        self.fhdhr = fhdhr
        self.stream_args = stream_args
        self.tuner = tuner

        self.bytes_per_read = int(self.fhdhr.config.dict["streaming"]["bytes_per_read"])

        raise TunerError("806 - Tune Failed: Feature not implemented")
