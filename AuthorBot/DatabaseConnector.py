import pymysql
import paramiko
import sys
import sshtunnel

create_table = '''CREATE TABLE DuplicateNames(
        Wikipage CHAR(20) NOT NULL,
        Author_Match CHAR(100) NOT NULL,
        Name_One CHAR(100) NOT NULL,
        Name_Two CHAR(100) NOT NULL
)'''

drop_table  = '''DROP TABLE DUPNAMES'''

#gets sql login information
with open('sql_info.txt') as file:
    _sql_info = file.read().splitlines()

#gets ssh login information
with open('ssh_info.txt') as file:
    _ssh_info = file.read().splitlines()


def create_database_table():
    with sshtunnel.SSHTunnelForwarder(
        ('login.toolforge.org', 22),
        ssh_username=_ssh_info[0],
        ssh_pkey=_ssh_info[1],
        ssh_private_key_password=_ssh_info[2],
        remote_bind_address=('tools.db.svc.wikimedia.cloud', 3306)
    ) as tunnel:
        conn = pymysql.connections.Connection(user=_sql_info[0], password = _sql_info[1], database=_sql_info[2], host = '127.0.0.1', port=tunnel.local_bind_port)
        with conn.cursor() as cur:
            cur.execute(create_table)

def add_multiple_match(multimatch):
    with sshtunnel.SSHTunnelForwarder(
        ('login.toolforge.org', 22),
        ssh_username=_ssh_info[0],
        ssh_pkey=_ssh_info[1],
        ssh_private_key_password=_ssh_info[2],
        remote_bind_address=('tools.db.svc.wikimedia.cloud', 3306)
    ) as tunnel:
        conn = pymysql.connections.Connection(user=_sql_info[0], password = _sql_info[1], database=_sql_info[2], host = '127.0.0.1', port=tunnel.local_bind_port)
        with conn.cursor() as cur:
            for w_match in multimatch:
                for au in multimatch[w_match]:
                    q = sql_add_multiple_matches(w_match, au, multimatch[w_match][au][0][0].toJSON()['id'], multimatch[w_match][au][1][0].toJSON()['id'])
                    cur.execute(q)
        conn.commit()
        conn.close()



def sql_add_multiple_matches(itempage, author_match, name_one, name_two):
    query = "INSERT IGNORE INTO DuplicateNames VALUES ('" + itempage + "', '" + author_match.replace("'", "''") + "', '" +  str(name_one) + "', '" + str(name_two) + "')"
    print(query)
    return query

def get_multimatch_articles():
    with sshtunnel.SSHTunnelForwarder(
        ('login.toolforge.org', 22),
        ssh_username=_ssh_info[0],
        ssh_pkey=_ssh_info[1],
        ssh_private_key_password=_ssh_info[2],
        remote_bind_address=('tools.db.svc.wikimedia.cloud', 3306)
    ) as tunnel:
        conn = pymysql.connections.Connection(user=_sql_info[0], password = _sql_info[1], database=_sql_info[2], host = '127.0.0.1', port=tunnel.local_bind_port)
        with conn.cursor() as cur:
            q = 'SELECT DISTINCT Wikipage FROM DuplicateNames'
            cur.execute(q)
            wikipages = cur.fetchall()
            wikipages = [i[0] for i in wikipages]
        conn.close()
        return wikipages

#create_database_table()
