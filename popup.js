document.getElementById('send-btn').addEventListener('click', async () => {
    const inputField = document.getElementById('user-input');
    const text = inputField.value.trim();
    if (!text) return;

    const chatContainer = document.getElementById('chat-container');
    chatContainer.innerHTML += `<div style="color: #ffca28; margin-top: 6px;">Addie: ${text}</div>`;
    inputField.value = '';
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Ask Ruby's background engine to perform an autonomous search
    chrome.runtime.sendMessage({ action: "rubySearch", query: text }, (response) => {
        const searchResult = (response && response.success) ? response.text : "Couldn't fetch data.";
        
        chatContainer.innerHTML += `<div style="color: #00bcd4; margin-top: 6px;">Ruby: I searched it myself. Let's see what we got...</div>`;
        chatContainer.scrollTop = chatContainer.scrollHeight;
        console.log("Autonomous Search Data:", searchResult);
    });
})
  ;
