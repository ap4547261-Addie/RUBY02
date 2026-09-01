// popup.js - Complete with WebSocket integration and real-time learning feedback

document.addEventListener("DOMContentLoaded", () => {
    const chatContainer = document.getElementById('chat-container');
    const inputField = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const learningText = document.getElementById('learningText');
    const statsLearned = document.getElementById('statsLearned');
    const statsMemory = document.getElementById('statsMemory');
    const statsQueue = document.getElementById('statsQueue');
    
    let messageCount = 0;
    let isConnected = false;
    
    // --- Message Functions ---
    function addMessage(sender, text, isUser = false) {
        const msgDiv = document.createElement('div');
        msgDiv.style.margin = '6px 0';
        msgDiv.style.padding = '8px 12px';
        msgDiv.style.borderRadius = '8px';
        msgDiv.style.maxWidth = '90%';
        msgDiv.style.wordWrap = 'break-word';
        msgDiv.style.animation = 'fadeIn 0.3s ease';
        
        if (isUser) {
            msgDiv.style.background = '#1a1a3e';
            msgDiv.style.marginLeft = 'auto';
            msgDiv.style.border = '1px solid #2a2a5e';
            msgDiv.style.color = '#ffeb3b';
        } else {
            msgDiv.style.background = '#1a2a2a';
            msgDiv.style.border = '1px solid #1a3a3a';
            msgDiv.style.color = '#00bcd4';
        }
        
        msgDiv.innerHTML = `<strong>${sender}:</strong> ${text}`;
        chatContainer.appendChild(msgDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        messageCount++;
    }
    
    function addSystemMessage(text, type = 'info') {
        const msgDiv = document.createElement('div');
        msgDiv.style.margin = '4px 0';
        msgDiv.style.padding = '4px 12px';
        msgDiv.style.fontSize = '11px';
        msgDiv.style.color = type === 'error' ? '#ff6b6b' : '#666';
        msgDiv.style.textAlign = 'center';
        msgDiv.style.border = '1px dashed #2a2a2a';
        msgDiv.style.borderRadius = '4px';
        msgDiv.textContent = text;
        chatContainer.appendChild(msgDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // --- Status Updates ---
    function updateStatus(connected, queueLength = 0) {
        isConnected = connected;
        
        if (connected) {
            statusDot.className = 'status-dot connected';
            statusText.textContent = 'Connected';
            learningText.textContent = '📡 Connected to Ruby';
        } else {
            statusDot.className = 'status-dot disconnected';
            statusText.textContent = 'Disconnected';
            learningText.textContent = '❌ Ruby not connected';
        }
        
        statsQueue.textContent = queueLength;
    }
    
    function updateStats(learned = 0, memory = 0) {
        statsLearned.textContent = learned;
        statsMemory.textContent = memory;
    }
    
    // --- Send to Ruby ---
    function sendToRuby(platform, content) {
        return new Promise((resolve) => {
            chrome.runtime.sendMessage({
                action: "learnFromPage",
                data: {
                    platform: platform,
                    content: content
                }
            }, (response) => {
                if (chrome.runtime.lastError) {
                    resolve({ success: false, error: chrome.runtime.lastError });
                    return;
                }
                resolve(response || { success: false });
            });
        });
    }
    
    // --- Main Send Handler ---
    async function handleSend() {
        const text = inputField.value.trim();
        if (!text) return;
        
        // Add user message
        addMessage('Addie', text, true);
        inputField.value = '';
        
        // Show learning status
        learningText.textContent = '🧠 Ruby is thinking...';
        
        try {
            // Send to Ruby's background for autonomous search
            chrome.runtime.sendMessage({ 
                action: "rubySearch", 
                query: text 
            }, async (response) => {
                if (chrome.runtime.lastError) {
                    addSystemMessage('❌ Error: ' + chrome.runtime.lastError.message, 'error');
                    learningText.textContent = '❌ Error occurred';
                    return;
                }
                
                if (response && response.success) {
                    // Ruby found results
                    addMessage('Ruby', `🔍 I searched and found information about "${text}"!`);
                    addSystemMessage(`📊 Found ${response.text?.length || 0} characters of data`);
                    
                    // Send the search results to Ruby's learning system
                    if (response.text) {
                        const result = await sendToRuby('search', 
                            `Search results for "${text}":\n${response.text.slice(0, 2000)}`
                        );
                        
                        if (result.success) {
                            addSystemMessage('✅ Ruby learned from the search results!');
                            learningText.textContent = `✅ Learned about "${text}"`;
                            
                            // Update stats
                            chrome.runtime.sendMessage({ action: "getStatus" }, (status) => {
                                if (status) {
                                    updateStats(status.learned_count, status.memory_count);
                                }
                            });
                        } else {
                            addSystemMessage('⚠️ Could not send to Ruby\'s learning system');
                        }
                    }
                } else {
                    // No results found
                    addMessage('Ruby', `🤔 I couldn't find much about "${text}". Can you be more specific?`);
                    learningText.textContent = '❓ No results found';
                }
                
                // Reset learning text after delay
                setTimeout(() => {
                    learningText.textContent = isConnected ? '📡 Connected to Ruby' : '❌ Ruby not connected';
                }, 3000);
            });
        } catch (error) {
            console.error('Error in handleSend:', error);
            addSystemMessage('❌ Error: ' + error.message, 'error');
            learningText.textContent = '❌ Error occurred';
        }
    }
    
    // --- Quick Actions ---
    function handleLearnPage() {
        chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
            const activeTab = tabs[0];
            if (!activeTab) {
                addSystemMessage('❌ No active tab found', 'error');
                return;
            }
            
            addSystemMessage(`📄 Learning from: ${activeTab.title || activeTab.url}`);
            learningText.textContent = '📄 Reading page...';
            
            try {
                chrome.runtime.sendMessage({ action: "learnPage" }, async (response) => {
                    if (response && response.success) {
                        addSystemMessage('✅ Learned from current page!');
                        learningText.textContent = '📄 Page learned!';
                        
                        // Update stats
                        chrome.runtime.sendMessage({ action: "getStatus" }, (status) => {
                            if (status) {
                                updateStats(status.learned_count, status.memory_count);
                            }
                        });
                    } else {
                        addSystemMessage('❌ Failed to learn page', 'error');
                    }
                    
                    setTimeout(() => {
                        learningText.textContent = isConnected ? '📡 Connected to Ruby' : '❌ Ruby not connected';
                    }, 2000);
                });
            } catch (error) {
                addSystemMessage('❌ Error: ' + error.message, 'error');
            }
        });
    }
    
    function handleStatus() {
        chrome.runtime.sendMessage({ action: "getStatus" }, (response) => {
            if (response) {
                addSystemMessage(`📊 Status: ${response.connected ? '🟢 Connected' : '🔴 Disconnected'}`);
                addSystemMessage(`📨 Queue: ${response.queue_length || 0} messages`);
                addSystemMessage(`📚 Learned: ${response.learned_count || 0} items`);
                addSystemMessage(`💾 Memory: ${response.memory_count || 0} items`);
                addSystemMessage(`🔌 Server: ${response.server || 'ws://localhost:8765'}`);
                updateStatus(response.connected, response.queue_length || 0);
                updateStats(response.learned_count, response.memory_count);
            } else {
                addSystemMessage('❌ Could not get status', 'error');
            }
        });
    }
    
    function handleClear() {
        chatContainer.innerHTML = '';
        messageCount = 0;
        // Restore empty state
        const emptyDiv = document.createElement('div');
        emptyDiv.style.textAlign = 'center';
        emptyDiv.style.padding = '40px 20px';
        emptyDiv.style.color = '#444';
        emptyDiv.innerHTML = `
            <div style="font-size: 40px; margin-bottom: 12px;">💬</div>
            <h3 style="color: #666; font-weight: 400; font-size: 14px;">Chat with Ruby</h3>
            <p style="font-size: 12px; color: #333; margin-top: 4px;">Ask questions or send content to learn</p>
        `;
        chatContainer.appendChild(emptyDiv);
        addSystemMessage('🗑️ Chat cleared');
    }
    
    // --- Event Listeners ---
    sendBtn.addEventListener('click', handleSend);
    inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleSend();
        }
    });
    
    // --- Quick Action Buttons ---
    document.querySelectorAll('.quick-actions button').forEach(btn => {
        btn.addEventListener('click', () => {
            const action = btn.dataset.action;
            switch(action) {
                case 'learnPage': handleLearnPage(); break;
                case 'search': inputField.focus(); break;
                case 'status': handleStatus(); break;
                case 'clear': handleClear(); break;
                default: break;
            }
        });
    });
    
    // --- Listen for status updates from background ---
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.type === "ruby_connected") {
            updateStatus(request.status);
            if (request.status) {
                addSystemMessage('✅ Ruby is connected!');
                learningText.textContent = '📡 Connected to Ruby';
            } else {
                addSystemMessage('❌ Ruby disconnected. Reconnecting...');
                learningText.textContent = '🔄 Reconnecting...';
            }
        }
        return true;
    });
    
    // --- Initial Status Check ---
    chrome.runtime.sendMessage({ action: "getStatus" }, (response) => {
        if (response) {
            updateStatus(response.connected, response.queue_length || 0);
            updateStats(response.learned_count, response.memory_count);
            if (response.connected) {
                addSystemMessage('✅ Connected to Ruby\'s brain!');
            } else {
                addSystemMessage('⏳ Connecting to Ruby...');
                learningText.textContent = '🔄 Connecting to Ruby...';
            }
        }
    });
    
    // --- Auto-focus input ---
    inputField.focus();
    
    console.log('💬 Ruby Bridge popup ready');
    console.log('📡 Send messages to Ruby by typing and pressing Enter');
});
