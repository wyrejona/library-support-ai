import os
import zipfile

# --- Configuration ---
PLUGIN_DIR = "library-chat-widget"
ZIP_NAME = "library-chat-widget.zip"
DEFAULT_API_URL = "http://127.0.0.1:8000/ask" # This acts as the default if the user hasn't saved settings yet

# --- File Contents ---

php_code = f"""<?php
/**
 * Plugin Name: Library AI Assistant
 * Description: A floating chat widget powered by your FastAPI backend. Configurable via Settings > Library AI.
 * Version: 2.0
 * Author: Library Team
 */

if (!defined('ABSPATH')) exit;

// -------------------------------------------------------------------------
// 1. CREATE SETTINGS MENU
// -------------------------------------------------------------------------

function lcw_register_settings() {{
    register_setting('lcw_options_group', 'lcw_api_url');
    register_setting('lcw_options_group', 'lcw_target_page');
}}
add_action('admin_init', 'lcw_register_settings');

function lcw_register_options_page() {{
    add_options_page(
        'Library AI Settings', 
        'Library AI', 
        'manage_options', 
        'lcw-settings', 
        'lcw_options_page_html'
    );
}}
add_action('admin_menu', 'lcw_register_options_page');

function lcw_options_page_html() {{
    ?>
    <div class="wrap">
        <h1>Library AI Assistant Settings</h1>
        <form method="post" action="options.php">
            <?php settings_fields('lcw_options_group'); ?>
            <?php do_settings_sections('lcw_options_group'); ?>
            <table class="form-table">
                <tr valign="top">
                    <th scope="row">Backend API URL</th>
                    <td>
                        <input type="text" name="lcw_api_url" value="<?php echo esc_attr(get_option('lcw_api_url', '{DEFAULT_API_URL}')); ?>" style="width: 100%; max-width: 500px;" />
                        <p class="description">The full URL to your FastAPI endpoint (e.g., https://your-app.com/ask).</p>
                    </td>
                </tr>
                <tr valign="top">
                    <th scope="row">Show only on Page (Slug)</th>
                    <td>
                        <input type="text" name="lcw_target_page" value="<?php echo esc_attr(get_option('lcw_target_page')); ?>" />
                        <p class="description">Enter a page slug (e.g., 'faqs' or 'help') to show the chat widget ONLY on that page. <br><strong>Leave empty</strong> to show on the entire site.</p>
                    </td>
                </tr>
            </table>
            <?php submit_button(); ?>
        </form>
    </div>
    <?php
}}

// -------------------------------------------------------------------------
// 2. ENQUEUE SCRIPTS (Frontend)
// -------------------------------------------------------------------------

function lcw_enqueue_scripts() {{
    // Check if we should show the widget
    $target_page = get_option('lcw_target_page');
    if (!empty($target_page) && !is_page($target_page)) {{
        return; // Stop loading if we are not on the target page
    }}

    wp_enqueue_style('lcw-style', plugin_dir_url(__FILE__) . 'style.css');
    wp_enqueue_script('lcw-script', plugin_dir_url(__FILE__) . 'script.js', array('jquery'), '1.0', true);

    // Get the saved URL or fallback to default
    $api_url = get_option('lcw_api_url', '{DEFAULT_API_URL}');

    wp_localize_script('lcw-script', 'lcwSettings', array(
        'apiUrl' => $api_url,
        'nonce'  => wp_create_nonce('lcw_nonce')
    ));
}}
add_action('wp_enqueue_scripts', 'lcw_enqueue_scripts');

// -------------------------------------------------------------------------
// 3. RENDER HTML (Frontend)
// -------------------------------------------------------------------------

function lcw_add_chat_html() {{
    // Check visibility again just to be safe
    $target_page = get_option('lcw_target_page');
    if (!empty($target_page) && !is_page($target_page)) {{
        return; 
    }}
    ?>
    <div id="lcw-container">
        <button id="lcw-toggle-btn">
            <span class="dashicons dashicons-format-chat"></span> Chat with Library AI
        </button>
        <div id="lcw-chat-window" style="display: none;">
            <div class="lcw-header">
                <h3>Library Assistant</h3>
                <button id="lcw-close-btn">&times;</button>
            </div>
            <div id="lcw-messages">
                <div class="lcw-message bot">
                    Hello! I can answer questions about library hours, policies, and referencing styles. How can I help?
                </div>
            </div>
            <div class="lcw-input-area">
                <input type="text" id="lcw-input" placeholder="Type a question..." />
                <button id="lcw-send-btn">Send</button>
            </div>
        </div>
    </div>
    <?php
}}
add_action('wp_footer', 'lcw_add_chat_html');
"""

