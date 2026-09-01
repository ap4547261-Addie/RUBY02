// content.js - Runs on target social media sites and extracts visible page content
(function() {
    if (window.__rubyContentScriptLoaded) return;
    window.__rubyContentScriptLoaded = true;

    // Platform detection
    function detectPlatform() {
        const url = window.location.href;
        if (url.includes('instagram.com')) return 'instagram';
        if (url.includes('youtube.com') || url.includes('youtu.be')) return 'youtube';
        if (url.includes('reddit.com')) return 'reddit';
        if (url.includes('twitter.com') || url.includes('x.com')) return 'twitter';
        if (url.includes('linkedin.com')) return 'linkedin';
        if (url.includes('facebook.com')) return 'facebook';
        if (url.includes('tiktok.com')) return 'tiktok';
        if (url.includes('pinterest.com')) return 'pinterest';
        return 'unknown';
    }

    // Platform-specific extractors
    const extractors = {
        instagram: function() {
            const data = {
                platform: 'instagram',
                posts: [],
                comments: [],
                profile: null
            };
            
            // Profile info
            const profileName = document.querySelector('h1, [data-testid="profile-name"]');
            const bio = document.querySelector('[data-testid="profile-bio"]');
            if (profileName) {
                data.profile = {
                    name: profileName.textContent,
                    bio: bio ? bio.textContent : ''
                };
            }
            
            // Posts
            document.querySelectorAll('article, [role="article"]').forEach((post, i) => {
                if (i < 5) {
                    const text = post.textContent || '';
                    const images = post.querySelectorAll('img');
                    data.posts.push({
                        text: text.slice(0, 300),
                        images: images.length,
                        index: i
                    });
                }
            });
            
            // Comments
            document.querySelectorAll('[role="comment"], .comment').forEach((comment, i) => {
                if (i < 10) {
                    data.comments.push({
                        text: comment.textContent.slice(0, 200),
                        index: i
                    });
                }
            });
            
            return data;
        },
        
        youtube: function() {
            const data = {
                platform: 'youtube',
                video: null,
                comments: [],
                channel: null
            };
            
            // Video info
            const title = document.querySelector('h1.ytd-video-primary-info-renderer');
            const channel = document.querySelector('#owner-name a');
            const views = document.querySelector('.view-count');
            
            if (title) {
                data.video = {
                    title: title.textContent,
                    channel: channel ? channel.textContent : 'Unknown',
                    views: views ? views.textContent : 'Unknown',
                    url: window.location.href
                };
            }
            
            // Comments
            document.querySelectorAll('#comments #content #content-text').forEach((comment, i) => {
                if (i < 10) {
                    data.comments.push({
                        text: comment.textContent.slice(0, 200),
                        index: i
                    });
                }
            });
            
            return data;
        },
        
        reddit: function() {
            const data = {
                platform: 'reddit',
                posts: [],
                comments: []
            };
            
            // Posts
            document.querySelectorAll('[data-testid="post-container"]').forEach((post, i) => {
                if (i < 5) {
                    const title = post.querySelector('h3');
                    const text = post.querySelector('[data-testid="post-content"]');
                    data.posts.push({
                        title: title ? title.textContent : '',
                        text: text ? text.textContent.slice(0, 300) : '',
                        index: i
                    });
                }
            });
            
            // Comments
            document.querySelectorAll('[data-testid="comment"]').forEach((comment, i) => {
                if (i < 10) {
                    data.comments.push({
                        text: comment.textContent.slice(0, 200),
                        index: i
                    });
                }
            });
            
            return data;
        },
        
        twitter: function() {
            const data = {
                platform: 'twitter',
                tweets: [],
                profile: null
            };
            
            // Profile
            const profileName = document.querySelector('[data-testid="UserName"]');
            if (profileName) {
                data.profile = {
                    name: profileName.textContent
                };
            }
            
            // Tweets
            document.querySelectorAll('[data-testid="tweet"]').forEach((tweet, i) => {
                if (i < 5) {
                    const text = tweet.querySelector('[data-testid="tweetText"]');
                    data.tweets.push({
                        text: text ? text.textContent.slice(0, 300) : '',
                        index: i
                    });
                }
            });
            
            return data;
        },
        
        linkedin: function() {
            const data = {
                platform: 'linkedin',
                posts: [],
                comments: []
            };
            
            // Posts
            document.querySelectorAll('.feed-shared-update-v2').forEach((post, i) => {
                if (i < 5) {
                    const text = post.querySelector('.feed-shared-text');
                    data.posts.push({
                        text: text ? text.textContent.slice(0, 300) : '',
                        index: i
                    });
                }
            });
            
            return data;
        },
        
        facebook: function() {
            const data = {
                platform: 'facebook',
                posts: [],
                comments: []
            };
            
            // Posts
            document.querySelectorAll('[role="article"]').forEach((post, i) => {
                if (i < 5) {
                    const text = post.textContent || '';
                    data.posts.push({
                        text: text.slice(0, 300),
                        index: i
                    });
                }
            });
            
            return data;
        },
        
        tiktok: function() {
            const data = {
                platform: 'tiktok',
                videos: [],
                comments: []
            };
            
            // Videos
            document.querySelectorAll('[data-e2e="video-desc"]').forEach((desc, i) => {
                if (i < 5) {
                    data.videos.push({
                        text: desc.textContent.slice(0, 300),
                        index: i
                    });
                }
            });
            
            // Comments
            document.querySelectorAll('[data-e2e="comment-content"]').forEach((comment, i) => {
                if (i < 10) {
                    data.comments.push({
                        text: comment.textContent.slice(0, 200),
                        index: i
                    });
                }
            });
            
            return data;
        },
        
        pinterest: function() {
            const data = {
                platform: 'pinterest',
                pins: [],
                boards: []
            };
            
            // Pins
            document.querySelectorAll('[data-testid="pin"]').forEach((pin, i) => {
                if (i < 5) {
                    const text = pin.textContent || '';
                    data.pins.push({
                        text: text.slice(0, 300),
                        index: i
                    });
                }
            });
            
            return data;
        },
        
        unknown: function() {
            return {
                platform: 'unknown',
                title: document.title,
                url: window.location.href,
                text: document.body.innerText.slice(0, 2000)
            };
        }
    };

    function extractPageData() {
        try {
            const platform = detectPlatform();
            const extractor = extractors[platform] || extractors.unknown;
            const data = extractor();
            
            // Format for sending
            let content = '';
            switch(data.platform) {
                case 'instagram':
                    content = `📸 Instagram\n`;
                    if (data.profile) {
                        content += `Profile: ${data.profile.name}\n`;
                        content += `Bio: ${data.profile.bio || 'None'}\n`;
                    }
                    content += `\nPosts (${data.posts.length}):\n`;
                    data.posts.forEach(p => content += `- ${p.text}\n`);
                    content += `\nComments (${data.comments.length}):\n`;
                    data.comments.forEach(c => content += `- ${c.text}\n`);
                    break;
                    
                case 'youtube':
                    content = `🎬 YouTube\n`;
                    if (data.video) {
                        content += `Video: ${data.video.title}\n`;
                        content += `Channel: ${data.video.channel}\n`;
                        content += `Views: ${data.video.views}\n`;
                    }
                    content += `\nComments (${data.comments.length}):\n`;
                    data.comments.forEach(c => content += `- ${c.text}\n`);
                    break;
                    
                case 'reddit':
                    content = `📚 Reddit\n`;
                    content += `Posts (${data.posts.length}):\n`;
                    data.posts.forEach(p => content += `- ${p.title}: ${p.text}\n`);
                    content += `\nComments (${data.comments.length}):\n`;
                    data.comments.forEach(c => content += `- ${c.text}\n`);
                    break;
                    
                case 'twitter':
                    content = `🐦 Twitter/X\n`;
                    if (data.profile) {
                        content += `Profile: ${data.profile.name}\n`;
                    }
                    content += `\nTweets (${data.tweets.length}):\n`;
                    data.tweets.forEach(t => content += `- ${t.text}\n`);
                    break;
                    
                case 'linkedin':
                    content = `💼 LinkedIn\n`;
                    content += `Posts (${data.posts.length}):\n`;
                    data.posts.forEach(p => content += `- ${p.text}\n`);
                    break;
                    
                case 'facebook':
                    content = `📘 Facebook\n`;
                    content += `Posts (${data.posts.length}):\n`;
                    data.posts.forEach(p => content += `- ${p.text}\n`);
                    break;
                    
                case 'tiktok':
                    content = `🎵 TikTok\n`;
                    content += `Videos (${data.videos.length}):\n`;
                    data.videos.forEach(v => content += `- ${v.text}\n`);
                    content += `Comments (${data.comments.length}):\n`;
                    data.comments.forEach(c => content += `- ${c.text}\n`);
                    break;
                    
                case 'pinterest':
                    content = `📌 Pinterest\n`;
                    content += `Pins (${data.pins.length}):\n`;
                    data.pins.forEach(p => content += `- ${p.text}\n`);
                    break;
                    
                default:
                    content = `🌐 ${data.title || 'Web Page'}\n`;
                    content += `URL: ${data.url || window.location.href}\n\n`;
                    content += data.text || '';
            }
            
            // Send to background
            if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendMessage) {
                chrome.runtime.sendMessage({
                    action: "streamSocialContent",
                    platform: data.platform,
                    url: window.location.href,
                    content: content.slice(0, 5000)
                }, (response) => {
                    if (chrome.runtime.lastError) {
                        console.log('Background not ready:', chrome.runtime.lastError);
                    }
                });
            }
            
            // Also log for debugging
            console.log(`📤 Ruby learned from ${data.platform}`);
            
        } catch (e) {
            console.error("Ruby Content Extraction Error:", e);
        }
    }

    // Extract on page load
    window.addEventListener("load", () => {
        setTimeout(extractPageData, 2000);
    });

    // Extract on URL change (for SPA navigation)
    let lastUrl = window.location.href;
    const observer = new MutationObserver(() => {
        if (window.location.href !== lastUrl) {
            lastUrl = window.location.href;
            setTimeout(extractPageData, 1000);
        }
    });
    observer.observe(document, { subtree: true, childList: true });

    // Extract on new content (infinite scroll)
    let scrollTimeout;
    window.addEventListener('scroll', () => {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            extractPageData();
        }, 2000);
    });

    console.log(`🌐 Ruby Bridge watching ${detectPlatform()}`);
})();
