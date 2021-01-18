import os
import logging


class Logger():

    def __init__(self, settings):
        self.config = settings

        log_level = self.config.dict["logging"]["level"].upper()

        # Create a custom logger
        logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s', level=log_level)
        self.logger = logging.getLogger('fHDHR')
        log_file = os.path.join(self.config.internal["paths"]["logs_dir"], 'fHDHR.log')

        # Create handlers
        # c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(log_file)
        # c_handler.setLevel(log_level)
        f_handler.setLevel(log_level)

        # Create formatters and add it to handlers
        # c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # c_handler.setFormatter(c_format)
        f_handler.setFormatter(f_format)

        # Add handlers to the logger
        # logger.addHandler(c_handler)
        self.logger.addHandler(f_handler)

    def __getattr__(self, name):
        ''' will only get called for undefined attributes '''
        if hasattr(self.logger, name):
            return eval("self.logger.%s" % name)
