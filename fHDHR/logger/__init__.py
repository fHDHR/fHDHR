import os
import logging
from logging.config import dictConfig


class Logger():

    def __init__(self, settings):
        logging_config = {
            'version': 1,
            'formatters': {
                'fHDHR': {
                    'format': '[%(asctime)s] %(levelname)s - %(message)s',
                    },
            },
            'loggers': {
                # all purpose, fHDHR root logger
                'fHDHR': {
                    'level': settings.dict["logging"]["level"].upper(),
                    'handlers': ['console', 'logfile'],
                },
            },
            'handlers': {
                # output on stderr
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'fHDHR',
                },
                # generic purpose log file
                'logfile': {
                    'level': 'DEBUG',
                    'class': 'logging.handlers.TimedRotatingFileHandler',
                    'filename': os.path.join(
                        settings.internal["paths"]["logs_dir"], '.fHDHR.log'),
                    'when': 'midnight',
                    'formatter': 'fHDHR',
                },
            },
        }
        dictConfig(logging_config)
        self.logger = logging.getLogger('fHDHR')

    def __getattr__(self, name):
        ''' will only get called for undefined attributes '''
        if hasattr(self.logger, name):
            return eval("self.logger.%s" % name)
        elif hasattr(self.logger, name.lower()):
            return eval("self.logger.%s" % name.lower())
