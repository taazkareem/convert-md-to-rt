from __future__ import annotations

import argparse
import hashlib
import logging
import signal
import sys
from typing import Optional

from .detector import is_markdown
from .converter import markdown_to_styled_html_and_text
from .clipboard import (
    ClipboardPoller,
    read_plain_text_from_pasteboard,
    add_styled_html_to_pasteboard_preserving_original,
)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_watcher(interval: float = 0.3, dry_run: bool = False) -> None:
    """Start a loop that watches the clipboard and converts Markdown to styled HTML."""
    log = logging.getLogger("md2rt")
    last_processed_hash: Optional[str] = None

    def on_change(_change_count: int) -> None:
        nonlocal last_processed_hash
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
        except Exception as exc:  # noqa: BLE001 - top-level boundary
            log.exception("Conversion failed: %s", exc)
            # Do not update last_processed_hash here; allow retry on next copy.
            return

        if dry_run:
            log.info("[dry-run] Would add styled HTML to clipboard (%d chars), preserving original Markdown", len(styled_html))
        else:
            add_styled_html_to_pasteboard_preserving_original(styled_html, text)
            log.info("Added styled HTML to clipboard (%d chars), preserving original Markdown", len(styled_html))

        last_processed_hash = _hash_text(text)

    poller = ClipboardPoller(interval)

    def handle_sigint(_signum, _frame):
        poller.stop()

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        poller.run(on_change)
    finally:
        poller.stop()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Convert Markdown clipboard text to styled HTML")
    parser.add_argument("--interval", type=float, default=0.3, help="Polling interval in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Do not modify clipboard; log only")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, ...)")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        run_watcher(interval=args.interval, dry_run=args.dry_run)
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as exc:  # noqa: BLE001 - top-level CLI boundary
        logging.getLogger("md2rt").exception("Unhandled error: %s", exc)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


