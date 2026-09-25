#!/usr/bin/env python3
"""Unit tests for the transient-vs-fatal fetch retry logic in source_pipeline.py."""

from __future__ import annotations

import io
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

import source_pipeline


class IsRetryableTests(unittest.TestCase):
    def test_retryable_http_statuses(self) -> None:
        for status in source_pipeline.RETRYABLE_HTTP_STATUSES:
            error = urllib.error.HTTPError("https://example.invalid", status, "boom", {}, None)
            self.assertTrue(source_pipeline._is_retryable(error), f"status {status} should be retryable")

    def test_non_retryable_http_status(self) -> None:
        error = urllib.error.HTTPError("https://example.invalid", 404, "not found", {}, None)
        self.assertFalse(source_pipeline._is_retryable(error))

    def test_url_error_is_retryable(self) -> None:
        self.assertTrue(source_pipeline._is_retryable(urllib.error.URLError("connection reset")))

    def test_connection_error_is_retryable(self) -> None:
        self.assertTrue(source_pipeline._is_retryable(ConnectionResetError("reset")))

    def test_timeout_is_retryable(self) -> None:
        self.assertTrue(source_pipeline._is_retryable(TimeoutError("timed out")))

    def test_value_error_is_not_retryable(self) -> None:
        # A checksum mismatch (ValueError) must never be retried: retrying
        # cannot change whether the bytes match the recorded hash.
        self.assertFalse(source_pipeline._is_retryable(ValueError("SHA-512 mismatch")))


class FetchRetryTests(unittest.TestCase):
    def test_succeeds_after_transient_failures(self) -> None:
        attempts: list[int] = []

        def urlopen_side_effect(request, timeout=60):
            attempts.append(1)
            if len(attempts) < 3:
                raise urllib.error.HTTPError(request.full_url, 502, "bad gateway", {}, None)
            handle = mock.MagicMock()
            handle.__enter__.return_value = io.BytesIO(b"payload")
            handle.__exit__.return_value = False
            return handle

        with mock.patch("source_pipeline.urllib.request.urlopen", side_effect=urlopen_side_effect):
            with mock.patch("source_pipeline.time.sleep") as sleep:
                destination = mock.MagicMock(spec=Path)
                handle = mock.MagicMock()
                handle.__enter__.return_value = io.BytesIO()
                handle.__exit__.return_value = False
                destination.open.return_value = handle
                with mock.patch("source_pipeline.shutil.copyfileobj") as copy:
                    source_pipeline.fetch("https://example.invalid/file", destination)
                    self.assertEqual(copy.call_count, 1)
                self.assertEqual(len(attempts), 3)
                self.assertEqual(sleep.call_count, 2)

    def test_gives_up_after_max_retries_on_transient_error(self) -> None:
        with mock.patch("source_pipeline.urllib.request.urlopen") as urlopen:
            urlopen.side_effect = urllib.error.URLError("connection reset")
            with mock.patch("source_pipeline.time.sleep"):
                destination = mock.MagicMock(spec=Path)
                with self.assertRaises(urllib.error.URLError):
                    source_pipeline.fetch("https://example.invalid/file", destination, retries=3)
                self.assertEqual(urlopen.call_count, 3)

    def test_does_not_retry_non_transient_error(self) -> None:
        with mock.patch("source_pipeline.urllib.request.urlopen") as urlopen:
            urlopen.side_effect = urllib.error.HTTPError("https://example.invalid", 404, "not found", {}, None)
            with mock.patch("source_pipeline.time.sleep") as sleep:
                destination = mock.MagicMock(spec=Path)
                with self.assertRaises(urllib.error.HTTPError):
                    source_pipeline.fetch("https://example.invalid/file", destination, retries=3)
                self.assertEqual(urlopen.call_count, 1)
                sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
