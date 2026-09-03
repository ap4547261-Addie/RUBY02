# tools/gmail_backup.py
import os
import base64
import pickle
import email
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class GmailBackup:
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    
    def __init__(self, creds_file="credentials.json", token_file="token_gmail.pickle"):
        self.creds_file = creds_file
        self.token_file = token_file
        self.creds = self._authenticate()
        self.service = build('gmail', 'v1', credentials=self.creds)
        self.label_name = "Ruby_Backup"
        self._ensure_label()
    
    def _authenticate(self):
        creds = None
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as f:
                creds = pickle.load(f)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.creds_file, self.SCOPES)
                creds = flow.run_local_server(port=8080)
            with open(self.token_file, 'wb') as f:
                pickle.dump(creds, f)
        return creds
    
    def _ensure_label(self):
        try:
            labels = self.service.users().labels().list(userId='me').execute()
            if not any(l['name'] == self.label_name for l in labels.get('labels', [])):
                label = {'name': self.label_name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}
                self.service.users().labels().create(userId='me', body=label).execute()
                print("📂 Gmail label 'Ruby_Backup' created.")
        except Exception as e:
            print(f"⚠️ Gmail label error: {e}")
    
    def backup_db(self, db_path, db_name="ruby_memory.db"):
        try:
            with open(db_path, 'rb') as f:
                file_data = f.read()
            
            msg = MIMEMultipart()
            msg['To'] = 'me'
            msg['Subject'] = f"Ruby Backup - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(file_data)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{db_name}"')
            msg.attach(part)
            
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
            body = {'raw': raw}
            sent = self.service.users().messages().send(userId='me', body=body).execute()
            print(f"✅ Gmail backup sent: {sent['id']}")
            return True
        except Exception as e:
            print(f"❌ Gmail backup error: {e}")
            return False
    
    def restore_db(self, db_path, db_name="ruby_memory.db"):
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='subject:"Ruby Backup"',
                maxResults=1
            ).execute()
            msgs = results.get('messages', [])
            if not msgs:
                print("⚠️ No Gmail backup found.")
                return False
            
            msg_id = msgs[0]['id']
            msg = self.service.users().messages().get(userId='me', id=msg_id).execute()
            
            for part in msg['payload'].get('parts', []):
                if part['filename'] == db_name:
                    att_id = part['body']['attachmentId']
                    att = self.service.users().messages().attachments().get(
                        userId='me', messageId=msg_id, id=att_id
                    ).execute()
                    data = base64.urlsafe_b64decode(att['data'])
                    with open(db_path, 'wb') as f:
                        f.write(data)
                    print(f"✅ Gmail restore: {db_name}")
                    return True
            return False
        except Exception as e:
            print(f"❌ Gmail restore error: {e}")
            return False
