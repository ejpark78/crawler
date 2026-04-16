import os
import psycopg2
from psycopg2 import pool

# 전역 커넥션 풀 설정
_pool = None

def get_pg_connection():
    """
    환경 변수를 사용하여 PostgreSQL 연결을 설정하고 커넥션 풀에서 연결을 반환합니다.
    """
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            user=os.getenv("POSTGRES_USER", "airflow"),
            password=os.getenv("POSTGRES_PASSWORD", "airflow"),
            host=os.getenv("POSTGRES_HOST", "postgres"),
            database=os.getenv("POSTGRES_DB", "airflow")
        )
    return _pool.getconn()

def release_pg_connection(conn):
    """커넥션을 풀에 반환합니다."""
    global _pool
    if _pool:
        _pool.putconn(conn)
