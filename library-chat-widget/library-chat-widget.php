<?php
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

function lcw_register_settings() {
    register_setting('lcw_options_group', 'lcw_api_url');
    register_setting('lcw_options_group', 'lcw_target_page');
}
add_action('admin_init', 'lcw_register_settings');

function lcw_register_options_page() {
    add_options_page(
        'Library AI Settings', 
        'Library AI', 
        'manage_options', 
        'lcw-settings', 
        'lcw_options_page_html'
    );
}
add_action('admin_menu', 'lcw_register_options_page');

function lcw_options_page_html() {
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
                        <input type="text" name="lcw_api_url" value="<?php echo esc_attr(get_option('lcw_api_url', 'http://127.0.0.1:8000/ask')); ?>" style="width: 100%; max-width: 500px;" />
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
}

// -------------------------------------------------------------------------
// 2. ENQUEUE SCRIPTS (Frontend)
// -------------------------------------------------------------------------

function lcw_enqueue_scripts() {
    // Check if we should show the widget
    $target_page = get_option('lcw_target_page');
    if (!empty($target_page) && !is_page($target_page)) {
        return; // Stop loading if we are not on the target page
    }

    wp_enqueue_style('lcw-style', plugin_dir_url(__FILE__) . 'style.css');
    wp_enqueue_script('lcw-script', plugin_dir_url(__FILE__) . 'script.js', array('jquery'), '1.0', true);

    // Get the saved URL or fallback to default
    $api_url = get_option('lcw_api_url', 'http://127.0.0.1:8000/ask');

    wp_localize_script('lcw-script', 'lcwSettings', array(
        'apiUrl' => $api_url,
        'nonce'  => wp_create_nonce('lcw_nonce')
    ));
}
add_action('wp_enqueue_scripts', 'lcw_enqueue_scripts');

// -------------------------------------------------------------------------
// 3. RENDER HTML (Frontend)
// -------------------------------------------------------------------------

function lcw_add_chat_html() {
    // Check visibility again just to be safe
    $target_page = get_option('lcw_target_page');
    if (!empty($target_page) && !is_page($target_page)) {
        return; 
    }
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
}
add_action('wp_footer', 'lcw_add_chat_html');
