import unittest
import importlib.util
import sys
import types
from unittest.mock import Mock, patch

import requests

bot_module = types.ModuleType("bot")
bot_module.__path__ = []
bot_module.utils = types.SimpleNamespace(clean_file_name=lambda value: value)
player_module = types.ModuleType("bot.player")
player_module.__path__ = []
enums_module = types.ModuleType("bot.player.enums")


class TrackType:
    Default = "default"
    Dynamic = "dynamic"


enums_module.TrackType = TrackType
sys.modules.update(
    {
        "bot": bot_module,
        "bot.player": player_module,
        "bot.player.enums": enums_module,
    }
)
spec = importlib.util.spec_from_file_location(
    "bot.player.track", "bot/player/track.py"
)
track_module = importlib.util.module_from_spec(spec)
sys.modules["bot.player.track"] = track_module
spec.loader.exec_module(track_module)
Track = track_module.Track
_resolve_audio_page = track_module._resolve_audio_page


def response_for(body, content_type="text/html", url="https://example.com/player"):
    response = Mock()
    response.url = url
    response.encoding = "utf-8"
    response.headers = {"Content-Type": content_type}
    response.iter_content.return_value = [body.encode()]
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    return response


class AudioPageTests(unittest.TestCase):
  def test_extracts_nested_source_and_preserves_filename_title(self):
    response = response_for(
        '<audio><source src="/stream.mp3"></audio>',
        url="https://example.com/player.php?file=folder/001-SampleBook.mp3",
    )
    response.raise_for_status = Mock()

    with patch("bot.player.track.requests.get", return_value=response):
        track = Track(url="https://example.com/player.php?file=folder%2F001-SampleBook.mp3")

    self.assertEqual(track.url, "https://example.com/stream.mp3")
    self.assertEqual(track.name, "001-SampleBook")

  def test_decodes_html_entities_in_audio_source(self):
    response = response_for(
        '<audio src="/stream.php?file=a&amp;b.mp3"></audio>',
        url="https://example.com/player?file=book.mp3",
    )
    response.raise_for_status = Mock()

    with patch("bot.player.track.requests.get", return_value=response):
        result = _resolve_audio_page("https://example.com/player?file=book.mp3")

    self.assertEqual(result, ("https://example.com/stream.php?file=a&b.mp3", "book"))

  def test_accepts_direct_audio_without_reading_body(self):
    response = response_for(
        "", content_type="audio/mpeg", url="https://example.com/audio.mp3"
    )
    response.raise_for_status = Mock()
    response.iter_content = Mock(side_effect=AssertionError("body was read"))

    with patch("bot.player.track.requests.get", return_value=response):
        result = _resolve_audio_page(
            "https://example.com/player?file=encoded%20name.mp3"
        )

    self.assertEqual(result, ("https://example.com/audio.mp3", "encoded name"))

  def test_preserves_page_title_when_metadata_updates_name(self):
    response = response_for(
        '<audio src="/stream.mp3"></audio>',
        url="https://example.com/player?file=book.mp3",
    )
    response.raise_for_status = Mock()

    with patch("bot.player.track.requests.get", return_value=response):
        track = Track(url="https://example.com/player?file=book.mp3")

    track.name = "Unrelated metadata title"
    self.assertEqual(track.name, "book")

  def test_falls_back_to_original_url_on_timeout(self):
    self._assert_falls_back(requests.Timeout())

  def test_falls_back_to_original_url_on_invalid_response(self):
    self._assert_falls_back(ValueError("invalid response"))

  def _assert_falls_back(self, exception):
    with patch("bot.player.track.requests.get", side_effect=exception):
      value = "https://example.com/player?file=book.mp3"
      track = Track(url=value)

    self.assertEqual(track.url, value)

  def test_falls_back_when_html_page_is_oversized(self):
    response = response_for(
        "x" * 131073,
        url="https://example.com/player?file=book.mp3",
    )
    response.raise_for_status = Mock()

    with patch("bot.player.track.requests.get", return_value=response):
        value = "https://example.com/player?file=book.mp3"
        track = Track(url=value)

    self.assertEqual(track.url, value)

  def test_does_not_request_unrelated_urls(self):
    with patch("bot.player.track.requests.get") as get:
        value = "https://example.com/about"
        track = Track(url=value)

    get.assert_not_called()
    self.assertEqual(track.url, value)
