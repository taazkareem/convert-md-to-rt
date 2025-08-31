from md2rt.converter import markdown_to_html_via_api, markdown_to_styled_html_and_text


def test_markdown_to_html_via_api_contains_expected_elements():
    """Test that the external API returns proper HTML elements."""
    html = markdown_to_html_via_api("# Title\n\n**bold** and [link](https://example.com)")
    assert "<h1" in html
    assert "<strong>bold</strong>" in html
    assert "<a href=\"https://example.com\"" in html


def test_markdown_to_styled_html_and_text():
    """Test the complete styled HTML conversion pipeline."""
    markdown_text = "# Title\n\n**bold** text"
    styled_html, original_text = markdown_to_styled_html_and_text(markdown_text)
    
    # Check that we get both outputs
    assert isinstance(styled_html, str)
    assert original_text == markdown_text
    
    # Check that styling is added
    assert "charset='utf-8'" in styled_html
    assert "style=" in styled_html
    assert "<h1" in styled_html
    assert "<strong>" in styled_html


