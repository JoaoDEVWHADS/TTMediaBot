from __future__ import annotations
import os
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from bot.translator import Translator

app_name = "TTMediaBot"
app_version = "4.0"
client_name = app_name + "-V" + app_version
about_text: Callable[[Translator], str] = lambda translator: translator.translate(
    """\
Hello! I am João Almeida. This is my fork of TTMediaBot for TeamTalk 5.
This repository focuses on stability and support for YouTube Music.
Repository: https://github.com/JoaoDEVWHADS/TTMediaBot
Original Authors: Amir Gumerov, Vladislav Kopylov, Beqa Gozalishvili, Kirill Belousov.
"""
)
fallback_service = "yt"
loop_timeout = 0.01
max_message_length = 256
recents_max_lenth = 32
tt_event_timeout = 2

directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
