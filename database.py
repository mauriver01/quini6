import os
import pg8000.dbapi
from urllib.parse import urlparse

def get_conn():
    url = urlparse(os.environ["DATABASE_URL"])
    conn = pg8000.dbapi.connect(
        host=url.hostname,
        port=url.port or 5432,
        database=url.path[1:],
        user=url.username,
        password=url.password,
        ssl_context=True
    )
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sorteos (
            id          SERIAL PRIMARY KEY,
            fecha       DATE NOT NULL UNIQUE,
            n1          INT NOT NULL,
            n2          INT NOT NULL,
            n3          INT NOT NULL,
            n4          INT NOT NULL,
            n5          INT NOT NULL,
            n6          INT NOT NULL,
            modalidad   VARCHAR(20) DEFAULT 'tradicional',
            creado_en   TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scraper_log (
            id          SERIAL PRIMARY KEY,
            ejecutado   TIMESTAMP DEFAULT NOW(),
            status      VARCHAR(20),
            mensaje     TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Base de datos inicializada.")
