"""
CivicAI Bangladesh - Automated Database Backup & Snapshot Engine
Supports both local SQLite database snapshots and PostgreSQL / Neon exports.
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backups_dir = os.path.join(base_dir, "database", "backups")
os.makedirs(backups_dir, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database/civicai.db")

def perform_backup():
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    print("=" * 60)
    print(">> CivicAI Bangladesh - Database Backup Snapshot")
    print(f"Timestamp: {timestamp}")
    print("=" * 60)

    if DATABASE_URL.startswith("sqlite"):
        # Resolve SQLite file path
        rel_path = DATABASE_URL.replace("sqlite:///", "").replace("./", "")
        db_file = os.path.join(base_dir, rel_path)

        if not os.path.exists(db_file):
            print(f"[FAIL] SQLite database file not found at: {db_file}")
            return False

        backup_file = os.path.join(backups_dir, f"civicai_sqlite_backup_{timestamp}.db")
        shutil.copy2(db_file, backup_file)
        size_kb = os.path.getsize(backup_file) / 1024
        print(f"[SUCCESS] SQLite snapshot created successfully!")
        print(f"File: {backup_file}")
        print(f"Size: {size_kb:.2f} KB")
        return True

    elif "postgresql" in DATABASE_URL or "postgres" in DATABASE_URL:
        # PostgreSQL pg_dump backup
        backup_file = os.path.join(backups_dir, f"civicai_postgres_backup_{timestamp}.sql")
        print(f"Running pg_dump for PostgreSQL connection...")
        try:
            cmd = f'pg_dump "{DATABASE_URL}" -f "{backup_file}"'
            res = subprocess.run(cmd, shell=True)
            if res.returncode == 0:
                print(f"[SUCCESS] PostgreSQL dump created at {backup_file}")
                return True
            else:
                print(f"[WARN] pg_dump CLI utility not present in path. You can take automated cloud snapshots directly in your Neon Console (Storage > Snapshots).")
                return False
        except Exception as e:
            print(f"[ERROR] {e}")
            return False

    return False

if __name__ == "__main__":
    perform_backup()
