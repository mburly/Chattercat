import multiprocessing
import os

from chattercat.chattercat import Chattercat
import chattercat.db as db
from chattercat.utils import verify

if __name__ == '__main__':
    os.system("")
    streams = verify()
    pool = multiprocessing.Pool(processes=len(streams))
    try:
        out = pool.map(Chattercat,streams)
        pool.close()
    except KeyboardInterrupt:
        db.updateExecution()
        pool.close()