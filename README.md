MD→RT
=====

A lightweight macOS menu bar app that automatically converts copied Markdown text to Rich Text formatting while preserving the original.

✨ **What it does**
- Watches your clipboard for Markdown text
- Automatically adds rich text formatting (bold, italic, headers, lists, links, code blocks)
- Keeps both the original Markdown AND the formatted version
- Works seamlessly with your existing clipboard manager
- Uses external API for accurate Markdown conversion with browser-style formatting

🚀 **Quick Start**

**One-liner (recommended):**
```bash
pipx install convert-md-to-rt && md2rt-menubar
```

**Alternative methods:**
```bash
# From source (developers)
git clone https://github.com/taazkareem/convert-md-to-rt.git
cd convert-md-to-rt
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
md2rt-menubar
```

**How to use:**
- Copy any Markdown text (like `**bold**` or `# Heading`)
- Paste into rich text apps (ClickUp, TextEdit, Word, etc.) → you'll see formatting!
- Paste into plain text apps → you'll see original Markdown
- Control via menu bar: Start/Stop/Quit

That's it! The app runs quietly in your menu bar and works automatically.

💡 **Practical Use Cases**
- Copy LLM outputs or prompt templates into ClickUp task descriptions
- Move README snippets into Google Docs with correct headings and lists
- Paste meeting notes from Markdown into Apple Notes or Pages with styling
- Keep pure Markdown when pasting into terminals, editors, or GitHub fields
- Transfer API specs into Confluence or Notion with links and code blocks
- Drop checklists into Outlook or Apple Mail as rich text
- Build proposals in Word by pasting Markdown content with formatting preserved

---

[ClickUp](https://clickup.com) One app to replace them all
