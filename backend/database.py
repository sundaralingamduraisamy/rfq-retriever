import psycopg2
from psycopg2.pool import SimpleConnectionPool
from settings import settings

class DatabaseManager:
    """PostgreSQL connection pool manager"""

    def __init__(self):
        try:
            self.pool = SimpleConnectionPool(
                1, 5, # ID, Pool Size
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                connect_timeout=5
            )
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            raise

    def get_connection(self):
        return self.pool.getconn()

    def return_connection(self, conn):
        self.pool.putconn(conn)

    def close_all(self):
        self.pool.closeall()

    def execute_query(self, query: str, params: tuple = None):
        """Execute SELECT query"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except psycopg2.Error as e:
            print(f"❌ Query error: {e}")
            return []
        finally:
            cursor.close()
            self.return_connection(conn)

    def execute_query_single(self, query: str, params: tuple = None):
        """Execute SELECT and return single result"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        except psycopg2.Error as e:
            print(f"❌ Query error: {e}")
            return None
        finally:
            cursor.close()
            self.return_connection(conn)

    def execute_update(self, query: str, params: tuple = None) -> bool:
        """Execute INSERT/UPDATE/DELETE"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
            return True
        except psycopg2.Error as e:
            conn.rollback()
            print(f"❌ Update error: {e}")
            return False
        finally:
            cursor.close()
            self.return_connection(conn)

    def create_tables(self):
        """Create necessary database tables"""
        queries = [
            "CREATE EXTENSION IF NOT EXISTS vector;",
            """
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                filename TEXT UNIQUE NOT NULL,
                category TEXT,
                file_size INTEGER,
                file_content BYTEA,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS document_summaries (
                id SERIAL PRIMARY KEY,
                document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                summary_text TEXT,
                word_count INTEGER,
                UNIQUE(document_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS summary_embeddings (
                id SERIAL PRIMARY KEY,
                summary_id INTEGER REFERENCES document_summaries(id) ON DELETE CASCADE,
                embedding vector(384),
                UNIQUE(summary_id)
            );
            """
        ]
        
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                for query in queries:
                    cur.execute(query)
                conn.commit()
                print("✅ Database tables created successfully")
        except psycopg2.Error as e:
            conn.rollback()
            print(f"❌ Failed to create tables: {e}")
            raise
        finally:
            self.return_connection(conn)

# Singleton instance
try:
    db = DatabaseManager()
except Exception as e:
    print(f"⚠️ Database initialization failed: {e}")
    db = None

