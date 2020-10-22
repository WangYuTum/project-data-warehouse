import configparser
import psycopg2
from sql_queries import create_table_queries, drop_table_queries


def drop_tables(cur, conn):
    """
    Drop tables by executing drop table queries.

    Arg(s):
        cur: cursor to the database
        conn: connection object to the database
    """
    for query in drop_table_queries:
        cur.execute(query)
        conn.commit()


def create_tables(cur, conn):
    """
    Create staging tables and analytics tables.

    Arg(s):
        cur: cursor to the database
        conn: connection object to the database
    """
    for query in create_table_queries:
        cur.execute(query)
        conn.commit()


def main():
    config = configparser.ConfigParser()
    config.read('dwh.cfg')

    conn = psycopg2.connect("host={} dbname={} user={} password={} port={}".format(*config['CLUSTER'].values()))
    cur = conn.cursor()

    print('Droping all tables...')
    drop_tables(cur, conn)
    print('Creating tables...')
    create_tables(cur, conn)

    conn.close()
    print('Job finished.')


if __name__ == "__main__":
    main()