MD→RT
=====
[![PyPI version](https://img.shields.io/pypi/v/convert-md-to-rt.svg?logo=pypi&label=PyPI)](https://pypi.org/project/convert-md-to-rt/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?logo=opensourceinitiative&label=License)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/github/actions/workflow/status/taazkareem/convert-md-to-rt/publish.yml?branch=main&logo=github&label=CI)](https://github.com/taazkareem/convert-md-to-rt/actions)

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
- Paste into plain text apps → you'll see original Markdown!
- Control via menu bar: Start/Stop/Quit

That's it! The app runs quietly in your menu bar and works automatically by simply detecting Markdown content.

💡 **Pro Use Case**
- Copy LLM outputs directly into ClickUp task descriptions with formatting
- Easily send Apple Mail with checkmarked lists or code blocks
- Many more

---

 **Acknowledgments**
- Conversion Powered by [Switchlabs](https://www.switchlabs.dev/)
- [ClickUp](https://clickup.com) One app to replace them all
