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
        r'\*\*.*?\*\*',      # **bold**
        r'\*.*?\*',          # *italic*
        r'`.*?`',            # `code`
        r'#+\s+',            # # heading
        r'\[.*?\]\(.*?\)',   # [link](url)
        r'!\[.*?\]\(.*?\)',  # ![alt](url)
        r'^\s*[-*+]\s+',     # - list item
        r'^\s*\d+\.\s+',     # 1. numbered list
        r'^\s*>\s+',         # > blockquote
        r'```[\s\S]*?```',   # ```code block```
    ]
    
    for pattern in patterns:
        if re.search(pattern, text, re.MULTILINE):
            return True
    
    return False

def simple_markdown_to_html(md_text):
    """Convert markdown to HTML using simple regex replacements."""
    html = md_text
    
    # Headers
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold and italic
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    # Inline code
    html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
    
    # Code blocks
    html = re.sub(r'```([\s\S]*?)```', r'<pre><code>\1</code></pre>', html)
    
    # Lists
    html = re.sub(r'^\s*[-*+]\s+(.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'^\s*\d+\.\s+(.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    
    # Wrap consecutive list items in <ul> tags
    lines = html.split('\n')
    in_list = False
    result_lines = []
    
    for line in lines:
        if line.strip().startswith('<li>'):
            if not in_list:
                result_lines.append('<ul>')
                in_list = True
            result_lines.append(line)
        else:
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            result_lines.append(line)
    
    if in_list:
        result_lines.append('</ul>')
    
    html = '\n'.join(result_lines)
    
    # Blockquotes
    html = re.sub(r'^\s*>\s+(.*?)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)
    
    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Images
    html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', html)
    
    # Paragraphs (wrap non-tag lines in <p> tags)
    lines = html.split('\n')
    result_lines = []
    current_paragraph = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_paragraph:
                result_lines.append('<p>' + ' '.join(current_paragraph) + '</p>')
                current_paragraph = []
        elif line.startswith('<') and line.endswith('>'):
            if current_paragraph:
                result_lines.append('<p>' + ' '.join(current_paragraph) + '</p>')
                current_paragraph = []
            result_lines.append(line)
        else:
            current_paragraph.append(line)
    
    if current_paragraph:
        result_lines.append('<p>' + ' '.join(current_paragraph) + '</p>')
    
    html = '\n'.join(result_lines)
    
    return html

def markdown_to_styled_html_and_text(md_text):
    """Convert markdown to styled HTML."""
    # Convert markdown to HTML using our simple parser
    html = simple_markdown_to_html(md_text)
    
    # Add basic styling
    styled_html = f"""
    <meta charset='utf-8'>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; margin: 20px; }}
        h1, h2, h3, h4, h5, h6 {{ color: #333; margin-top: 24px; margin-bottom: 16px; }}
        h1 {{ font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
        h2 {{ font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
        h3 {{ font-size: 1.25em; }}
        p {{ margin-bottom: 16px; }}
        blockquote {{ padding: 0 1em; color: #6a737d; border-left: 0.25em solid #dfe2e5; margin: 0 0 16px 0; }}
        code {{ background-color: rgba(27,31,35,0.05); border-radius: 3px; font-size: 85%; margin: 0; padding: 0.2em 0.4em; }}
        pre {{ background-color: #f6f8fa; border-radius: 6px; font-size: 85%; line-height: 1.45; overflow: auto; padding: 16px; }}
        pre code {{ background-color: transparent; padding: 0; }}
        ul, ol {{ padding-left: 2em; }}
        li {{ margin-bottom: 0.25em; }}
        a {{ color: #0366d6; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        img {{ max-width: 100%; }}
    </style>
    {html}
    """
    
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
