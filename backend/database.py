import psycopg2
from psycopg2.pool import SimpleConnectionPool
from settings import settings

class DatabaseManager:
    """PostgreSQL connection pool manager"""

    def __init__(self):
        self._ensure_database_exists()
        try:
            self.pool = SimpleConnectionPool(
                1, 5, # ID, Pool Size
                host=settings.POSTGRES_HOST,
                port=int(settings.POSTGRES_PORT),
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                connect_timeout=5
            )
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            raise

    def _ensure_database_exists(self):
        """Check if target database exists, if not create it."""
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        try:
            # Connect to default 'postgres' db
            conn = psycopg2.connect(
                dbname='postgres',
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                host=settings.POSTGRES_HOST,
                port=int(settings.POSTGRES_PORT)
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            
            # Check existence
            cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{settings.POSTGRES_DB}'")
            exists = cur.fetchone()
            
            if not exists:
                print(f"🛠️  Database '{settings.POSTGRES_DB}' not found. Creating...")
                cur.execute(f"CREATE DATABASE {settings.POSTGRES_DB}")
                print(f"✅ Database '{settings.POSTGRES_DB}' created successfully.")
            
            cur.close()
            conn.close()
        except Exception as e:
            print(f"⚠️ Warning: Could not verify/create database: {e}")
            # We don't raise here, we let the main connection attempt fail if it must.

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

    def execute_insert_returning(self, query: str, params: tuple = None):
        """Execute INSERT and return a single result (e.g. ID)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            result = cursor.fetchone()
            conn.commit()
            return result
        except psycopg2.Error as e:
            conn.rollback()
            print(f"❌ Insert error: {e}")
            return None
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
            """,
            """
            CREATE TABLE IF NOT EXISTS generated_rfqs (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                content TEXT,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS document_images (
                id SERIAL PRIMARY KEY,
                document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                image_data BYTEA NOT NULL,
                description TEXT,
                metadata JSONB,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS image_embeddings (
                id SERIAL PRIMARY KEY,
                image_id INTEGER REFERENCES document_images(id) ON DELETE CASCADE,
                embedding vector(768),
                UNIQUE(image_id)
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

