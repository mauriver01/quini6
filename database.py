import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
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
                );

                CREATE TABLE IF NOT EXISTS scraper_log (
                    id          SERIAL PRIMARY KEY,
                    ejecutado   TIMESTAMP DEFAULT NOW(),
                    status      VARCHAR(20),
                    mensaje     TEXT
                );
            """)
        conn.commit()
    print("✅ Base de datos inicializada.")
