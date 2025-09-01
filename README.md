# MD→RT (Markdown to Rich Text)

**The easiest way to convert Markdown to Rich Text on macOS - no terminal required!**

MD→RT is a simple menubar app that automatically converts Markdown text in your clipboard to Rich Text formatting. Just copy Markdown from anywhere (ChatGPT, GitHub, etc.) and paste it into any rich text app - it will be automatically converted!

## ✨ Features

- **Automatic Conversion**: Copy Markdown, paste Rich Text - it's that simple!
- **Menubar Integration**: Runs quietly in your menu bar
- **Real-time Monitoring**: Watches your clipboard for Markdown content
- **Smart Detection**: Only converts actual Markdown, ignores plain text
- **Preserves Original**: Keeps the original Markdown text as a fallback
- **Zero Configuration**: Works out of the box

## 🚀 Quick Start

**One-liner (recommended):**
```bash
git clone https://github.com/taazkareem/convert-md-to-rt.git && cd convert-md-to-rt && ./run_md2rt.command
```

**Alternative (if you prefer to download just the script):**
```bash
curl -L -o run_md2rt.command "https://raw.githubusercontent.com/taazkareem/convert-md-to-rt/main/run_md2rt.command?$(date +%s)" && chmod +x run_md2rt.command && ./run_md2rt.command
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

## 🛠️ Development

### Prerequisites
- Python 3.9+
- macOS (required for clipboard access)

### Setup
```bash
# Clone the repository
git clone https://github.com/taazkareem/convert-md-to-rt.git
cd convert-md-to-rt

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests
```bash
pytest
```

### Project Structure
```
src/md2rt/
├── __init__.py
├── menubar_debug.py    # Main menubar app (working version)
├── menubar.py          # Core menubar functionality
├── detector.py         # Markdown detection logic
├── converter.py        # Markdown to HTML conversion
├── clipboard.py        # Clipboard operations
└── runner.py           # Command-line runner
```

## 🤝 Contributing

This is an open-source project! Contributions are welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

**Acknowledgments**
- Conversion Powered by [Switchlabs](https://www.switchlabs.dev/)
- [ClickUp](https://clickup.com) One app to replace them all
