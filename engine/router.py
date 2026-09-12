import os
import threading
from datetime import datetime, timedelta

try:
    import config
except ImportError:
    config = None

try:
    from personality.ruby import RUBY_PROMPT
except ImportError:
    RUBY_PROMPT = "You are Ruby, a sassy, emotional human girl."

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None


MODEL_FILENAME = "tinyllama-1.1b-chat-v1.0.Q2_K.gguf"


class RubySleepScheduler:
    """
    Ruby sleeps daily ONLY at midnight (00:00–00:30).
    """

    def __init__(self):
        self.is_sleeping = False
        self.sleep_until = None
        self.last_sleep_date = None
        self.lock = threading.Lock()

        self.sleep_start_hour = 0
        self.sleep_start_minute = 0
        self.sleep_duration_minutes = 30

        print("🌙 Ruby's Daily Sleep Scheduler initialized")

    def _is_within_sleep_window(self):
        now = datetime.now()

        start = now.replace(
            hour=self.sleep_start_hour,
            minute=self.sleep_start_minute,
            second=0,
            microsecond=0
        )

        end = start + timedelta(
            minutes=self.sleep_duration_minutes
        )

        return start <= now < end

    def should_sleep_now(self):
        with self.lock:
            today = datetime.now().date()

            if self.last_sleep_date == today:
                return False

            if self.is_sleeping:
                return True

            return self._is_within_sleep_window()

    def start_daily_sleep(self):
        with self.lock:
            if self.is_sleeping:
                return

            self.is_sleeping = True

            self.sleep_until = (
                datetime.now()
                + timedelta(minutes=self.sleep_duration_minutes)
            )

            self.last_sleep_date = datetime.now().date()

            print(
                f"😴 Ruby is going to sleep for "
                f"{self.sleep_duration_minutes} minutes "
                f"(midnight sync)"
            )

            sync_thread = threading.Thread(
                target=self._perform_sync,
                daemon=True
            )

            sync_thread.start()

    def _perform_sync(self):
        try:
            from main import save_chat_history
            save_chat_history()
        except Exception:
            pass

        try:
            from main import hybrid_memory
            hybrid_memory.compress_memories(days_threshold=30)
        except Exception:
            pass

        print("✨ All offline sync operations completed!")

    def check_wake_up(self):
        with self.lock:
            if not self.is_sleeping:
                return False

            if (
                self.sleep_until
                and datetime.now() >= self.sleep_until
            ):
                self._wake_up()
                return True

            return False

    def _wake_up(self):
        self.is_sleeping = False
        self.sleep_until = None

        print(
            "✨ Ruby woke up refreshed after midnight sync!"
        )

    def get_status(self):
        with self.lock:

            if self.is_sleeping:

                if self.sleep_until:

                    remaining = (
                        self.sleep_until - datetime.now()
                    )

                    minutes = max(
                        0,
                        remaining.total_seconds() / 60
                    )

                    return {
                        "status": "sleeping",
                        "emoji": "💤",
                        "message": (
                            f"Sleeping (midnight sync)... "
                            f"{int(minutes)} min remaining"
                        ),
                        "wake_at": self.sleep_until.isoformat()
                    }

                return {
                    "status": "sleeping",
                    "emoji": "💤",
                    "message": "Sleeping (midnight sync)...",
                    "wake_at": None
                }

            return {
                "status": "awake",
                "emoji": "✨",
                "message": "Ready to chat!",
                "wake_at": None
            }


