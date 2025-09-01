#!/usr/bin/env python3
"""
Debug menubar app for MD→RT with extensive logging and alternative clipboard methods
"""

import threading
import time
import logging
import rumps
import re
import subprocess
import os
import json
import base64
import urllib.request
from AppKit import NSPasteboard, NSObject
from Foundation import NSData, NSString, NSUTF8StringEncoding

# Set up logging to both console and file
log_dir = os.path.expanduser("~/Desktop/md2rt_logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "md2rt_debug.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("md2rt")

def is_markdown(text):
    """Check if text contains markdown formatting."""
    if not text or len(text.strip()) < 3:
        return False
    
    # Common markdown patterns
    patterns = [
        r'\*\*.*?\*\*',  # Bold
        r'\*.*?\*',      # Italic
        r'^#\s+',        # Headers
        r'^##\s+',       # Subheaders
        r'^###\s+',      # Subsubheaders
        r'^\s*[-*+]\s+', # Unordered lists
        r'^\s*\d+\.\s+', # Ordered lists
        r'`.*?`',        # Inline code
        r'```[\s\S]*?```', # Code blocks
        r'^\s*>\s+',     # Blockquotes
        r'\[.*?\]\(.*?\)', # Links
        r'!\[.*?\]\(.*?\)', # Images
    ]
    
    for pattern in patterns:
        if re.search(pattern, text, re.MULTILINE):
            return True
    
    return False

def markdown_to_html_via_api(text: str) -> str:
    """Convert markdown text to HTML using external API."""
    url = 'https://hook.us1.make.com/2jf9wjjs1oupgxbt5t8w5brrkqt7gjxv'
    
    # Prepare the request data
    data = {
        'markdownText': text
    }
    
    # Convert to JSON
    json_data = json.dumps(data).encode('utf-8')
    
    # Create the request
    req = urllib.request.Request(
        url,
        data=json_data,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
            'Referer': 'https://www.switchlabs.dev/'
        }
    )
    
    # Make the request
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            response_text = response.read().decode('utf-8')
            
            # Check if response is a base64 data URL
            if response_text.startswith('data:application/octet-stream;base64,'):
                # Extract the base64 part and decode it
                base64_data = response_text.split(',', 1)[1]
                html = base64.b64decode(base64_data).decode('utf-8')
                return html.strip()
            else:
                # Response is plain HTML
                return response_text.strip()
                
    except Exception as e:
        # Fallback to basic HTML if API fails
        log.error(f"API conversion failed: {e}")
        return f"<p>{text}</p>"

def add_browser_styling_to_html(html: str) -> str:
    """Add browser-style inline CSS to HTML elements for proper clipboard formatting."""
    
    # Add meta charset
    if not html.startswith('<meta'):
        html = "<meta charset='utf-8'>" + html
    
    # Style h1 elements
    html = re.sub(
        r'<h1([^>]*)>',
        r'<h1\1 style="color: rgb(0, 0, 0); font-family: Times; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px; white-space: normal; text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: initial;">',
        html
    )
    
    # Style p elements
    html = re.sub(
        r'<p([^>]*)>',
        r'<p\1 style="color: rgb(0, 0, 0); font-family: Times; font-size: medium; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px; white-space: normal; text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: initial;">',
        html
    )
    
    # Explicitly close any open lists before code blocks to break list context
    # First remove any existing style attributes from pre tags
    html = re.sub(r'<pre([^>]*?)style="[^"]*"([^>]*)>', r'<pre\1\2>', html)
    
    # Insert explicit list closure before each pre block to break list context
    html = re.sub(
        r'<pre([^>]*)>(.*?)</pre>',
        r'</ol></ul><pre\1 style="display: block; color: rgb(0, 0, 0); font-family: Monaco, Menlo, Consolas, monospace; font-size: 13px; background-color: rgb(248, 248, 248); border: 1px solid rgb(231, 231, 231); border-radius: 3px; padding: 16px; margin: 16px 0; overflow-x: auto; white-space: pre;">\2</pre>',
        html,
        flags=re.DOTALL
    )
    
    # Style code elements within pre blocks
    # First remove any existing style attributes from code tags
    html = re.sub(r'<code([^>]*?)style="[^"]*"([^>]*)>', r'<code\1\2>', html)

    # Then add simple styling
    html = re.sub(
        r'<code([^>]*)>',
        r'<code\1 style="font-family: Monaco, Menlo, Consolas, monospace; font-size: 13px; color: rgb(51, 51, 51); background: transparent;">',
        html
    )
    
    # Add non-breaking spaces around strong elements (like browser does)
    html = re.sub(r'<strong>', '<span>\xa0</span><strong>', html)
    html = re.sub(r'</strong>', '</strong><span>\xa0</span>', html)
    
    return html

