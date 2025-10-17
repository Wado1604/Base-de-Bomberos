import mysql.connector
import json

cfg = dict(host='localhost', user='root', password='Bomberos12', database='bomberos')
conn = mysql.connector.connect(**cfg)
cur = conn.cursor()
print('DESCRIBE bomberos:')
cur.execute('DESCRIBE bomberos')
for row in cur.fetchall():
    print(row)

print('\nSAMPLE rows (first 5):')
cur.execute('SELECT * FROM bomberos LIMIT 5')
cols = [d[0] for d in cur.description]
for r in cur.fetchall():
    obj = dict(zip(cols, r))
    print(json.dumps(obj, default=str, ensure_ascii=False))

cur.close()
conn.close()
