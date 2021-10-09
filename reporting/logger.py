import logging


class Logger:

    def __init__(self, prefix: str, logging_level=logging.INFO):
        logger = logging
        logger.basicConfig(level=logging_level)
        self.__log = logger.getLogger("[REPORTING][{}]".format(prefix))

    @property
    def log(self):
        return self.__log
