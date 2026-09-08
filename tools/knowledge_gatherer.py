# tools/knowledge_gatherer.py
import random
import time
import threading
from datetime import datetime

class KnowledgeGatherer:
    def __init__(self, video_learner, web_learner, memory, knowledge, interval=3600):
        """
        interval: seconds between learning sessions.
        Set to 0 to run continuously (not recommended, may overload).
        """
        self.video_learner = video_learner
        self.web_learner = web_learner
        self.memory = memory
        self.knowledge = knowledge
        self.interval = interval
        self.running = False
        self.thread = None

        # You can add any topics here – this list is not limited
        self.topics = [
            "artificial intelligence", "space exploration", "history",
            "science", "philosophy", "psychology", "technology",
            "nature", "art", "music", "literature", "cooking",
            "fashion", "travel", "culture", "politics", "economics"
        ]

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"🧠 KnowledgeGatherer started (learning every {self.interval} seconds)")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

    def _run(self):
        while self.running:
            try:
                self._learn_one_topic()
            except Exception as e:
                print(f"KnowledgeGatherer error: {e}")
            if self.interval > 0:
                time.sleep(self.interval)
            else:
                # If interval is 0, learn non-stop (use with caution)
                time.sleep(1)  # small delay to avoid hammering

    def _learn_one_topic(self):
        topic = random.choice(self.topics)
        print(f"📖 Ruby is learning about: {topic}")

        # Try YouTube first
        try:
            result = self.video_learner.search_and_learn(topic)
            if result and result.get("success"):
                print(f"✅ Ruby learned from YouTube about '{topic}'")
                self.memory.save_hybrid_memory(
                    f"Ruby learned about {topic} from YouTube.",
                    importance=2,
                    category="self_learned"
                )
                return
        except Exception as e:
            print(f"YouTube learning failed: {e}")

        # If YouTube fails, try web search
        try:
            result = self.web_learner.search_web_and_learn(topic)
            if result and result.get("success"):
                print(f"✅ Ruby learned from the web about '{topic}'")
                self.memory.save_hybrid_memory(
                    f"Ruby learned about {topic} from the web.",
                    importance=2,
                    category="self_learned"
                )
                return
        except Exception as e:
            print(f"Web learning failed: {e}")

        print(f"❌ Ruby couldn't learn about '{topic}' this time.")