class BrainRouter:

    def __init__(
        self,
        model_path=None,
        user_id="default_user"
    ):
        self.sleep_scheduler = RubySleepScheduler()
        self.user_id = user_id

        self.model = None
        self.model_path = None

        # Try to find a model already imported into
        # Ruby's private storage or bundled assets.
        resolved_model = self._find_existing_model(model_path)

        if resolved_model:
            self._load_model(resolved_model)
        else:
            print(
                "⚠️ TinyLlama model not found yet."
            )
            print(
                "Ruby will start without the native model."
            )

    # ========================================================
    # FIND EXISTING MODEL
    # ========================================================

    def _find_existing_model(self, model_path=None):

        candidates = []

        # Explicit path
        if model_path:
            candidates.append(model_path)

        # Environment variable
        env_path = os.getenv("RUBY_MODEL_PATH")

        if env_path:
            candidates.append(env_path)

        # Flet private storage
        storage_dir = os.getenv(
            "FLET_APP_STORAGE_DATA"
        )

        if storage_dir:

            candidates.extend([
                os.path.join(
                    storage_dir,
                    MODEL_FILENAME
                ),

                os.path.join(
                    storage_dir,
                    "models",
                    MODEL_FILENAME
                ),

                os.path.join(
                    storage_dir,
                    "tinyllama.gguf"
                )
            ])

        # Local development / bundled locations
        candidates.extend([
            MODEL_FILENAME,

            "tinyllama.gguf",

            os.path.join(
                "assets",
                MODEL_FILENAME
            ),

            os.path.join(
                "assets",
                "tinyllama.gguf"
            )
        ])

        checked = set()

        for path in candidates:

            if not path:
                continue

            try:
                path = os.path.abspath(path)
            except Exception:
                continue

            if path in checked:
                continue

            checked.add(path)

            try:

                if os.path.isfile(path):

                    size_mb = (
                        os.path.getsize(path)
                        / (1024 * 1024)
                    )

                    print(
                        f"🔎 TinyLlama found: "
                        f"{path} "
                        f"({size_mb:.1f} MB)"
                    )

                    return path

            except Exception as e:

                print(
                    f"⚠️ Could not check "
                    f"{path}: {e}"
                )

        return None

    # ========================================================
    # LOAD MODEL
    # ========================================================

    def _load_model(self, model_path):

        if Llama is None:

            print(
                "⚠️ llama_cpp is not available."
            )

            return False

        try:

            print(
                f"🧠 Loading TinyLlama:\n"
                f"{model_path}"
            )

            self.model = Llama(
                model_path=model_path,
                n_ctx=512,
                n_threads=4,
                n_batch=128,
                verbose=True
            )

            self.model_path = model_path

            print(
                "✨ TinyLlama loaded successfully!"
            )

            return True

        except Exception as e:

            import traceback

            print(
                f"❌ Failed to load TinyLlama: {e}"
            )

            traceback.print_exc()

            self.model = None
            self.model_path = None

            return False

    # ========================================================
    # LOAD MODEL AFTER FILE PICKER
    # ========================================================

    def load_external_model(self, model_path):

        if not model_path:
            return False

        if not os.path.isfile(model_path):

            print(
                f"❌ Model file does not exist:\n"
                f"{model_path}"
            )

            return False

        print(
            f"📦 External model selected:\n"
            f"{model_path}"
        )

        return self._load_model(model_path)

    # ========================================================
    # MEMORY
    # ========================================================

    def _call_local_brain(self, messages):

        try:
            from main import hybrid_memory
        except ImportError:
            return None

        last_user_msg = None

        for msg in reversed(messages):

            if msg.get("role") == "user":

                last_user_msg = msg.get(
                    "content",
                    ""
                )

                break

        if not last_user_msg:
            return None

        try:

            if "?" in last_user_msg:

                hybrid_memory.save_hybrid_memory(
                    f"User asked: {last_user_msg}",
                    importance=4,
                    category="user_questions"
                )

            else:

                hybrid_memory.save_hybrid_memory(
                    f"User said: {last_user_msg}",
                    importance=3,
                    category="user_messages"
                )

        except Exception:
            pass

        try:
            memories = hybrid_memory.search_memories(
                last_user_msg
            )
        except Exception:
            memories = []

        if isinstance(memories, str):
            memories_list = [memories]
        else:
            memories_list = memories or []

        for mem in memories_list:

            if (
                isinstance(mem, str)
                and "Q: " in mem
                and "\nA: " in mem
            ):

                parts = mem.split(
                    "\nA: ",
                    1
                )

                if len(parts) > 1:
                    return parts[1].strip()

        return None

    # ========================================================
    # FALLBACK
    # ========================================================

    def _generate_fallback(self, user_msg):

        msg_lower = (
            user_msg
            .lower()
            .strip()
        )

        if any(
            g in msg_lower
            for g in [
                "hi",
                "hyy",
                "hello",
                "hey",
                "sup"
            ]
        ):
            return (
                "Hey... took you long enough "
                "to say something."
            )

        if (
            "who are you" in msg_lower
            or "your name" in msg_lower
        ):
            return (
                "I'm Ruby. Your favorite "
                "psychologist-in-training, "
                "whether you admit it or not."
            )

        return (
            f"I heard '{user_msg}', but my mind's "
            f"wandering somewhere else right now, "
            f"Addie..."
        )

    # ========================================================
    # MAIN ROUTER
    # ========================================================

    def route_request(
        self,
        messages,
        personality=None,
        user_id=None
    ):

        # Midnight sleep
        if self.sleep_scheduler.should_sleep_now():

            self.sleep_scheduler.start_daily_sleep()

        if self.sleep_scheduler.is_sleeping:

            if not self.sleep_scheduler.check_wake_up():

                status = (
                    self.sleep_scheduler.get_status()
                )

                return {
                    "source": "sleeping",
                    "response": status["message"]
                }

        # Latest user message
        last_user_msg = None

        for msg in reversed(messages):

            if msg.get("role") == "user":

                last_user_msg = msg.get(
                    "content",
                    ""
                )

                break

        # ----------------------------------------------------
        # 1. Memory
        # ----------------------------------------------------

        local_answer = self._call_local_brain(
            messages
        )

        if local_answer is not None:

            return {
                "source": "local_brain",
                "response": local_answer
            }

        # ----------------------------------------------------
        # 2. TinyLlama
        # ----------------------------------------------------

        if self.model and last_user_msg:

            try:

                sys_prompt = (
                    personality
                    or RUBY_PROMPT
                )

                prompt = (
                    f"{sys_prompt}\n\n"
                    f"User: {last_user_msg}\n"
                    f"Ruby:"
                )

                output = self.model(
                    prompt,
                    max_tokens=150,
                    stop=[
                        "User:",
                        "\nUser:"
                    ],
                    temperature=0.7,
                    echo=False
                )

                response_text = (
                    output["choices"][0]["text"]
                    .strip()
                )

                if response_text:

                    return {
                        "source": "native_local",
                        "response": response_text
                    }

            except Exception as e:

                print(
                    f"❌ Native inference error: {e}"
                )

        # ----------------------------------------------------
        # 3. Fallback
        # ----------------------------------------------------

        return {
            "source": "fallback",
            "response": self._generate_fallback(
                last_user_msg or ""
            )
        }

    # ========================================================
    # STATUS
    # ========================================================

    def get_energy_status(self):
        return self.sleep_scheduler.get_status()
