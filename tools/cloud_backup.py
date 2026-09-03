# tools/cloud_backup.py
import os
from datetime import datetime
from google.cloud import storage

class CloudBackup:
    def __init__(self, bucket_name, credentials_path="service_account.json"):
        self.client = storage.Client.from_service_account_json(credentials_path)
        self.bucket = self.client.bucket(bucket_name)
        if not self.bucket.exists():
            self.bucket.create()
            print(f"☁️ Created bucket: {bucket_name}")
        print(f"☁️ Cloud Storage ready: {bucket_name}")
    
    def backup_db(self, db_path, db_name="ruby_memory.db"):
        try:
            blob = self.bucket.blob(f"backups/{datetime.now().strftime('%Y%m%d')}/{db_name}")
            blob.upload_from_filename(db_path)
            print(f"✅ Cloud backup uploaded: {blob.name}")
            return True
        except Exception as e:
            print(f"❌ Cloud backup error: {e}")
            return False
    
    def restore_latest(self, db_path, db_name="ruby_memory.db"):
        try:
            blobs = list(self.bucket.list_blobs(prefix="backups/"))
            if not blobs:
                print("⚠️ No Cloud backup found.")
                return False
            # Find the most recent blob for this db_name
            candidates = [b for b in blobs if b.name.endswith(db_name)]
            if not candidates:
                print(f"⚠️ No Cloud backup for {db_name}.")
                return False
            latest = sorted(candidates, key=lambda b: b.time_created, reverse=True)[0]
            latest.download_to_filename(db_path)
            print(f"✅ Cloud restore: {latest.name}")
            return True
        except Exception as e:
            print(f"❌ Cloud restore error: {e}")
            return False
