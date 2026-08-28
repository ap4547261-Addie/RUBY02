// Connect to Ruby's local WebSocket server
let rubySocket = null;

function connectToRuby() {
    rubySocket = new WebSocket("ws://localhost:8765");

    rubySocket.onopen = () => {
        console.log("Connected to Ruby's background engine.");
    };

    rubySocket.onclose = () => {
        console.log("Disconnected from Ruby. Reconnecting in 3 seconds...");
        setTimeout(connectToRuby, 3000);
    };

    rubySocket.onerror = (error) => {
        console.error("Ruby WebSocket error:", error);
    };
}

connectToRuby();

// Listen for messages from your extension popup or content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "autoSearch") {
        const query = request.query;
        const searchUrl = `https://duckduckgo.com/?q=${encodeURIComponent(query)}`;
        
        chrome.tabs.create({ url: searchUrl, active: false }, (tab) => {
            const tabId = tab.id;
            
            chrome.tabs.onUpdated.addListener(function listener(updatedTabId, changeInfo) {
                if (updatedTabId === tabId && changeInfo.status === 'complete') {
                    chrome.tabs.onUpdated.removeListener(listener);
                    
                    chrome.scripting.executeScript({
                        target: { tabId: tabId },
                        func: () => document.body.innerText
                    }, (results) => {
                        const pageText = results && results[0] ? results[0].result : "";
                        chrome.tabs.remove(tabId);
                        
                        const snippet = pageText.slice(0, 1500);

                        // If Ruby's WebSocket is open, stream the scraped data straight to her!
                        if (rubySocket && rubySocket.readyState === WebSocket.OPEN) {
                            rubySocket.send(JSON.stringify({
                                platform: searchUrl,
                                content: snippet
                            }));
                        }
                        
                        sendResponse({ success: true, text: snippet });
                    });
                }
            });
        });
        return true; 
   
    }
});
