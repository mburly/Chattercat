import multiprocessing
import os

from chattercat.chattercat import Chattercat
from chattercat.constants import ADMIN_DB_NAME
from chattercat.db import connectAdmin
from chattercat.utils import verify, getDateTime

if __name__ == '__main__':
    os.system("")
    streams = verify()
    pool = multiprocessing.Pool(processes=len(streams))
    db = connectAdmin(ADMIN_DB_NAME)
    sql = f'INSERT INTO executions (start, end, userId) VALUES ("{getDateTime()}",NULL,NULL);'
    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()
    try:
        out = pool.map(Chattercat,streams)
        pool.close()
        sql = f'UPDATE executions SET end = "{getDateTime()}" WHERE id = (SELECT MAX(id) FROM executions);'
        cursor.execute(sql)
        db.commit()
        cursor.close()
        db.close()
    except KeyboardInterrupt:
        pool.close()
        sql = f'UPDATE executions SET end = "{getDateTime()}" WHERE id = (SELECT MAX(id) FROM executions);'
        cursor.execute(sql)
        db.commit()
        cursor.close()
        db.close()