css_code = """
#lcw-container {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 99999;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
#lcw-toggle-btn {
    background-color: #0073aa;
    color: white;
    border: none;
    border-radius: 50px;
    padding: 12px 24px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    display: flex;
    align-items: center;
    gap: 8px;
    transition: transform 0.2s;
}
#lcw-toggle-btn:hover { transform: translateY(-2px); }
#lcw-chat-window {
    position: absolute;
    bottom: 70px;
    right: 0;
    width: 350px;
    height: 500px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 5px 25px rgba(0,0,0,0.2);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: lcw-fade-in 0.2s ease-out;
}
@keyframes lcw-fade-in { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.lcw-header {
    background-color: #0073aa;
    color: white;
    padding: 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.lcw-header h3 { margin: 0; font-size: 16px; color: white; }
#lcw-close-btn { background: none; border: none; color: white; font-size: 24px; cursor: pointer; }
#lcw-messages {
    flex: 1;
    padding: 15px;
    overflow-y: auto;
    background-color: #f9f9f9;
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.lcw-message {
    max-width: 85%;
    padding: 10px 14px;
    border-radius: 10px;
    font-size: 14px;
    line-height: 1.5;
}
.lcw-message.bot { align-self: flex-start; background: white; border: 1px solid #ddd; color: #333; border-bottom-left-radius: 2px; }
.lcw-message.user { align-self: flex-end; background: #0073aa; color: white; border-bottom-right-radius: 2px; }
.lcw-message.bot strong { font-weight: bold; }
.lcw-message.bot em { font-style: italic; }
.lcw-input-area {
    padding: 10px;
    border-top: 1px solid #eee;
    background: white;
    display: flex;
    gap: 10px;
}
#lcw-input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 20px; outline: none; }
#lcw-send-btn { background: #0073aa; color: white; border: none; padding: 0 20px; border-radius: 20px; cursor: pointer; font-weight: 600; }
#lcw-send-btn:disabled { background: #ccc; cursor: not-allowed; }
"""

js_code = """
document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.getElementById('lcw-toggle-btn');
    const closeBtn = document.getElementById('lcw-close-btn');
    const chatWindow = document.getElementById('lcw-chat-window');
    const sendBtn = document.getElementById('lcw-send-btn');
    const inputField = document.getElementById('lcw-input');
    const messagesContainer = document.getElementById('lcw-messages');

    if(!toggleBtn) return; // Exit if elements don't exist (e.g. wrong page)

    function toggleChat() {
        if (chatWindow.style.display === 'none') {
            chatWindow.style.display = 'flex';
            toggleBtn.style.display = 'none';
        } else {
            chatWindow.style.display = 'none';
            toggleBtn.style.display = 'flex';
        }
    }
    toggleBtn.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', toggleChat);

    function parseMarkdown(text) {
        if (!text) return '';
        return text
            .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
            .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
            .replace(/\\n/g, '<br>');
    }

    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.classList.add('lcw-message', sender);
        if (sender === 'bot') {
            div.innerHTML = parseMarkdown(text);
        } else {
            div.textContent = text;
        }
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async function sendMessage() {
        const text = inputField.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        inputField.value = '';
        inputField.disabled = true;
        sendBtn.disabled = true;

        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('lcw-message', 'bot');
        loadingDiv.id = 'lcw-loading';
        loadingDiv.textContent = 'Thinking...';
        messagesContainer.appendChild(loadingDiv);

        try {
            const res = await fetch(lcwSettings.apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: text })
            });
            const data = await res.json();
            document.getElementById('lcw-loading').remove();
            
            if (data.answer) {
                addMessage(data.answer, 'bot');
            } else {
                addMessage("I'm sorry, I didn't get a response.", 'bot');
            }
        } catch (err) {
            console.error(err);
            document.getElementById('lcw-loading').remove();
            addMessage("Error connecting to server. Please try again later.", 'bot');
        } finally {
            inputField.disabled = false;
            sendBtn.disabled = false;
            inputField.focus();
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});
"""

def create_zip():
    # 1. Create Directory
    if not os.path.exists(PLUGIN_DIR):
        os.makedirs(PLUGIN_DIR)

    # 2. Write Files
    with open(os.path.join(PLUGIN_DIR, "library-chat-widget.php"), "w") as f:
        f.write(php_code)
    
    with open(os.path.join(PLUGIN_DIR, "style.css"), "w") as f:
        f.write(css_code)
        
    with open(os.path.join(PLUGIN_DIR, "script.js"), "w") as f:
        f.write(js_code)

    # 3. Zip It
    with zipfile.ZipFile(ZIP_NAME, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PLUGIN_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(PLUGIN_DIR))
                zipf.write(file_path, arcname)

    print(f"✅ Success! Created '{ZIP_NAME}'")
    print(f"👉 Download this file and upload it to WordPress (Plugins -> Add New -> Upload Plugin)")

if __name__ == "__main__":
    create_zip()
