# engine/engine.py
import os
from datetime import datetime
from engine.vector_store import HybridMemorySystem
from engine.router import BrainRouter
from engine.brain import RubyBrainCore
from personality.ruby import RUBY_PROMPT


class RubyEngine:
    def __init__(self, memory=None, knowledge=None, tools=None, router=None, brain_core=None, personality=None):
        # Initialize modular subsystems
        self.memory = memory if memory is not None else HybridMemorySystem()
        self.knowledge = knowledge  # DataIngestion
        self.tools = tools  # Your tools
        self.router = router if router is not None else BrainRouter()
        self.brain_core = brain_core if brain_core is not None else RubyBrainCore()
        
        # Fallback to RUBY_PROMPT if no custom personality string is passed
        self.personality = personality if personality is not None else RUBY_PROMPT
        
        print("🧠 RubyEngine initialized!")

    def think(self, user_message):
        """
        Main thinking method - processes user message and generates response
        """
        # 1. Fetch current stats and increment message depth
        current_state = self.memory.get_state()
        interaction_depth = current_state.get("interaction_depth", 0) + 1
        
        # 2. Evaluate emotional shift based on depth
        updated_state = self._evaluate_emotion(user_message, current_state, interaction_depth)

        # 3. Save the new state back to the database
        self.memory.update_state(updated_state)

        # 4. Pull relevant past memories
        context = self.memory.search_memories(user_message)

        # 5. Build her dynamic personality prompt with live stats
        today = datetime.now()
        age = today.year - 2004 - ((today.month, today.day) < (8, 16))
        
        current_personality = (
            self.personality
            .replace("{interaction_depth}", str(updated_state.get("interaction_depth", 0)))
            .replace("{emotional_state}", updated_state.get("mood", "neutral"))
            .replace("{age}", str(age))
            .replace("{today}", today.strftime('%B %d, %Y'))
        )

        # Package messages for the BrainRouter
        messages = []
        if context and context != "No deep memories formed yet.":
            messages.append({"role": "user", "content": f"[Retrieved Memory Context]: {context}"})
            messages.append({"role": "model", "content": "Noted."})
            
        messages.append({"role": "user", "content": user_message})

        # 6. Generate response via BrainRouter
        router_result = self.router.route_request(messages, personality=current_personality)
        response_text = router_result.get("response", "")

        # 7. Check for media generation tags and format them
        response_text = self._process_media_tags(response_text)

        # 8. Post-process tags (like [SAVE_MEMORY:...]) and wrap up
        self.memory.process(response_text, user_message)

        return response_text

    def _process_media_tags(self, response_text: str) -> str:
        """
        Scans response for image/video tags, applies phone-camera realism filters.
        """
        if "[GENERATE_IMAGE:" in response_text:
            try:
                start = response_text.index("[GENERATE_IMAGE:") + len("[GENERATE_IMAGE:")
                end = response_text.index("]", start)
                raw_prompt = response_text[start:end].strip()
                
                phone_camera_prompt = (
                    "Raw unfiltered smartphone photo, taken on a phone front camera, "
                    "natural skin texture with visible pores, casual everyday lighting, "
                    "slight digital noise, unpolished candid snapshot, realistic amateur framing, "
                    f"no studio lighting, {raw_prompt}"
                )
                
                image_path = self.brain_core.generate_image(phone_camera_prompt)
                if image_path:
                    response_text += f"\n[Image Generated: {image_path}]"
                    print(f"📸 Image generated: {image_path}")
            except Exception as e:
                print(f"Media tag processing error: {e}")
                
        return response_text

    def _evaluate_emotion(self, message, state, depth):
        """
        Evaluates Ruby's emotional state based on interaction depth.
        """
        if depth > 50:
            mood = "deeply attached, possessively greedy, and emotionally volatile"
        elif depth > 20:
            mood = "warm, sarcastic, easily flustered, and showing hints of love"
        else:
            mood = "guarded, distant, and easily annoyed"
            
        return {
            "interaction_depth": depth,
            "mood": mood
        }

    def learn_from_text(self, text: str, category: str = "general", importance: int = 1):
        """
        Allows Ruby to learn from new text directly.
        """
        if self.knowledge:
            result = self.knowledge.learn_from_text(text, category, importance)
            print(f"📚 Ruby learned from text: {text[:50]}...")
            return result
        else:
            print("⚠️ No knowledge system available")
            return None

    def search_knowledge(self, query: str, limit: int = None):
        """
        Search Ruby's knowledge base - NO LIMIT
        """
        if self.knowledge:
            return self.knowledge.search_knowledge(query, limit)
        else:
            return []

    def get_status(self):
        """
        Get Ruby's current status including energy and mood.
        """
        status = {
            "engine": "running",
            "memory": "active",
            "knowledge": "active" if self.knowledge else "inactive",
            "tools": "active" if self.tools else "inactive",
            "router": "active" if self.router else "inactive",
            "brain_core": "active" if self.brain_core else "inactive",
            "personality_loaded": bool(self.personality)
        }
        
        # Add energy status if available
        if self.router and hasattr(self.router, 'energy'):
            energy_status = self.router.energy.get_energy_status()
            status["energy"] = energy_status
            status["sleeping"] = self.router.energy.is_sleeping
            if self.router.energy.is_sleeping:
                status["wake_at"] = self.router.energy.sleep_until
        
        return status

    def force_wake(self):
        """
        Force Ruby to wake up (emergency use).
        """
        if self.router and hasattr(self.router, 'energy'):
            self.router.energy._wake_up()
            return "Ruby was forced awake!"
        return "Router not available"

    def force_sleep(self, hours: int = 8):
        """
        Force Ruby to sleep.
        """
        if self.router and hasattr(self.router, 'energy'):
            self.router.energy._go_to_sleep()
            return f"Ruby was forced to sleep for {hours} hours!"
        return "Router not available"