def markdown_to_styled_html_and_text(md_text):
    """Convert markdown to styled HTML using external API."""
    # Get HTML from API
    html = markdown_to_html_via_api(md_text)
    
    # Add browser-style inline CSS
    styled_html = add_browser_styling_to_html(html)
    
    # Return styled HTML and original markdown text
    return styled_html, md_text

def read_plain_text_from_pasteboard():
    """Read plain text from the clipboard using multiple methods."""
    log.debug("🔍 Attempting to read from clipboard...")
    
    # Method 1: NSPasteboard
    try:
        pasteboard = NSPasteboard.generalPasteboard()
        text = pasteboard.stringForType_("public.utf8-plain-text")
        if text:
            log.debug(f"✅ NSPasteboard method successful: {repr(text[:100])}...")
            return text
        else:
            log.debug("❌ NSPasteboard returned empty text")
    except Exception as e:
        log.error(f"❌ NSPasteboard method failed: {e}")
    
    # Method 2: pbpaste command
    try:
        result = subprocess.run(['pbpaste'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            text = result.stdout.strip()
            log.debug(f"✅ pbpaste method successful: {repr(text[:100])}...")
            return text
        else:
            log.debug(f"❌ pbpaste failed: returncode={result.returncode}, stderr={result.stderr}")
    except Exception as e:
        log.error(f"❌ pbpaste method failed: {e}")
    
    log.debug("❌ All clipboard reading methods failed")
    return None

def add_styled_html_to_pasteboard_preserving_original(html, original_text):
    """Add styled HTML to clipboard while preserving original text using multiple methods."""
    log.debug(f"🔍 Attempting to write HTML to clipboard (length: {len(html)})")
    
    # Method 1: NSPasteboard
    try:
        pasteboard = NSPasteboard.generalPasteboard()
        
        # Clear existing content
        pasteboard.clearContents()
        log.debug("✅ Cleared pasteboard contents")
        
        # Add HTML content
        html_data = NSData.dataWithBytes_length_(html.encode('utf-8'), len(html.encode('utf-8')))
        pasteboard.setData_forType_(html_data, "public.html")
        log.debug("✅ Added HTML data to pasteboard")
        
        # Add plain text content (preserve original)
        pasteboard.setString_forType_(original_text, "public.utf8-plain-text")
        log.debug("✅ Added plain text to pasteboard")
        
        # Verify what's in the pasteboard
        available_types = pasteboard.types()
        log.debug(f"✅ Available pasteboard types: {available_types}")
        
        return True
    except Exception as e:
        log.error(f"❌ NSPasteboard method failed: {e}")
    
    # Method 2: pbcopy command
    try:
        # Create a temporary file with the HTML content
        temp_file = os.path.join(log_dir, "temp_clipboard.html")
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Use pbcopy to copy the HTML file
        result = subprocess.run(['pbcopy'], input=html, text=True, timeout=5)
        if result.returncode == 0:
            log.debug("✅ pbcopy method successful")
            return True
        else:
            log.debug(f"❌ pbcopy failed: returncode={result.returncode}")
    except Exception as e:
        log.error(f"❌ pbcopy method failed: {e}")
    
    log.debug("❌ All clipboard writing methods failed")
    return False

class Md2RtMenuApp(rumps.App):
    def __init__(self):
        super().__init__("MD→RT", icon=None, quit_button=None)

        # State
        self._running = False
        self._thread = None

        # Create menu items
        self._start_item = rumps.MenuItem('Start', callback=self.start_clicked)
        self._stop_item = rumps.MenuItem('Stop', callback=self.stop_clicked)
        self._quit_item = rumps.MenuItem('Quit', callback=self.quit_clicked)
        self._debug_item = rumps.MenuItem('Debug Info', callback=self.debug_clicked)

        # Auto-start when launched
        self.start_watcher()

    def _update_menu(self):
        """Update menu items based on current state."""
        # Clear the menu completely
        self.menu.clear()

        # Add only the appropriate items based on state
        if self._running:
            # When running, show Stop, Debug, and Quit
            self.menu.add(self._stop_item)
            self.menu.add(self._debug_item)
            self.menu.add(rumps.separator)
            self.menu.add(self._quit_item)
        else:
            # When stopped, show Start, Debug, and Quit
            self.menu.add(self._start_item)
            self.menu.add(self._debug_item)
            self.menu.add(rumps.separator)
            self.menu.add(self._quit_item)

    def start_watcher(self):
        """Start the clipboard watcher."""
        if self._running:
            return

        log.info("🚀 Starting clipboard watcher...")
        self._running = True
        self._thread = threading.Thread(target=self._run_clipboard_watcher, daemon=True)
        self._thread.start()

        # Wait a moment to ensure thread starts
        time.sleep(0.1)

        # Verify thread is running
        if self._thread.is_alive():
            log.info("✅ Clipboard watcher thread started successfully")
        else:
            log.error("❌ Failed to start clipboard watcher thread")
            self._running = False

        self._update_menu()
        rumps.notification("MD→RT", "Started", "Watching clipboard for Markdown")

    def stop_watcher(self):
        """Stop the clipboard watcher."""
        if not self._running:
            return

        log.info("🛑 Stopping clipboard watcher...")
        self._running = False
        self._update_menu()
        rumps.notification("MD→RT", "Stopped", "Stopped watching clipboard")

    def debug_clicked(self, _):
        """Show debug information."""
        log.info("🔍 Debug info requested")
        
        # Check clipboard contents
        text = read_plain_text_from_pasteboard()
        if text:
            log.info(f"📋 Current clipboard text: {repr(text[:200])}...")
            is_md = is_markdown(text)
            log.info(f"📝 Is markdown: {is_md}")
            
            if is_md:
                html, _ = markdown_to_styled_html_and_text(text)
                log.info(f"🔄 Generated HTML length: {len(html)}")
                log.info(f"🔄 HTML preview: {html[:500]}...")
        else:
            log.info("📋 No text in clipboard")
        
        # Show log file location
        log.info(f"📁 Log file location: {log_file}")
        rumps.notification("MD→RT", "Debug Info", f"Check logs at: {log_file}")

    def _run_clipboard_watcher(self):
        """Run the clipboard watcher."""
        pasteboard = NSPasteboard.generalPasteboard()
        last_change_count = int(pasteboard.changeCount())
        last_processed_hash = None

        log.info(f"🔍 Starting clipboard monitoring, initial count: {last_change_count}")

        while self._running:
            try:
                current = int(pasteboard.changeCount())
                if current != last_change_count:
                    log.info(f"📋 Clipboard changed: {last_change_count} -> {current}")
                    last_change_count = current

                    # Process the change
                    self._process_clipboard_change()

                time.sleep(0.3)
            except Exception as exc:
                log.error(f"❌ Clipboard monitoring error: {exc}")
                import traceback
                traceback.print_exc()
                break

        log.info("🔍 Clipboard monitoring stopped")

    def _process_clipboard_change(self):
        """Process clipboard change."""
        try:
            log.debug("🔄 Processing clipboard change...")
            
            text = read_plain_text_from_pasteboard()
            if not text:
                log.debug("📋 No text in clipboard")
                return

            log.debug(f"📋 Clipboard text: {repr(text[:100])}...")

            # Check if it's markdown
            if not is_markdown(text):
                log.debug("📝 Not Markdown, ignoring")
                return

            log.info("✅ Markdown detected, converting...")

            # Convert to HTML
            html, plain = markdown_to_styled_html_and_text(text)
            log.info(f"🔄 Conversion complete, HTML length: {len(html)}")

            # Add to clipboard
            success = add_styled_html_to_pasteboard_preserving_original(html, text)
            if success:
                log.info("✅ Styled HTML added to clipboard!")
            else:
                log.error("❌ Failed to add HTML to clipboard")

        except Exception as exc:
            log.error(f"❌ Processing error: {exc}")
            import traceback
            traceback.print_exc()

    def start_clicked(self, _):
        self.start_watcher()

    def stop_clicked(self, _):
        self.stop_watcher()

    def quit_clicked(self, _):
        rumps.quit_application()

def main():
    """Main function"""
    log.info("🚀 Starting MD→RT Debug App...")
    app = Md2RtMenuApp()
    app.run()

if __name__ == "__main__":
    main()
