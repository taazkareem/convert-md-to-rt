#!/usr/bin/env python3
"""
MD→RT Menubar App - Consolidated version with configurable logging
"""

import threading
import time
import logging
from . import rumps
import re
import os
import argparse
import sys
from AppKit import NSPasteboard, NSObject
from Foundation import NSData, NSString, NSUTF8StringEncoding

def setup_logging(level):
    """Setup logging based on command line argument."""
    if level == 'quiet':
        log_level = logging.WARNING
        format_str = "%(levelname)s %(message)s"
    elif level == 'normal':
        log_level = logging.INFO
        format_str = "%(asctime)s %(levelname)s %(message)s"
    elif level == 'verbose':
        log_level = logging.DEBUG
        format_str = "%(asctime)s %(levelname)s %(message)s"
    elif level == 'debug':
        log_level = logging.DEBUG
        format_str = "%(asctime)s %(levelname)s %(funcName)s:%(lineno)d %(message)s"
    else:
        log_level = logging.INFO
        format_str = "%(asctime)s %(levelname)s %(message)s"
    
    logging.basicConfig(level=log_level, format=format_str)
    return logging.getLogger("md2rt")

def is_markdown(text):
    """Check if text contains markdown formatting."""
    if not text or len(text.strip()) < 3:
        return False
    
    # Skip if text appears to be already converted HTML
    if '<' in text and '>' in text:
        # Check for common HTML tags that indicate already converted content
        html_indicators = ['<h1', '<h2', '<h3', '<p', '<strong', '<em', '<ul', '<ol', '<li', '<code', '<pre']
        if any(indicator in text for indicator in html_indicators):
            return False
    
    # Skip if text appears to be already converted Rich Text
    rich_text_indicators = ['style=', 'font-family:', 'color:', 'background-color:']
    if any(indicator in text for indicator in rich_text_indicators):
        return False
    
    # Skip if text contains mostly GitHub badges or non-content Markdown
    badge_patterns = [
        r'!\[.*?\]\(https?://.*?\)',  # Image badges
        r'\[.*?\]\(https?://.*?\)',   # Link badges
        r'https?://.*?\.svg',         # SVG badge URLs
        r'img\.shields\.io',          # Shields.io badges
    ]
    
    badge_count = 0
    for pattern in badge_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            badge_count += 1
    
    # If more than 50% of the text is badges, skip it
    if badge_count > 0 and len(text.split('\n')) > 0:
        lines = text.split('\n')
        badge_lines = sum(1 for line in lines if any(re.search(pattern, line, re.IGNORECASE) for pattern in badge_patterns))
        if badge_lines / len(lines) > 0.5:
            return False
    
    # Common markdown patterns (more strict matching)
    patterns = [
        r'^\s*#\s+\w+',        # Headers with content
        r'^\s*##\s+\w+',       # Subheaders with content
        r'^\s*###\s+\w+',      # Subsubheaders with content
        r'^\s*[-*+]\s+\w+',    # Unordered lists with content
        r'^\s*\d+\.\s+\w+',    # Ordered lists with content
        r'\*\*[^*]+\*\*',      # Bold with content
        r'\*[^*]+\*',          # Italic with content
        r'`[^`]+`',            # Inline code with content
        r'^\s*```[\s\S]*?```', # Code blocks
        r'^\s*>\s+\w+',        # Blockquotes with content
        r'\[[^\]]+\]\([^)]+\)', # Links with content
        r'!\[[^\]]*\]\([^)]+\)', # Images with content
    ]
    
    # Count how many patterns match
    match_count = 0
    for pattern in patterns:
        if re.search(pattern, text, re.MULTILINE):
            match_count += 1
    
    # Only consider it Markdown if we have multiple strong indicators
    # This prevents false positives on text with just one or two Markdown-like characters
    return match_count >= 2

def markdown_to_styled_html_and_text(md_text):
    """Convert markdown to styled HTML using external API."""
    try:
        # Try to use the external API first
        from .converter import markdown_to_styled_html_and_text as api_converter
        return api_converter(md_text)
    except ImportError:
        # Fallback to built-in converter if external module not available
        log.warning("External API not available, using built-in converter")
        return simple_markdown_to_html(md_text), md_text

def simple_markdown_to_html(md_text):
    """Fallback markdown to HTML converter."""
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
    
    return styled_html

def read_plain_text_from_pasteboard():
    """Read plain text from the clipboard."""
    try:
        pasteboard = NSPasteboard.generalPasteboard()
        text = pasteboard.stringForType_("public.utf8-plain-text")
        return text if text else None
    except Exception as e:
        log.error(f"Error reading clipboard: {e}")
        return None

def add_styled_html_to_pasteboard_preserving_original(html, original_text):
    """Add styled HTML to clipboard while preserving original text."""
    try:
        pasteboard = NSPasteboard.generalPasteboard()
        
        # Clear existing content
        pasteboard.clearContents()
        
        # Add HTML content
        html_data = NSData.dataWithBytes_length_(html.encode('utf-8'), len(html.encode('utf-8')))
        pasteboard.setData_forType_(html_data, "public.html")
        
        # Add plain text content (preserve original)
        pasteboard.setString_forType_(original_text, "public.utf8-plain-text")
        
        return True
    except Exception as e:
        log.error(f"Error writing to clipboard: {e}")
        return False

