import os

import mysql.connector

def extract(channel_name):
    if not os.path.exists('csv'):
        os.mkdir('csv')
    db = mysql.connector.connect(host='localhost',user='root',password='',database=f'cc_{channel_name}')
    cursor = db.cursor()
    dir = os.getcwd().replace('\\','\\\\')
    filename = f'{os.getcwd()}\\csv\\cc_{channel_name}'
    filename_sql = f'{dir}\\\\csv\\\\cc_{channel_name}'
    sql = f"SELECT code INTO OUTFILE '{filename_sql}_table_emotes.csv' FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' LINES TERMINATED BY '\n' FROM emotes;"
    cursor.execute(sql)
    with open(f'{filename}_table_emotes.csv', 'r') as original: data = original.read()
    with open(f'{filename}_table_emotes.csv', 'w') as modified: modified.write('"code"\n' + data)
    sql = f"SELECT message INTO OUTFILE '{filename_sql}_table_messages.csv' FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' LINES TERMINATED BY '\n' FROM messages WHERE session_id = (SELECT MAX(id) FROM sessions);"
    cursor.execute(sql)
    with open(f'{filename}_table_messages.csv', 'r', errors='ignore') as original: data = original.read()
    with open(f'{filename}_table_messages.csv', 'w') as modified: modified.write('"message"\n' + data)
