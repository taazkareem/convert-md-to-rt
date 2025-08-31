from __future__ import annotations

import threading
import logging
from typing import Optional

import rumps

from .runner import run_watcher


class Md2RtMenuApp(rumps.App):
    def __init__(self) -> None:
        super().__init__("MD→RT", icon=None, menu=[])
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self.title = "MD→RT"
        self.quit_button = None  # hide default Quit
        self._setup_logging()
        
        # Create menu items explicitly
        self._start_item = rumps.MenuItem('Start', callback=self.start_clicked)
        self._stop_item = rumps.MenuItem('Stop', callback=self.stop_clicked)
        self._quit_item = rumps.MenuItem('Quit', callback=self.quit_clicked)
        
        # Auto-start when launched
        self.start_watcher()

    def _setup_logging(self) -> None:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    def _update_menu(self) -> None:
        """Update menu items based on current state."""
        # Clear the menu completely
        self.menu.clear()
        
        # Add only the appropriate items based on state
        if self._running:
            # When running, show only Stop and Quit
            self.menu.add(self._stop_item)
            self.menu.add(rumps.separator)
            self.menu.add(self._quit_item)
        else:
            # When stopped, show only Start and Quit
            self.menu.add(self._start_item)
            self.menu.add(rumps.separator)
            self.menu.add(self._quit_item)

    def _run_watcher_thread(self) -> None:
        """Run the clipboard watcher without signal handlers (for background thread)."""
        import hashlib
        from typing import Optional
        from .detector import is_markdown
        from .converter import markdown_to_styled_html_and_text
        from .clipboard import (
            read_plain_text_from_pasteboard,
            add_styled_html_to_pasteboard_preserving_original,
        )

        def _hash_text(text: str) -> str:
            return hashlib.sha256(text.encode("utf-8")).hexdigest()

        log = logging.getLogger("md2rt")
        last_processed_hash: Optional[str] = None

        def on_change(_change_count: int) -> None:
            nonlocal last_processed_hash
            if not self._running:  # Check if we should stop
                return
                
            text = read_plain_text_from_pasteboard()
            if not text:
                return

            current_hash = _hash_text(text)
            if last_processed_hash == current_hash:
                return

            if not is_markdown(text):
                log.debug("Clipboard changed but not Markdown; ignoring")
                last_processed_hash = current_hash
                return

            try:
                styled_html, plain_text = markdown_to_styled_html_and_text(text)
            except Exception as exc:
                log.exception("Conversion failed: %s", exc)
                return

            add_styled_html_to_pasteboard_preserving_original(styled_html, text)
            log.info("Added styled HTML to clipboard (%d chars), preserving original Markdown", len(styled_html))
            last_processed_hash = _hash_text(text)

        # Custom polling loop that respects self._running
        from AppKit import NSPasteboard
        import time
        
        pasteboard = NSPasteboard.generalPasteboard()
        last_change_count = int(pasteboard.changeCount())
        
        while self._running:
            try:
                current = int(pasteboard.changeCount())
                if current != last_change_count:
                    last_change_count = current
                    on_change(current)
                time.sleep(0.3)
            except Exception as exc:
                log.exception("Polling error: %s", exc)
                break

    def start_watcher(self) -> None:
        """Start the clipboard watcher."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_watcher_thread, daemon=True)
        self._thread.start()
        self._update_menu()
        rumps.notification("MD→RT", "Started", "Watching clipboard for Markdown")

    def stop_watcher(self) -> None:
        """Stop the clipboard watcher."""
        if not self._running:
            return
            
        self._running = False
        self._update_menu()
        rumps.notification("MD→RT", "Stopped", "Stopped watching clipboard")

    def start_clicked(self, _):
        self.start_watcher()

    def stop_clicked(self, _):
        self.stop_watcher()

    def quit_clicked(self, _):
        rumps.quit_application()


def main() -> int:
    Md2RtMenuApp().run()
    return 0


