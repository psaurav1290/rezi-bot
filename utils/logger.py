import logging
import os.path
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Logger(object):
    def __init__(self, module, debugMode=None):
        logging.basicConfig(filename=os.path.join(BASE_DIR, "logfile.log"), filemode='a', format='%(asctime)s [%(name)s] %(levelname)s %(message)s')
        self.LOGGER = logging.getLogger(module)

        if debugMode == True:
            self.LOGGER.setLevel(logging.DEBUG)
        elif debugMode == False:
            self.LOGGER.setLevel(logging.INFO)


if __name__ == '__main__':
    pass