class Md2RtMenuApp(rumps.App):
    def __init__(self, log_level='normal'):
        super().__init__("MD→RT", icon=None, quit_button=None)
        
        # Setup logging
        self.log = setup_logging(log_level)
        
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

        self.log.info("🚀 Starting clipboard watcher...")
        self._running = True
        self._thread = threading.Thread(target=self._run_clipboard_watcher, daemon=True)
        self._thread.start()

        # Wait a moment to ensure thread starts
        time.sleep(0.1)

        # Verify thread is running
        if self._thread.is_alive():
            self.log.info("✅ Clipboard watcher thread started successfully")
        else:
            self.log.error("❌ Failed to start clipboard watcher thread")
            self._running = False

        self._update_menu()
        rumps.notification("MD→RT", "Started", "Watching clipboard for Markdown")

    def stop_watcher(self):
        """Stop the clipboard watcher."""
        if not self._running:
            return

        self.log.info("🛑 Stopping clipboard watcher...")
        self._running = False
        self._update_menu()
        rumps.notification("MD→RT", "Stopped", "Stopped watching clipboard")

    def debug_clicked(self, _):
        """Show debug information."""
        self.log.info("🔍 Debug info requested")
        
        # Check clipboard contents
        text = read_plain_text_from_pasteboard()
        if text:
            self.log.info(f"📋 Current clipboard text: {repr(text[:200])}...")
            is_md = is_markdown(text)
            self.log.info(f"📝 Is markdown: {is_md}")
            
            if is_md:
                html, plain = markdown_to_styled_html_and_text(text)
                self.log.info(f"🔄 Generated HTML length: {len(html)}")
                self.log.info(f"🔄 HTML preview: {html[:500]}...")
        else:
            self.log.info("📋 No text in clipboard")
        
        # Show debug info notification
        rumps.notification("MD→RT", "Debug Info", "Check terminal for debug information")

    def _run_clipboard_watcher(self):
        """Run the clipboard watcher."""
        pasteboard = NSPasteboard.generalPasteboard()
        last_change_count = int(pasteboard.changeCount())
        last_processed_hash = None
        last_processed_content = None

        self.log.info(f"🔍 Starting clipboard monitoring, initial count: {last_change_count}")

        while self._running:
            try:
                current = int(pasteboard.changeCount())
                if current != last_change_count:
                    # Only log if we haven't processed this content before
                    text = read_plain_text_from_pasteboard()
                    if text and text != last_processed_content:
                        self.log.info(f"📋 Clipboard changed: {last_change_count} -> {current}")
                        last_change_count = current
                        last_processed_content = text

                        # Process the change
                        self._process_clipboard_change()
                    else:
                        # Content is the same, just update the count
                        last_change_count = current

                time.sleep(0.3)
            except Exception as exc:
                self.log.error(f"❌ Clipboard monitoring error: {exc}")
                break

        self.log.info("🔍 Clipboard monitoring stopped")

    def _process_clipboard_change(self):
        """Process clipboard change."""
        try:
            text = read_plain_text_from_pasteboard()
            if not text:
                self.log.debug("📋 No text in clipboard")
                return

            # Check if it's markdown
            if not is_markdown(text):
                self.log.debug("📝 Not Markdown, ignoring")
                return

            self.log.info("✅ Markdown detected, converting...")

            # Convert to HTML
            html, plain = markdown_to_styled_html_and_text(text)
            self.log.info(f"🔄 Conversion complete, HTML length: {len(html)}")

            # Add to clipboard
            success = add_styled_html_to_pasteboard_preserving_original(html, text)
            if success:
                self.log.info("✅ Styled HTML added to clipboard!")
            else:
                self.log.error("❌ Failed to add HTML to clipboard")

        except Exception as exc:
            self.log.error(f"❌ Processing error: {exc}")
            import traceback
            traceback.print_exc()

    def start_clicked(self, _):
        self.start_watcher()

    def stop_clicked(self, _):
        self.stop_watcher()

    def quit_clicked(self, _):
        rumps.quit_application()

def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="MD→RT - Convert Markdown to Rich Text in your clipboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Normal logging (default)
  %(prog)s --quiet           # Minimal logging (production)
  %(prog)s --verbose         # Detailed logging (development)
  %(prog)s --debug           # Maximum logging (debugging)
        """
    )
    
    parser.add_argument(
        '--log-level', '-l',
        choices=['quiet', 'normal', 'verbose', 'debug'],
        default='normal',
        help='Set logging level (default: normal)'
    )
    
    args = parser.parse_args()
    
    # Create and run the app
    app = Md2RtMenuApp(log_level=args.log_level)
    app.run()

if __name__ == "__main__":
    main()
