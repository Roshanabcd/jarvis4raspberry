from playwright.sync_api import sync_playwright
import time
import os

def whatsapp_action(action, contact_name=None, message=None, platform="whatsapp"):
    """
    Automates WhatsApp Web and Messenger using Playwright.
    Supported platforms: 'whatsapp', 'messenger', 'facebook'
    Actions: 'send_message', 'voice_call', 'video_call', 'open'
    """
    # Ensure browser data directory exists to save logins
    user_data_dir = os.path.join(os.getcwd(), "browser_data")
    os.makedirs(user_data_dir, exist_ok=True)
    
    # Start Playwright
    with sync_playwright() as p:
        # Launch persistent context to save login sessions (QR code / Cookies)
        # We must grant permissions for microphone and camera for calls
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False, # Must be visible for the user to scan QR the first time or see the call
            args=['--use-fake-ui-for-media-stream'], # Auto-accept camera/mic permissions
            permissions=['microphone', 'camera', 'notifications']
        )
        
        page = context.new_page()
        
        try:
            if platform == "facebook":
                page.goto("https://www.facebook.com/")
                # Just leave it open for the user
                return "Facebook is now open on your screen."
                
            elif platform == "messenger":
                page.goto("https://www.messenger.com/")
                if action == "open":
                    return "Messenger is now open on your screen."
                
                # Logic for messenger (requires user to be logged in)
                if action == "send_message" and contact_name and message:
                    page.fill('input[aria-label="Search Messenger"]', contact_name)
                    time.sleep(2)
                    page.keyboard.press("Enter")
                    time.sleep(3)
                    page.fill('div[aria-label="Message"]', message)
                    page.keyboard.press("Enter")
                    time.sleep(1)
                    return f"Message sent to {contact_name} on Messenger."
                    
                elif action in ["voice_call", "video_call"] and contact_name:
                    page.fill('input[aria-label="Search Messenger"]', contact_name)
                    time.sleep(2)
                    page.keyboard.press("Enter")
                    time.sleep(3)
                    if action == "voice_call":
                        page.click('div[aria-label="Start a voice call"]')
                        return f"Starting a voice call with {contact_name} on Messenger."
                    else:
                        page.click('div[aria-label="Start a video call"]')
                        return f"Starting a video call with {contact_name} on Messenger."
                
            elif platform == "whatsapp":
                page.goto("https://web.whatsapp.com/")
                
                # Wait for WhatsApp Web to load (Wait for the search bar to appear)
                print("Waiting for WhatsApp to load. If it's your first time, please scan the QR code.")
                page.wait_for_selector('div[contenteditable="true"][data-tab="3"]', timeout=60000)
                
                if action == "open":
                    return "WhatsApp Web is now open on your screen."
                
                if contact_name:
                    # Search for the contact
                    search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
                    search_box.fill(contact_name)
                    time.sleep(2)
                    
                    # Click the first contact in the search results
                    page.locator(f'span[title="{contact_name}"]').first.click()
                    time.sleep(2)
                    
                    if action == "send_message" and message:
                        # Type the message and send
                        message_box = page.locator('div[contenteditable="true"][data-tab="10"]')
                        message_box.fill(message)
                        page.keyboard.press("Enter")
                        time.sleep(1)
                        return f"Message sent to {contact_name} on WhatsApp."
                        
                    elif action == "voice_call":
                        # Click the voice call button (Header icon)
                        page.click('span[data-icon="ic-audio-call"]')
                        return f"Initiating WhatsApp Voice Call to {contact_name}."
                        
                    elif action == "video_call":
                        # Click the video call button
                        page.click('span[data-icon="ic-video-call"]')
                        return f"Initiating WhatsApp Video Call to {contact_name}."
                        
        except Exception as e:
            return f"Failed to automate {platform}. Error: {e}"
        finally:
            # We don't close the context if it's a call or opening the app so the user can interact
            if action not in ["voice_call", "video_call", "open"]:
                context.close()
            else:
                # If it's a call or open, we detach so Playwright doesn't kill the browser when python exits
                pass
                
        return f"Finished {action} on {platform}."


whatsapp_tool_schema = {
    "type": "function",
    "function": {
        "name": "whatsapp_action",
        "description": "Call this tool to send messages, open, or place voice/video calls on WhatsApp Web, Facebook, or Messenger.",
        "parameters": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["whatsapp", "messenger", "facebook"],
                    "description": "The platform to use."
                },
                "action": {
                    "type": "string",
                    "enum": ["send_message", "voice_call", "video_call", "open"],
                    "description": "The action to perform."
                },
                "contact_name": {
                    "type": "string",
                    "description": "The name of the contact as it appears in the app. Required for sending messages or calling."
                },
                "message": {
                    "type": "string",
                    "description": "The message to send. Required if action is 'send_message'."
                }
            },
            "required": ["platform", "action"]
        }
    }
}
