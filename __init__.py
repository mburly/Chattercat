import multiprocessing
import os

from chattercat.chattercat import Chattercat
from chattercat.constants import EXECUTION_HANDLER_CODES
from chattercat.db import executionHandler
from chattercat.utils import verify

if __name__ == '__main__':
    os.system("")
    streams = verify()
    pool = multiprocessing.Pool(processes=len(streams))
    try:
        out = pool.map(Chattercat,streams)
        pool.close()
    except KeyboardInterrupt:
        executionHandler(EXECUTION_HANDLER_CODES['end'])
        pool.close()