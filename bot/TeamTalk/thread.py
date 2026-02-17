from __future__ import annotations
from importlib.machinery import SourceFileLoader
import logging
import os
from threading import Thread
import time
from typing import Any, Callable, Optional, Tuple, TYPE_CHECKING
from types import ModuleType


import types
import sys

from bot.TeamTalk.structs import *

if TYPE_CHECKING:
    from bot import Bot
    from bot.TeamTalk import TeamTalk


class TeamTalkThread(Thread):
    def __init__(self, bot: Bot, ttclient: TeamTalk):
        Thread.__init__(self, daemon=True)
        self.name = "TeamTalkThread"
        self.bot = bot
        self.config = ttclient.config
        self.ttclient = ttclient

    def run(self) -> None:
        if self.config.event_handling.load_event_handlers:
            self.event_handlers = self.import_event_handlers()
        self._close = False
        while not self._close:
            event = self.ttclient.get_event(self.ttclient.tt.getMessage())
            if event.event_type == EventType.NONE:
                continue
            elif (
                event.event_type == EventType.ERROR
                and self.ttclient.state == State.CONNECTED
            ):
                self.ttclient.errors_queue.put(event.error)
            elif (
                event.event_type == EventType.SUCCESS
                and self.ttclient.state == State.CONNECTED
            ):
                self.ttclient.event_success_queue.put(event)
            elif (
                event.event_type == EventType.USER_TEXT_MESSAGE
                and event.message.type == MessageType.User
            ):
                self.ttclient.message_queue.put(event.message)
            elif (
                event.event_type == EventType.FILE_NEW
                and event.file.username == self.config.username
                and event.file.channel.id == self.ttclient.channel.id
            ):
                self.ttclient.uploaded_files_queue.put(event.file)
            elif (
                event.event_type == EventType.CON_FAILED
                or event.event_type == EventType.CON_LOST
                or event.event_type == EventType.MYSELF_KICKED
            ):
                if event.event_type == EventType.CON_FAILED:
                    logging.warning("Connection failed")
                elif event.event_type == EventType.CON_LOST:
                    logging.warning("Server lost")
                else:
                    logging.warning("Kicked")
                self.ttclient.disconnect()
                if (
                    self.ttclient.reconnect
                    and self.ttclient.reconnect_attempt
                    < self.config.reconnection_attempts
                    or self.config.reconnection_attempts < 0
                ):
                    self.ttclient.disconnect()
                    time.sleep(self.config.reconnection_timeout)
                    self.ttclient.connect()
                    self.ttclient.reconnect_attempt += 1
                else:
                    logging.error("Connection error")
                    sys.exit(1)
            elif event.event_type == EventType.CON_SUCCESS:
                self.ttclient.reconnect_attempt = 0
                self.ttclient.login()
            elif event.event_type == EventType.ERROR:
                if self.ttclient.flags & Flags.AUTHORIZED == Flags(0):
                    logging.warning("Login failed")
                    if (
                        self.ttclient.reconnect
                        and self.ttclient.reconnect_attempt
                        < self.config.reconnection_attempts
                        or self.config.reconnection_attempts < 0
                    ):
                        time.sleep(self.config.reconnection_timeout)
                        self.ttclient.login()
                    else:
                        logging.error("Login error")
                        sys.exit(1)
                else:
                    logging.warning("Failed to join channel")
                    if (
                        self.ttclient.reconnect
                        and self.ttclient.reconnect_attempt
                        < self.config.reconnection_attempts
                        or self.config.reconnection_attempts < 0
                    ):
                        time.sleep(self.config.reconnection_timeout)
                        self.ttclient.join()
                    else:
                        logging.error("Error joining channel")
                        sys.exit(1)
            elif event.event_type == EventType.MYSELF_LOGGEDIN:
                self.ttclient.user_account = event.user_account
                self.ttclient.reconnect_attempt = 0
                self.ttclient.join()
            elif (
                event.event_type == EventType.SUCCESS
                and self.ttclient.state == State.CONNECTING
            ):
                self.ttclient.reconnect_attempt = 0
                self.ttclient.reconnect = True
                self.ttclient.state = State.CONNECTED
                self.ttclient.change_status_text(self.ttclient.status)
            elif event.event_type == EventType.USER_LEFT:
                # Auto-return logic
                try:
                    # Log event details for debugging
                    logging.debug(f"USER_LEFT event: Source={event.source}, ChannelID={event.channel.id}, BotChannel={self.ttclient.channel.id}, User={event.user.username} ({event.user.id})")

                    # Check if the event happened in the bot's current channel
                    # Check both source and channel object to be safe
                    if event.source == self.ttclient.channel.id or event.channel.id == self.ttclient.channel.id:
                        # Get users in current channel using ctypes
                        users = self.ttclient.tt.getChannelUsers(self.ttclient.channel.id)
                        
                        # Robust counting: Exclude bot itself and the user who just left (if still in list)
                        other_users_count = 0
                        for u in users:
                            # u is a ctypes struct, so we use nUserID
                            # self.ttclient.user is wrapper object, use id
                            if u.nUserID == self.ttclient.user.id:
                                continue
                            if u.nUserID == event.user.id:
                                continue
                            other_users_count += 1
                        
                        logging.debug(f"Auto-return check: Total users={len(users)}, Other users counted={other_users_count}")

                        # Check if no other users remain
                        if other_users_count == 0:
                             logging.info("Auto-return triggered: Bot is alone in channel. returning to default.")
                             # Stop playback if playing
                             from bot.player.enums import State as PlayerState
                             if self.bot.player.state != PlayerState.Stopped:
                                 self.bot.player.stop()
                             
                             # Determine default channel ID
                             default_channel = self.config.channel
                             if isinstance(default_channel, int):
                                 default_channel_id = default_channel
                             else:
                                 # We need _str helper for string conversion
                                 def _str(data):
                                     if isinstance(data, str):
                                         return bytes(data, "utf-8") if os.supports_bytes_environ else data
                                     return str(data, "utf-8")
                                 default_channel_id = self.ttclient.tt.getChannelIDFromPath(_str(default_channel))
                                 if default_channel_id == 0:
                                     default_channel_id = 1
                             
                             # Move back if not already there
                             if self.ttclient.channel.id != default_channel_id:
                                 self.ttclient.move_user(self.ttclient.user.id, default_channel_id)
                except Exception as e:
                    logging.error(f"Error in auto-return logic: {e}")

            if self.config.event_handling.load_event_handlers:
                self.run_event_handler(event)

    def close(self) -> None:
        self._close = True

    def get_function_name_by_event_type(self, event_type: EventType) -> str:
        return f"on_{event_type.name.lower()}"

    def import_event_handlers(self) -> ModuleType:
        try:
            if (
                os.path.isfile(self.config.event_handling.event_handlers_file_name)
                and os.path.splitext(
                    self.config.event_handling.event_handlers_file_name
                )[1]
                == ".py"
            ):
                module = SourceFileLoader(
                    os.path.splitext(
                        self.config.event_handling.event_handlers_file_name
                    )[0],
                    self.config.event_handling.event_handlers_file_name,
                ).load_module()
            elif os.path.isdir(
                self.config.event_handling.event_handlers_file_name
            ) and "__init__.py" in os.listdir(
                self.config.event_handling.event_handlers_file_name
            ):
                module = SourceFileLoader(
                    self.config.event_handling.event_handlers_file_name,
                    self.config.event_handling.event_handlers_file_name
                    + "/__init__.py",
                ).load_module()
            else:
                logging.error(
                    "Incorrect path to event handlers. An empty module will be used"
                )
                module = types.ModuleType("event_handlers")
        except Exception as e:
            logging.error(
                "Can't load specified event handlers. Error: {}. An empty module will be used.".format(
                    e
                )
            )
            module = types.ModuleType("event_handlers")
        return module

    def parse_event(self, event: Event) -> Tuple[Any, ...]:
        if event.event_type in (
            EventType.USER_UPDATE,
            EventType.USER_JOINED,
            EventType.USER_LOGGEDIN,
            EventType.USER_LOGGEDOUT,
        ):
            return (event.user,)
        elif event.event_type == EventType.USER_LEFT:
            return (event.source, event.user)
        elif event.event_type == EventType.USER_TEXT_MESSAGE:
            return (event.message,)
        elif event.event_type in (
            EventType.CHANNEL_NEW,
            EventType.CHANNEL_UPDATE,
            EventType.CHANNEL_REMOVE,
        ):
            return (event.channel,)
        elif event.event_type in (
            EventType.FILE_NEW,
            EventType.FILE_REMOVE,
        ):
            return (event.file,)
        else:
            return (1, 2)

    def run_event_handler(self, event: Event) -> None:
        try:
            event_handler: Optional[Callable[..., None]] = getattr(
                self.event_handlers,
                self.get_function_name_by_event_type(event.event_type),
                None,
            )
            if not event_handler:
                return
            try:
                event_handler(*self.parse_event(event), self.bot)
            except Exception as e:
                print("Error in event handling {}".format(e))
        except AttributeError:
            self.event_handlers = self.import_event_handlers()
            self.run_event_handler(event)
