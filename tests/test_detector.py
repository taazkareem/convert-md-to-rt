from md2rt.detector import is_markdown


def test_is_markdown_true_on_common_patterns():
    md = """\
# Heading

- item 1
- item 2

`code` and **bold** and [link](https://example.com)
"""
    assert is_markdown(md) is True


def test_is_markdown_false_on_plain_text():
    txt = "This is a sentence without any markdown notation or lists."
    assert is_markdown(txt) is False