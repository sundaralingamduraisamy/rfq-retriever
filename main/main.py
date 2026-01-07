"""
PostgreSQL Document Upload Script
Automatically creates database and table if they don't exist
Uploads all files from 'data' folder to PostgreSQL BYTEA storage
"""

import psycopg2
from psycopg2 import sql
from pathlib import Path
import os
import sys
import codecs
from datetime import datetime

# Force UTF-8 encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# ============================================================================
# CONFIGURATION
# ============================================================================
# PostgreSQL connection details
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5433"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "rahul5757"
POSTGRES_DB_NAME = "documents_db"  # Database to create

# Folder containing files to upload
DATA_FOLDER = "./data"


# ============================================================================
# STEP 1: Create Database if it doesn't exist
# ============================================================================
def create_database_if_not_exists():
    """Create the database if it doesn't exist"""

    # First, connect to default 'postgres' database
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database="postgres"  # Connect to default database
        )

        # Enable autocommit for database creation (required for CREATE DATABASE)
        conn.autocommit = True
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{POSTGRES_DB_NAME}'")
        exists = cursor.fetchone()

        if not exists:
            # Create database
            cursor.execute(f"CREATE DATABASE {POSTGRES_DB_NAME}")
            print(f"✓ Database '{POSTGRES_DB_NAME}' created successfully")
        else:
            print(f"✓ Database '{POSTGRES_DB_NAME}' already exists")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"✗ Error creating database: {e}")
        return False


# ============================================================================
# STEP 2: Create Table if it doesn't exist
# ============================================================================
def create_table_if_not_exists():
    """Create the documents table if it doesn't exist"""

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB_NAME  # Connect to our database
        )

        cursor = conn.cursor()

        # Create table if not exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) UNIQUE NOT NULL,
            file_type VARCHAR(50),
            file_size INT NOT NULL,
            file_content BYTEA NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        cursor.execute(create_table_query)
        conn.commit()

        # Create indexes for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at)")

        conn.commit()
        print("✓ Table 'documents' created successfully (or already exists)")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"✗ Error creating table: {e}")
        return False


# ============================================================================
# STEP 3: Upload files from folder
# ============================================================================
def upload_files_from_folder(folder_path):
    """Upload all files from a folder to PostgreSQL"""

    folder_path = Path(folder_path)

    # Check if folder exists
    if not folder_path.exists():
        print(f"✗ Folder not found: {folder_path}")
        return False

    # Get all files in folder
    files = list(folder_path.iterdir())

    if not files:
        print(f"✗ No files found in folder: {folder_path}")
        return False

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB_NAME
        )

        cursor = conn.cursor()

        success_count = 0
        failed_count = 0
        failed_files = []

        print(f"\n{'=' * 70}")
        print(f"UPLOADING FILES FROM: {folder_path}")
        print(f"{'=' * 70}\n")

        for file_path in files:
            # Skip directories
            if file_path.is_dir():
                continue

            filename = file_path.name
            file_type = file_path.suffix.lower().strip('.')  # e.g., 'pdf', 'docx'

            try:
                # Read file as binary
                with open(file_path, 'rb') as f:
                    file_content = f.read()

                file_size = len(file_content)

                # Insert into database
                cursor.execute("""
                    INSERT INTO documents (filename, document_type, file_size, file_content)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (filename, file_type, file_size, file_content))

                doc_id = cursor.fetchone()[0]
                conn.commit()

                file_size_mb = file_size / (1024 * 1024)
                print(f"✓ Uploaded: {filename:<40} (ID: {doc_id}, Size: {file_size_mb:.2f} MB)")

                success_count += 1

            except Exception as e:
                failed_count += 1
                failed_files.append((filename, str(e)))
                print(f"✗ Failed: {filename:<40} Error: {str(e)[:50]}")

        cursor.close()
        conn.close()

        # Print summary
        print(f"\n{'=' * 70}")
        print("UPLOAD SUMMARY")
        print(f"{'=' * 70}")
        print(f"Total files processed: {success_count + failed_count}")
        print(f"Successfully uploaded: {success_count}")
        print(f"Failed uploads: {failed_count}")

        if failed_files:
            print(f"\nFailed files:")
            for filename, error in failed_files:
                print(f"  - {filename}: {error[:50]}")

        print(f"{'=' * 70}\n")

        return failed_count == 0

    except Exception as e:
        print(f"✗ Error uploading files: {e}")
        return False


# ============================================================================
# STEP 4: List all uploaded documents
# ============================================================================
def list_all_documents():
    """List all documents in the database"""

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB_NAME
        )

        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, filename, document_type, file_size, uploaded_at
            FROM documents
            ORDER BY uploaded_at DESC
        """)

        documents = cursor.fetchall()

        if not documents:
            print("No documents found in database")
            return

        print(f"\n{'=' * 70}")
        print("DOCUMENTS IN DATABASE")
        print(f"{'=' * 70}")
        print(f"{'ID':<5} {'Filename':<35} {'Type':<10} {'Size (MB)':<12}")
        print(f"{'-' * 70}")

        for row in documents:
            doc_id, filename, doc_type, file_size, uploaded_at = row
            file_size_mb = file_size / (1024 * 1024)
            print(f"{doc_id:<5} {filename:<35} {doc_type:<10} {file_size_mb:>10.2f} MB")

        print(f"{'=' * 70}\n")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"✗ Error listing documents: {e}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    """Main function to orchestrate the entire process"""

    print(f"\n{'=' * 70}")
    print("PostgreSQL Document Upload System")
    print(f"{'=' * 70}\n")

    # Step 1: Create database
    print("Step 1: Creating/Checking database...")
    if not create_database_if_not_exists():
        print("Failed to create database. Exiting.")
        return

    # Step 2: Create table
    print("\nStep 2: Creating/Checking table...")
    if not create_table_if_not_exists():
        print("Failed to create table. Exiting.")
        return

    # Step 3: Upload files
    print("\nStep 3: Uploading files...")
    if not upload_files_from_folder(DATA_FOLDER):
        print("Warning: Some files failed to upload")

    # Step 4: List all documents
    print("\nStep 4: Listing all documents...")
    list_all_documents()

    print("✓ Process completed!")


# ============================================================================
# RUN THE SCRIPT
# ============================================================================
if __name__ == "__main__":
    main()