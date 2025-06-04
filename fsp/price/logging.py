import logging
from logging.handlers import RotatingFileHandler


logger = logging.getLogger(__name__)
handler = RotatingFileHandler(filename='price/logs.txt', mode='a+',
                              maxBytes=6000, backupCount=6)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s - %(funcName)s - %(lineno)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
