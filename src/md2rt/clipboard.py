from __future__ import annotations

import time
from typing import Optional


def read_plain_text_from_pasteboard() -> Optional[str]:
    """Return the current plain text contents of the general pasteboard, if any."""
    from AppKit import NSPasteboard, NSPasteboardTypeString

    pasteboard = NSPasteboard.generalPasteboard()
    value = pasteboard.stringForType_(NSPasteboardTypeString)
    if value is None:
        return None
    text = str(value)
    return text if text else None




def add_styled_html_to_pasteboard_preserving_original(styled_html: str, original_markdown: str) -> None:
    """Add Apple HTML format to pasteboard while preserving the original Markdown text.

    Creates a pasteboard item with both styled HTML and plain text representations,
    so rich text apps get formatting while plain text apps get the original.
    """
    from AppKit import NSPasteboard, NSPasteboardTypeString, NSPasteboardTypeHTML

    pasteboard = NSPasteboard.generalPasteboard()

    # Clear and set both formats in a single pasteboard item
    pasteboard.clearContents()

    # Set Apple HTML data (this is the key format that works!)
    pasteboard.setString_forType_(styled_html, 'Apple HTML pasteboard type')
    
    # Also set the standard HTML type for broader compatibility
    pasteboard.setString_forType_(styled_html, NSPasteboardTypeHTML)

    # Set plain text as the original Markdown
    pasteboard.setString_forType_(original_markdown, NSPasteboardTypeString)


class ClipboardPoller:
    """Simple polling helper for the macOS pasteboard change count.

    This avoids heavy event wiring by using `changeCount` and a short polling
    interval. The caller is responsible for the callback logic.
    """

    def __init__(self, interval_seconds: float = 0.3) -> None:
        self.interval_seconds = interval_seconds
        self._stopped = False
        self._last_change_count: Optional[int] = None

    def stop(self) -> None:
        self._stopped = True

    def run(self, on_change: callable[[int], None]) -> None:
        from AppKit import NSPasteboard

        pasteboard = NSPasteboard.generalPasteboard()
        self._last_change_count = int(pasteboard.changeCount())

        while not self._stopped:
            current = int(pasteboard.changeCount())
            if current != self._last_change_count:
                self._last_change_count = current
                on_change(current)
            time.sleep(self.interval_seconds)


