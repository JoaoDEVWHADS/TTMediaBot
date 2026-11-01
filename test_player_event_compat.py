import tempfile
import threading
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock
import mpv
from bot.player import Player
from bot.player.enums import State, Mode, TrackType

class EventCompatibilityTests(TestCase):
    def make_player(self):
        p = object.__new__(Player)
        p.track = SimpleNamespace(service='ytm', name='test', type=TrackType.Local,
            _stream_refresh_attempted=False, refresh_stream=Mock(return_value='fresh'))
        p.state = State.Playing
        p.mode = Mode.TrackList
        p.queue = SimpleNamespace(is_empty=True)
        p._player = SimpleNamespace(idle_active=True, metadata=None, media_title=None)
        p._play = Mock()
        p.next = Mock()
        p.stop = Mock()
        return p

    def test_flat_byte_error_retries_once(self):
        p = self.make_player()
        event = {'event': b'end-file', 'reason': b'error'}
        p.on_end_file(event)
        p.on_end_file(event)
        p.track.refresh_stream.assert_called_once()
        p._play.assert_called_once_with('fresh', save_to_recents=False)
        p.next.assert_called_once()

    def test_flat_text_eof_advances(self):
        p = self.make_player()
        p.on_end_file({'event': 'end-file', 'reason': 'eof'})
        p.next.assert_called_once()

    def test_stop_does_not_advance(self):
        p = self.make_player()
        p.on_end_file({'event': b'end-file', 'reason': b'stop'})
        p.next.assert_not_called()

    def test_missing_metadata_preserves_title(self):
        p = self.make_player()
        p.on_metadata_update('metadata', None)
        self.assertEqual(p.track.name, 'test')
        self.assertEqual(p._parse_metadata({'title': None}), '')

    def test_real_mpv_eof_advances_to_second_file(self):
        with tempfile.TemporaryDirectory() as td:
            file = str(Path(td) / 'short.wav')
            with wave.open(file, 'wb') as out:
                out.setnchannels(1); out.setsampwidth(2); out.setframerate(8000)
                out.writeframes(b'\0\0' * 800)
            p = self.make_player()
            p.track.service = 'local'
            backend = mpv.MPV(ao='null', video=False, ytdl=False)
            p._player = backend
            done = threading.Event()
            errors = []
            def next_track():
                if p.next.call_count == 1:
                    backend.play(file)
                else:
                    done.set()
            p.next.side_effect = next_track
            def on_end(event):
                try:
                    p.on_end_file(event)
                except Exception as exc:
                    errors.append(exc); done.set()
            backend.event_callback('end-file')(on_end)
            try:
                backend.play(file)
                self.assertTrue(done.wait(8), 'Two EOF events did not advance')
                self.assertEqual(errors, [])
                self.assertEqual(p.next.call_count, 2)
            finally:
                backend.terminate()
