import sys
import pytest


@pytest.mark.skipif(sys.platform != "darwin", reason="Requires macOS AppKit")
def test_clipboard_integration():
    """Test that we can add styled HTML to clipboard."""
    from md2rt.clipboard import add_styled_html_to_pasteboard_preserving_original, read_plain_text_from_pasteboard
    
    # Test HTML with browser-style formatting
    styled_html = "<meta charset='utf-8'><h1 style='color: rgb(0, 0, 0); font-family: Times;'>Title</h1>"
    original_markdown = "# Title"
    
    # Add to clipboard
    add_styled_html_to_pasteboard_preserving_original(styled_html, original_markdown)
    
    # Read back plain text (should be the original markdown)
    plain_text = read_plain_text_from_pasteboard()
    assert plain_text == original_markdown


