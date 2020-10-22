import configparser
import psycopg2
from sql_queries import copy_table_queries, insert_table_queries


def load_staging_tables(cur, conn):
    """
    Load staging tables from S3 buckets

    Arg(s):
        cur: cursor to the database
        conn: connection object to the database
    """
    for query in copy_table_queries:
        cur.execute(query)
        conn.commit()


def insert_tables(cur, conn):
    """
    Transform data in staging tables and insert them into analytics tables

    Arg(s):
        cur: cursor to the database
        conn: connection object to the database
    """
    for query in insert_table_queries:
        cur.execute(query)
        conn.commit()


def main():
    config = configparser.ConfigParser()
    config.read('dwh.cfg')

    conn = psycopg2.connect("host={} dbname={} user={} password={} port={}".format(*config['CLUSTER'].values()))
    cur = conn.cursor()
    
    print('Loading staging tables. This may take up to 2 hours if using complete song dataset...')
    load_staging_tables(cur, conn)
    print('Inserting fact/dim tables...')
    insert_tables(cur, conn)

    conn.close()


if __name__ == "__main__":
    main()