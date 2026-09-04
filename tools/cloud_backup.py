# tools/cloud_backup.py
import os
from datetime import datetime

# Try to import Google Cloud Storage – if it fails, disable it gracefully
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    storage = None
    GCS_AVAILABLE = False
    print("⚠️ Google Cloud Storage not available – Cloud backup disabled.")

class CloudBackup:
    def __init__(self, bucket_name, credentials_path):
        self.bucket_name = bucket_name
        self.credentials_path = credentials_path
        self.client = None
        if GCS_AVAILABLE:
            try:
                self.client = storage.Client.from_service_account_json(credentials_path)
                print("☁️ Cloud Storage client initialized.")
            except Exception as e:
                print(f"⚠️ Cloud Storage client error: {e}")
                self.client = None
        else:
            print("ℹ️ Cloud backup disabled (no google-cloud-storage).")
    
    def backup_db(self, db_path, db_name):
        if not self.client:
            print("⚠️ Cloud backup not available – skipping.")
            return False
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(db_name)
            blob.upload_from_filename(db_path)
            print(f"✅ Cloud backup uploaded: {db_name}")
            return True
        except Exception as e:
            print(f"❌ Cloud backup error: {e}")
            return False
    
    def restore_latest(self, db_path, db_name):
        if not self.client:
            print("⚠️ Cloud backup not available – skipping restore.")
            return False
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(db_name)
            if not blob.exists():
                print(f"⚠️ No cloud backup found for {db_name}.")
                return False
            blob.download_to_filename(db_path)
            print(f"✅ Cloud backup restored: {db_name}")
            return True
        except Exception as e:
            print(f"❌ Cloud restore error: {e}")
            return False
