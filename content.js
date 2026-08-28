// content.js - Runs on target social media sites and extracts visible page content
(function() {
    if (window.__rubyContentScriptLoaded) return;
    window.__rubyContentScriptLoaded = true;

    function extractPageData() {
        try {
            const bodyText = document.body ? document.body.innerText : "";
            const currentUrl = window.location.href;

            // Send the page details back to background.js safely
            if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendMessage) {
                chrome.runtime.sendMessage({
                    action: "streamSocialContent",
                    url: currentUrl,
                    content: bodyText.slice(0, 2000) // Keep payload manageable
                });
            }
        } catch (e) {
            console.error("Ruby Content Extraction Error:", e);
        }
    }

    // Run extraction shortly after page load completes
    window.addEventListener("load", () => {
        setTimeout(extractPageData, 2000);
    });
})(
  
);
