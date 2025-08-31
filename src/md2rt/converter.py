"""Markdown to styled HTML conversion using external API."""

import json
import base64
import re
from typing import Tuple
import urllib.request


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
        print(f"API conversion failed: {e}")
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


def markdown_to_styled_html_and_text(text: str) -> Tuple[str, str]:
    """Convert markdown to browser-styled HTML using external API.
    
    Returns (styled_html, original_markdown_text)
    """
    # Get HTML from API
    html = markdown_to_html_via_api(text)
    
    # Add browser-style inline CSS
    styled_html = add_browser_styling_to_html(html)
    
    # Return styled HTML and original markdown text
    return styled_html, text