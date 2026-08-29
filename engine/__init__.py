import os
from datetime import datetime

class RubyEngine:

    def __init__(self, memory=None, knowledge=None, tools=None, router=None, brain_core=None, personality=None):
        # Initialize modular subsystems, falling back to default instances if none are provided
        self.memory = memory if memory is not None else HybridMemorySystem()
        self.knowledge = knowledge if knowledge is not None else KnowledgeEngine()
        self.tools = tools if tools is not None else ToolEngine()
        self.router = router if router is not None else BrainRouter()
        self.brain_core = brain_core if brain_core is not None else RubyBrainCore()
        
        # Fallback to RUBY_PROMPT if no custom personality string is passed
        self.personality = personality if personality is not None else RUBY_PROMPT

    def think(self, user_message):
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

        # 7. Post-process tags (like [SAVE_MEMORY:...]) and wrap up
        self.memory.process(response_text, user_message)

        return response_text

    def _evaluate_emotion(self, message, state, depth):
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
