// background.js - Chrome Extension Service Worker
// Listens to content.js messages and relays to Ruby's WebSocket server

const RUBY_SERVER = 'ws://localhost:8765';

let ws = null;
let isConnected = false;
let messageQueue = [];
let learnedCount = 0;
let memoryCount = 0;

// ============================================
// WebSocket Connection
// ============================================
function connectToRuby() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        return; // Already connected
    }

    try {
        ws = new WebSocket(RUBY_SERVER);

        ws.onopen = () => {
            console.log('✅ Connected to Ruby server');
            isConnected = true;
            
            // Send any queued messages
            while (messageQueue.length > 0) {
                const msg = messageQueue.shift();
                ws.send(JSON.stringify(msg));
                console.log('📤 Sent queued message:', msg.platform);
            }

            // Notify all tabs
            notifyTabs({ type: 'ruby_connected', status: true });
        };

        ws.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            isConnected = false;
            notifyTabs({ type: 'ruby_connected', status: false });
        };

        ws.onclose = () => {
            console.log('🔌 Disconnected from Ruby');
            isConnected = false;
            notifyTabs({ type: 'ruby_connected', status: false });
            
            // Try reconnecting after 5 seconds
            setTimeout(() => connectToRuby(), 5000);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('📨 Ruby responded:', data);
                
                if (data.learned) learnedCount += 1;
                if (data.memory) memoryCount += 1;
            } catch (e) {
                console.log('Ruby message:', event.data);
            }
        };
    } catch (error) {
        console.error('❌ Connection error:', error);
        isConnected = false;
        setTimeout(() => connectToRuby(), 5000);
    }
}

// ============================================
// Message Handlers
// ============================================
function sendToRuby(message) {
    if (!message.platform || !message.content) {
        console.error('❌ Invalid message format');
        return false;
    }

    const payload = {
        platform: message.platform,
        content: message.content,
        url: message.url || '',
        timestamp: new Date().toISOString()
    };

    if (isConnected && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(payload));
        console.log('📤 Sent to Ruby:', message.platform);
        return true;
    } else {
        // Queue message if not connected
        messageQueue.push(payload);
        console.log('📦 Message queued (Ruby not connected)');
        return false;
    }
}

function notifyTabs(message) {
    chrome.tabs.query({}, (tabs) => {
        tabs.forEach(tab => {
            chrome.tabs.sendMessage(tab.id, message).catch(() => {});
        });
    });
}

// ============================================
// Listen for Messages from Content Script
// ============================================
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('📨 Received message:', request.action);

    if (request.action === 'streamSocialContent') {
        // From content.js - stream page content to Ruby
        const success = sendToRuby({
            platform: request.platform,
            content: request.content,
            url: request.url
        });
        
        sendResponse({ 
            success: success,
            queue_length: messageQueue.length
        });
    }
    
    else if (request.action === 'learnPage') {
        // Learn from the current page
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
                const success = sendToRuby({
                    platform: 'current_page',
                    content: `Learning from: ${tabs[0].title}`,
                    url: tabs[0].url
                });
                sendResponse({ success: success });
            }
        });
    }
    
    else if (request.action === 'learnFromPage') {
        // From popup - send learning data
        const success = sendToRuby({
            platform: request.data.platform,
            content: request.data.content,
            url: request.data.url
        });
        sendResponse({ success: success });
    }
    
    else if (request.action === 'getStatus') {
        // Return current status
        sendResponse({
            connected: isConnected,
            queue_length: messageQueue.length,
            learned_count: learnedCount,
            memory_count: memoryCount,
            server: RUBY_SERVER
        });
    }
    
    else if (request.action === 'rubySearch') {
        // Handle search queries
        const query = request.query || '';
        
        // Queue the search
        const success = sendToRuby({
            platform: 'search',
            content: `Search query: ${query}`,
            url: ''
        });
        
        sendResponse({
            success: success,
            text: `Searching for: ${query}`
        });
    }

    return true;
});

// ============================================
// Initialize
// ============================================
console.log('🚀 Ruby Bridge Background Worker starting...');
connectToRuby();

// Periodically try to reconnect if disconnected
setInterval(() => {
    if (!isConnected) {
        console.log('🔄 Attempting to reconnect to Ruby...');
        connectToRuby();
    }
}, 10000);
