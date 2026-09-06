# tools/profile.py
import sqlite3
import re
from datetime import datetime

class ConversationProfile:
    """
    Tracks conversation patterns per user:
    - average message length
    - emoji usage frequency
    - question frequency
    - Ruby's own average response length and emoji usage
    """
    def __init__(self, db_path="ruby_memory.db"):
        self.db_path = db_path
        self._init_table()

    def _init_table(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_profile (
                user_id TEXT PRIMARY KEY,
                total_turns INTEGER DEFAULT 0,
                user_msg_length_sum INTEGER DEFAULT 0,
                user_msg_count INTEGER DEFAULT 0,
                user_emoji_count INTEGER DEFAULT 0,
                user_question_count INTEGER DEFAULT 0,
                ruby_msg_length_sum INTEGER DEFAULT 0,
                ruby_msg_count INTEGER DEFAULT 0,
                ruby_emoji_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def _count_emojis(self, text):
        # Simple emoji regex (covers most common emojis)
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        return len(emoji_pattern.findall(text))

    def update(self, user_id, user_msg, ruby_msg):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Fetch existing
        c.execute('SELECT * FROM user_profile WHERE user_id=?', (user_id,))
        row = c.fetchone()
        if row:
            (_, total, user_len_sum, user_count, user_emoji, user_ques,
             ruby_len_sum, ruby_count, ruby_emoji, _) = row
        else:
            total = user_len_sum = user_count = user_emoji = user_ques = 0
            ruby_len_sum = ruby_count = ruby_emoji = 0

        # Update user stats
        total += 1
        user_count += 1
        user_len_sum += len(user_msg.split())
        user_emoji += self._count_emojis(user_msg)
        if '?' in user_msg:
            user_ques += 1

        # Update Ruby stats
        ruby_count += 1
        ruby_len_sum += len(ruby_msg.split())
        ruby_emoji += self._count_emojis(ruby_msg)

        # Insert/update
        c.execute('''
            INSERT OR REPLACE INTO user_profile (
                user_id, total_turns, user_msg_length_sum, user_msg_count,
                user_emoji_count, user_question_count, ruby_msg_length_sum,
                ruby_msg_count, ruby_emoji_count, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, total, user_len_sum, user_count, user_emoji, user_ques,
              ruby_len_sum, ruby_count, ruby_emoji, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_stats(self, user_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM user_profile WHERE user_id=?', (user_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        (_, total, user_len_sum, user_count, user_emoji, user_ques,
         ruby_len_sum, ruby_count, ruby_emoji, _) = row
        stats = {
            'total_turns': total,
            'user_avg_length': user_len_sum / user_count if user_count else 0,
            'user_emoji_ratio': user_emoji / user_count if user_count else 0,
            'user_question_ratio': user_ques / user_count if user_count else 0,
            'ruby_avg_length': ruby_len_sum / ruby_count if ruby_count else 0,
            'ruby_emoji_ratio': ruby_emoji / ruby_count if ruby_count else 0,
        }
        return stats

    def build_style_instruction(self, stats):
        if not stats:
            return ""
        instr = "Based on our conversation history, please adapt to this style:\n"
        if stats['user_avg_length'] < 10:
            instr += "- The user prefers short, concise messages (average ~{} words).\n".format(int(stats['user_avg_length']))
        else:
            instr += "- The user writes longer, more detailed messages (average ~{} words).\n".format(int(stats['user_avg_length']))
        if stats['user_emoji_ratio'] > 0.3:
            instr += "- The user frequently uses emojis – respond with emojis naturally.\n"
        else:
            instr += "- The user rarely uses emojis – keep emojis minimal.\n"
        if stats['user_question_ratio'] > 0.3:
            instr += "- The user asks many questions – be curious and ask questions back.\n"
        else:
            instr += "- The user mostly makes statements – respond with thoughtful comments.\n"
        # Adapt to Ruby's own learned style
        if stats['ruby_emoji_ratio'] > 0.2:
            instr += "- You've used emojis in the past; continue naturally.\n"
        if stats['ruby_avg_length'] > 0:
            instr += "- Your typical response length is about {} words – stay consistent.\n".format(int(stats['ruby_avg_length']))
        return instr
