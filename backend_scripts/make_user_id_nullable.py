"""
Migration script to make user_id nullable in itineraries table
Run this once to allow anonymous users to generate itineraries
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(repo_root, '.env')
load_dotenv(dotenv_path=env_path)

def migrate():
    """Make user_id nullable in itineraries table"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "raahi_ai"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
        )
        cursor = conn.cursor()
        
        print("=" * 60)
        print("🔧 Making user_id nullable in itineraries table")
        print("=" * 60)
        
        # Drop NOT NULL constraint
        print("1. Dropping NOT NULL constraint on user_id...")
        cursor.execute("ALTER TABLE itineraries ALTER COLUMN user_id DROP NOT NULL;")
        
        # Find and drop existing foreign key
        print("2. Finding existing foreign key constraint...")
        cursor.execute("""
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = 'itineraries'::regclass
            AND confrelid = 'users'::regclass
            AND contype = 'f';
        """)
        result = cursor.fetchone()
        
        if result:
            constraint_name = result[0]
            print(f"   Found constraint: {constraint_name}")
            print(f"3. Dropping constraint {constraint_name}...")
            cursor.execute(f"ALTER TABLE itineraries DROP CONSTRAINT {constraint_name};")
        else:
            print("   No foreign key constraint found (may already be dropped)")
        
        # Recreate foreign key with SET NULL
        print("4. Creating new foreign key with SET NULL on delete...")
        cursor.execute("""
            ALTER TABLE itineraries
            ADD CONSTRAINT itineraries_user_id_fkey
            FOREIGN KEY (user_id) 
            REFERENCES users(user_id) 
            ON DELETE SET NULL;
        """)
        
        conn.commit()
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print("Now user_id is optional - anonymous users can generate itineraries")
        print("=" * 60)
        
        cursor.close()
        conn.close()
        
    except psycopg2.errors.DuplicateObject:
        print("⚠️ Foreign key constraint already exists with different name")
        print("   This is okay - the migration is mostly complete")
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    migrate()

