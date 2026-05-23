from __future__ import annotations
import logging
import os
import tempfile
import zipfile
from typing import List, Optional, TYPE_CHECKING

from bot.commands.command import Command
from bot.player.enums import Mode, State, TrackType
from bot.TeamTalk.structs import User, UserRight
from bot import errors, app_vars, utils

if TYPE_CHECKING:
    from bot.TeamTalk.structs import User


class HelpCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate("Shows command help")

    def __call__(self, arg: str, user: User) -> Optional[str]:
        return self.command_processor.help(arg, user)


class AboutCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate("Shows information about the bot")

    def __call__(self, arg: str, user: User) -> Optional[str]:
        return app_vars.client_name + "\n" + app_vars.about_text(self.translator)


class PlayPauseCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "QUERY Plays tracks found for the query. If no query is given, plays or pauses current track. When search results mode (sr) is active, shows a numbered list instead"
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if arg:
            self.run_async(
                self.ttclient.send_message,
                self.translator.translate("Searching..."),
                user,
            )
            try:
                # Search results mode: request more results from the service directly
                if self.config.general.search_results_mode:
                    count = self.command_processor.search_results_count
                    track_list = self.service_manager.service.search(arg, limit=count)
                    self.command_processor.pending_search_results[user.id] = track_list
                    lines = [self.translator.translate("Search results:")]
                    for i, track in enumerate(track_list):
                        lines.append(f"{i + 1}: {track.name}")
                    lines.append(self.translator.translate("Use 'sl NUMBER' to select a track"))
                    return "\n".join(lines)

                # Normal mode: request only 1 result and play immediately
                track_list = self.service_manager.service.search(arg)
                if self.config.general.send_channel_messages:
                    self.run_async(
                        self.ttclient.send_message,
                        self.translator.translate(
                            "{nickname} requested {request}"
                        ).format(nickname=user.nickname, request=arg),
                        type=2,
                    )
                self.run_async(self.player.play, track_list)
                return self.translator.translate("Playing {}").format(
                    track_list[0].name
                )
            except errors.NothingFoundError:
                return self.translator.translate("Nothing is found for your query")
            except errors.ServiceError:
                return self.translator.translate(
                    "The selected service is currently unavailable"
                )
        else:
            if self.player.state == State.Playing:
                self.run_async(self.player.pause)
            elif self.player.state == State.Paused:
                self.run_async(self.player.play)


class PlayUrlCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate("URL Plays a stream from a given URL")

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if arg:
            try:
                tracks = self.module_manager.streamer.get(arg, user.is_admin)
                if self.config.general.send_channel_messages:
                    self.run_async(
                        self.ttclient.send_message,
                        self.translator.translate(
                            "{nickname} requested playing from a URL"
                        ).format(nickname=user.nickname),
                        type=2,
                    )
                self.run_async(self.player.play, tracks)
            except errors.IncorrectProtocolError:
                return self.translator.translate("Incorrect protocol")
            except errors.ServiceError:
                return self.translator.translate("Cannot process stream URL")
            except errors.PathNotFoundError:
                return self.translator.translate("The path cannot be found")
        else:
            raise errors.InvalidArgumentError


class StopCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate("Stops playback")

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if self.player.state != State.Stopped:
            self.player.stop()
            if self.config.general.send_channel_messages:
                self.ttclient.send_message(
                    self.translator.translate("{nickname} stopped playback").format(
                        nickname=user.nickname
                    ),
                    type=2,
                )
        else:
            return self.translator.translate("Nothing is playing")


class VolumeCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "VOLUME Sets the volume to a value between 0 and {max_volume}. If no volume is specified, the current volume level is displayed"
        ).format(max_volume=self.config.player.max_volume)

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if arg:
            try:
                volume = int(arg)
                if 0 <= volume <= self.config.player.max_volume:
                    self.player.set_volume(int(arg))
                else:
                    raise ValueError
            except ValueError:
                raise errors.InvalidArgumentError
        else:
            return str(self.player.volume)


class SeekBackCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "STEP Seeks current track backward. the default step is {seek_step} seconds"
        ).format(seek_step=self.config.player.seek_step)

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if self.player.state == State.Stopped:
            return self.translator.translate("Nothing is playing")
        if arg:
            try:
                self.player.seek_back(float(arg))
            except ValueError:
                raise errors.InvalidArgumentError
        else:
            self.player.seek_back()


class SeekForwardCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "STEP Seeks current track forward. the default step is {seek_step} seconds"
        ).format(seek_step=self.config.player.seek_step)

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if self.player.state == State.Stopped:
            return self.translator.translate("Nothing is playing")
        if arg:
            try:
                self.player.seek_forward(float(arg))
            except ValueError:
                raise errors.InvalidArgumentError
        else:
            self.player.seek_forward()


class NextTrackCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate("Plays next track")

    def __call__(self, arg: str, user: User) -> Optional[str]:
        try:
            self.player.next()
            return self.translator.translate("Playing {}").format(
                self.player.track.name
            )
        except errors.NoNextTrackError:
            return self.translator.translate("No next track")
        except errors.NothingIsPlayingError:
            return self.translator.translate("Nothing is playing")


class PreviousTrackCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate("Plays previous track")

    def __call__(self, arg: str, user: User) -> Optional[str]:
        try:
            self.player.previous()
            return self.translator.translate("Playing {}").format(
                self.player.track.name
            )
        except errors.NoPreviousTrackError:
            return self.translator.translate("No previous track")
        except errors.NothingIsPlayingError:
            return self.translator.translate("Nothing is playing")


class ModeCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "MODE Sets the playback mode. If no mode is specified, the current mode and a list of modes are displayed"
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        self.mode_names = {
            Mode.SingleTrack: self.translator.translate("Single Track"),
            Mode.RepeatTrack: self.translator.translate("Repeat Track"),
            Mode.TrackList: self.translator.translate("Track list"),
            Mode.RepeatTrackList: self.translator.translate("Repeat track list"),
            Mode.Random: self.translator.translate("Random"),
        }
        mode_help = self.translator.translate(
            "Current mode: {current_mode}\n{modes}"
        ).format(
            current_mode=self.mode_names[self.player.mode],
            modes="\n".join(
                [
                    "{value} {name}".format(name=self.mode_names[i], value=i.value)
                    for i in Mode.__members__.values()
                ]
            ),
        )
        if arg:
            try:
                mode = Mode(arg.lower())
                if mode == Mode.Random:
                    self.player.shuffle(True)
                if self.player.mode == Mode.Random and mode != Mode.Random:
                    self.player.shuffle(False)
                self.player.mode = Mode(mode)
                return self.translator.translate("Current mode: {mode}").format(
                    mode=self.mode_names[self.player.mode]
                )
            except ValueError:
                return self.translator.translate("Incorrect mode") + "\n" + mode_help
        else:
            return mode_help


class ServiceCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "SERVICE Selects the service to play from, sv SERVICE h returns additional help. If no service is specified, the current service and a list of available services are displayed"
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        args = arg.split(" ")
        if args[0]:
            service_name = args[0].lower()
            if service_name not in self.service_manager.services:
                return self.translator.translate("Unknown service.\n{}").format(
                    self.service_help
                )
            service = self.service_manager.services[service_name]
            if len(args) == 1:
                if not service.hidden and service.is_enabled:
                    self.service_manager.service = service
                    if service.warning_message:
                        return self.translator.translate(
                            "Current service: {}\nWarning: {}"
                        ).format(service.name, service.warning_message)
                    return self.translator.translate("Current service: {}").format(
                        service.name
                    )
                elif not service.is_enabled:
                    if service.error_message:
                        return self.translator.translate(
                            "Error: {error}\n{service} is disabled".format(
                                error=service.error_message,
                                service=service.name,
                            )
                        )
                    else:
                        return self.translator.translate(
                            "{service} is disabled".format(service=service.name)
                        )
            elif len(args) >= 1:
                if service.help:
                    return service.help
                else:
                    return self.translator.translate(
                        "This service has no additional help"
                    )
        else:
            return self.service_help

    @property
    def service_help(self):
        services: List[str] = []
        for i in self.service_manager.services:
            service = self.service_manager.services[i]
            if not service.is_enabled:
                if service.error_message:
                    services.append(
                        "{} (Error: {})".format(service.name, service.error_message)
                    )
                else:
                    services.append(
                        self.translator.translate("{} (Error)").format(service.name)
                    )
            elif service.warning_message:
                services.append(
                    self.translator.translate("{} (Warning: {})").format(
                        service.name, service.warning_message
                    )
                )
            else:
                services.append(service.name)
        help = self.translator.translate(
            "Current service: {current_service}\nAvailable:\n{available_services}\nsend sv SERVICE h for additional help"
        ).format(
            current_service=self.service_manager.service.name,
            available_services="\n".join(services),
        )
        return help


class SelectTrackCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "NUMBER Selects track by number from the list of current results"
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if arg:
            try:
                number = int(arg)
                if number > 0:
                    index = number - 1
                elif number < 0:
                    index = number
                else:
                    return self.translator.translate("Incorrect number")
                self.player.play_by_index(index)
                return self.translator.translate("Playing {} {}").format(
                    arg, self.player.track.name
                )
            except errors.IncorrectTrackIndexError:
                return self.translator.translate("Out of list")
            except errors.NothingIsPlayingError:
                return self.translator.translate("Nothing is playing")
            except ValueError:
                raise errors.InvalidArgumentError
        else:
            if self.player.state != State.Stopped:
                return self.translator.translate("Playing {} {}").format(
                    self.player.track_index + 1, self.player.track.name
                )
            else:
                return self.translator.translate("Nothing is playing")


class SpeedCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "SPEED Sets playback speed from 0.25 to 4. If no speed is given, shows current speed"
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if not arg:
            return self.translator.translate("Current rate: {}").format(
                str(self.player.get_speed())
            )
        else:
            try:
                self.player.set_speed(float(arg))
            except ValueError:
                raise errors.InvalidArgumentError()


class FavoritesCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "+/-NUMBER Manages favorite tracks. + adds the current track to favorites. - removes a track requested from favorites. If a number is specified after +/-, adds/removes a track with that number"
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if user.username == "":
            return self.translator.translate(
                "This command is not available for guest users"
            )
        if arg:
            if arg[0] == "+":
                return self._add(user)
            elif arg[0] == "-":
                return self._del(arg, user)
            else:
                return self._play(arg, user)
        else:
            return self._list(user)

    def _add(self, user: User) -> str:
        if self.player.state != State.Stopped:
            if user.username in self.cache.favorites:
                self.cache.favorites[user.username].append(self.player.track.get_raw())
            else:
                self.cache.favorites[user.username] = [self.player.track.get_raw()]
            self.cache_manager.save()
            return self.translator.translate("Added")
        else:
            return self.translator.translate("Nothing is playing")

    def _del(self, arg: str, user: User) -> str:
        if (self.player.state != State.Stopped and len(arg) == 1) or len(arg) > 1:
            try:
                if len(arg) == 1:
                    self.cache.favorites[user.username].remove(self.player.track)
                else:
                    del self.cache.favorites[user.username][int(arg[1::]) - 1]
                self.cache_manager.save()
                return self.translator.translate("Deleted")
            except IndexError:
                return self.translator.translate("Out of list")
            except ValueError:
                if not arg[1::].isdigit:
                    return self.help
                return self.translator.translate("This track is not in favorites")
        else:
            return self.translator.translate("Nothing is playing")

    def _list(self, user: User) -> str:
        track_names: List[str] = []
        try:
            for number, track in enumerate(self.cache.favorites[user.username]):
                track_names.append(
                    self.translator.translate("{number}: {track_name}").format(
                        number=number + 1,
                        track_name=track.name if track.name else track.url,
                    )
                )
        except KeyError:
            pass
        if len(track_names) > 0:
            return "\n".join(track_names)
        else:
            return self.translator.translate("The list is empty")

    def _play(self, arg: str, user: User) -> Optional[str]:
        try:
            self.player.play(
                self.cache.favorites[user.username], start_track_index=int(arg) - 1
            )
        except ValueError:
            raise errors.InvalidArgumentError()
        except IndexError:
            return self.translator.translate("Out of list")
        except KeyError:
            return self.translator.translate("The list is empty")


class GetLinkCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate("Gets a direct link to the current track")

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if self.player.state != State.Stopped:
            url = self.player.track.url
            if url:
                shortener = self.module_manager.shortener
                return shortener.get(url) if shortener else url
            else:
                return self.translator.translate("URL is not available")
        else:
            return self.translator.translate("Nothing is playing")


class RecentsCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "NUMBER Plays a track with  the given number from a list of recent tracks. Without a number shows recent tracks"
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if arg:
            try:
                self.player.play(
                    list(reversed(list(self.cache.recents))),
                    start_track_index=int(arg) - 1,
                )
            except ValueError:
                raise errors.InvalidArgumentError()
            except IndexError:
                return self.translator.translate("Out of list")
        else:
            track_names: List[str] = []
            for number, track in enumerate(reversed(self.cache.recents)):
                if track.name:
                    track_names.append(
                        self.translator.translate("{number}: {track_name}").format(
                            number=number + 1, track_name=track.name
                        )
                    )
                else:
                    track_names.append(
                        self.translator.translate("{number}: {track_url}").format(
                            number=number + 1, track_url=track.url
                        )
                    )
            return (
                "\n".join(track_names)
                if track_names
                else self.translator.translate("The list is empty")
            )


class DownloadCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "Downloads the current track and uploads it to the channel."
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if self.player.state != State.Stopped:
            track = self.player.track
            if track.url and (
                track.type == TrackType.Default or track.type == TrackType.Local
            ):
                self.module_manager.uploader(self.player.track, user)
                return self.translator.translate("Downloading...")
            else:
                return self.translator.translate("Live streams cannot be downloaded")
        else:
            return self.translator.translate("Nothing is playing")


class DownloadVideoCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "Downloads the current track as video and uploads it to the channel."
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if self.player.state != State.Stopped:
            track = self.player.track
            if track.url and (
                track.type == TrackType.Default or track.type == TrackType.Local
            ):
                self.module_manager.uploader(self.player.track, user, video=True)
                return self.translator.translate("Downloading video...")
            else:
                return self.translator.translate("Live streams cannot be downloaded")
        else:
            return self.translator.translate("Nothing is playing")


class JoinChannelCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate("Makes the bot join your current channel")

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if self.player.state != State.Stopped:
            self.player.stop()

        user_channel = user.channel

        try:
            cmd = self.ttclient.move_user(self.ttclient.user.id, user_channel.id)

            import time
            from bot import app_vars
            from queue import Empty

            start_time = time.time()
            while time.time() - start_time < 5:
                try:
                    event = self.ttclient.event_success_queue.get_nowait()
                    if event.source == cmd:
                        self._bot.jc_requested_by_user_id = user.id
                        return self.translator.translate("Joining channel: {}").format(user_channel.name)
                    else:
                        self.ttclient.event_success_queue.put(event)
                except Empty:
                    pass

                try:
                    error = self.ttclient.errors_queue.get_nowait()
                    if error.command_id == cmd:
                        return self.translator.translate("Failed to join channel. Error: {}").format(error.message)
                    else:
                        self.ttclient.errors_queue.put(error)
                except Empty:
                    pass
                time.sleep(app_vars.loop_timeout)

            self._bot.jc_requested_by_user_id = user.id
            return self.translator.translate("Joining channel: {}").format(user_channel.name)

        except Exception as e:
            return self.translator.translate("Failed to join channel: {}").format(str(e))


class DownloadPlaylistCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "Downloads all tracks from a playlist/album URL, zips them, and uploads to the channel."
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if not arg:
            # Check if there's an active download for this user
            status = self.module_manager.playlist_uploader.get_status(user.id)
            if status:
                return self.translator.translate("Current progress: {}").format(status)
            
            # Set state to wait for link from this user
            self.command_processor.pending_playlist_download[user.id] = True
            return self.translator.translate("Please send the link to the playlist or album.")

        self.run_async(self._process, arg, user)
        return self.translator.translate("Searching...")

    def _process(self, arg: str, user: User):
        try:
            tracks = self.module_manager.streamer.get(arg, user.is_admin)
            
            if not tracks:
                self.ttclient.send_message(
                    self.translator.translate("Nothing is found for your query"),
                    user
                )
                return

            if len(tracks) == 1 and not (arg.startswith("http") and ("playlist" in arg or "album" in arg or "list=" in arg)):
                # If it's just a single track and not explicitly a playlist/album link
                self.ttclient.send_message(
                    self.translator.translate("This command is for playlists and albums. For single tracks, use 'dl'."),
                    user
                )
                return

            # Try to get playlist title and artist with more aggressive detection
            playlist_name = "Playlist"
            artist_name = ""
            is_official_album = arg.startswith("http") and "list=OLAK" in arg
            found_album_metadata = False
            
            try:
                # 1. Look for metadata in ALL tracks
                for t in tracks:
                    info = t.extra_info if t.extra_info else {}
                    
                    # Try to find playlist/album title
                    if not found_album_metadata or playlist_name == "Playlist":
                        if "album" in info and info["album"]:
                            playlist_name = info["album"]
                            found_album_metadata = True
                        elif "playlist_title" in info and info["playlist_title"]:
                            playlist_name = info["playlist_title"]
                        elif "playlist" in info and info["playlist"]:
                            playlist_name = info["playlist"]
                    
                    # Try to find artist name
                    if not artist_name:
                        artist_name = info.get("artist") or info.get("album_artist") or info.get("uploader") or info.get("playlist_uploader")
                    
                    # If we have a playlist title and it's not an official album, 
                    # we don't need to look further for artist unless we want to be sure
                    if found_album_metadata and artist_name and is_official_album:
                        break

                # 2. Cleanup: If playlist_name still starts with "Album - ", clean it
                if playlist_name.startswith("Album - "):
                    playlist_name = playlist_name.replace("Album - ", "", 1)
                    found_album_metadata = True

            except Exception as e:
                logging.error(f"Error extracting playlist metadata: {e}")
                pass

            # Final naming logic
            final_zip_name = playlist_name
            
            # RULE: Only add artist if it is an official album (OLAK) 
            # OR if metadata explicitly identified it as an album and we have an artist
            if (is_official_album or (found_album_metadata and "album" in arg.lower())) and artist_name:
                if artist_name.lower() not in playlist_name.lower():
                    final_zip_name = f"{playlist_name} - {artist_name}"

            logging.info(f"PlaylistUploader determined name: {final_zip_name} (Official Album: {is_official_album})")
            self.module_manager.playlist_uploader(tracks, user, final_zip_name)
        except errors.ServiceError as e:
            self.ttclient.send_message(
                self.translator.translate("Error: {}").format(str(e)),
                user
            )
        except Exception as e:
            logging.error(f"DLP Error: {e}", exc_info=True)
            self.ttclient.send_message(
                self.translator.translate("Error: {}").format(str(e)),
                user
            )

# ===========================================================================
# COMANDOS DE FILA
# ===========================================================================

class QueueAddCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "QUERY Searches for a track and adds it to the queue. If nothing is playing, starts immediately"
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if not arg:
            raise errors.InvalidArgumentError()

        self.run_async(
            self.ttclient.send_message,
            self.translator.translate("Searching..."),
            user,
        )

        try:
            track_list = self.service_manager.service.search(arg)
        except errors.NothingFoundError:
            return self.translator.translate("Nothing is found for your query")
        except errors.ServiceError:
            return self.translator.translate(
                "The selected service is currently unavailable"
            )

        track = track_list[0]

        # Se nada está tocando, inicia imediatamente
        if self.player.state == State.Stopped:
            self.run_async(self.player.play, [track])
            return self.translator.translate("Playing {}").format(track.name)

        # Caso contrário, enfileira
        position = self.player.queue.add(track)

        if self.config.general.send_channel_messages:
            self.run_async(
                self.ttclient.send_message,
                self.translator.translate(
                    "{nickname} added to queue: {track}"
                ).format(nickname=user.nickname, track=track.name),
                type=2,
            )

        return self.translator.translate(
            "Added to queue [{position}]: {track}"
        ).format(position=position, track=track.name)


class QueueListCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate("Lists all tracks in the queue")

    def __call__(self, arg: str, user: User) -> Optional[str]:
        tracks = self.player.queue.list_tracks()

        if not tracks:
            return self.translator.translate("The queue is empty")

        lines: List[str] = []
        for i, track in enumerate(tracks):
            name = track.name if track.name else track._url
            lines.append(f"{i + 1}: {name}")

        header = self.translator.translate(
            "Queue ({count} track(s)):"
        ).format(count=len(tracks))

        return header + "\n" + "\n".join(lines)


class QueueRemoveCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "NUMBER Removes track number NUMBER from the queue"
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if not arg:
            raise errors.InvalidArgumentError()

        try:
            number = int(arg)
        except ValueError:
            raise errors.InvalidArgumentError()

        if number < 1:
            raise errors.InvalidArgumentError()

        index = number - 1
        tracks = self.player.queue.list_tracks()

        if index >= len(tracks):
            return self.translator.translate("Out of list")

        track_name = tracks[index].name if tracks[index].name else tracks[index]._url
        self.player.queue.remove(index)

        return self.translator.translate(
            "Removed from queue: {track}"
        ).format(track=track_name)


class QueueClearCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate("Clears the entire queue")

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if self.player.queue.is_empty:
            return self.translator.translate("The queue is already empty")

        self.player.queue.clear()
        return self.translator.translate("Queue cleared")


class QueueSkipCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "Skips current track and plays the next one from the queue. Falls back to normal next if queue is empty"
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if self.player.state == State.Stopped:
            return self.translator.translate("Nothing is playing")

        # Tenta a fila primeiro
        if not self.player.queue.is_empty:
            next_track_name = self.player.queue.peek_next().name
            self.run_async(self.player.play_from_queue)
            return self.translator.translate("Playing next from queue: {}").format(
                next_track_name
            )

        # Fila vazia — comportamento normal de 'n'
        try:
            self.player.next()
            return self.translator.translate("Playing {}").format(
                self.player.track.name
            )
        except errors.NoNextTrackError:
            return self.translator.translate("No next track")


# ===========================================================================
# MODO DE RESULTADOS DE BUSCA
# ===========================================================================

class SearchResultsCommand(Command):
    """sr — toggle do modo de resultados de busca (salvo no config.json via 'sc')."""

    @property
    def help(self) -> str:
        return self.translator.translate(
            "Toggles search results mode. When active, 'p QUERY' shows a numbered list. Use 'sr on' or 'sr off' to set explicitly. Save permanently with 'sc'"
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        arg = arg.strip().lower()

        if arg in ("on", "1", "yes", "true"):
            self.config.general.search_results_mode = True
            return self.translator.translate("Search results mode: ON")

        elif arg in ("off", "0", "no", "false"):
            self.config.general.search_results_mode = False
            return self.translator.translate("Search results mode: OFF")

        elif arg == "":
            # Toggle
            self.config.general.search_results_mode = not self.config.general.search_results_mode
            if self.config.general.search_results_mode:
                return self.translator.translate("Search results mode: ON")
            else:
                return self.translator.translate("Search results mode: OFF")

        else:
            raise errors.InvalidArgumentError


class SelectSearchResultCommand(Command):
    """sl NUMBER — seleciona e toca o resultado N da última busca (volátil por usuário)."""

    @property
    def help(self) -> str:
        return self.translator.translate(
            "NUMBER Selects and plays result NUMBER from the last search list (requires search results mode to be active)"
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if not arg:
            raise errors.InvalidArgumentError

        try:
            number = int(arg.strip())
        except ValueError:
            raise errors.InvalidArgumentError

        if number < 1:
            raise errors.InvalidArgumentError

        results = self.command_processor.pending_search_results.get(user.id)

        if not results:
            return self.translator.translate(
                "No search results available. Use 'p QUERY' to search first"
            )

        if number > len(results):
            return self.translator.translate("Out of list")

        track = results[number - 1]
        # Clear pending results after selection
        del self.command_processor.pending_search_results[user.id]

        if self.config.general.send_channel_messages:
            self.run_async(
                self.ttclient.send_message,
                self.translator.translate(
                    "{nickname} selected: {track}"
                ).format(nickname=user.nickname, track=track.name),
                type=2,
            )

        self.run_async(self.player.play, [track])
        return self.translator.translate("Playing {}").format(track.name)


class SearchResultsCountCommand(Command):
    """slc NUMBER — configura quantidade de resultados exibidos (volátil, padrão 5)."""

    _MIN = 1

    @property
    def help(self) -> str:
        return self.translator.translate(
            "NUMBER Sets how many results are shown when search results mode is active. Without a number shows current count. Resets to 5 on restart"
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if not arg:
            return self.translator.translate(
                "Search results count: {count}"
            ).format(count=self.command_processor.search_results_count)

        try:
            count = int(arg.strip())
        except ValueError:
            raise errors.InvalidArgumentError

        if count < self._MIN:
            return self.translator.translate(
                "Invalid count. Please enter a number greater than 0"
            )

        self.command_processor.search_results_count = count
        return self.translator.translate(
            "Search results count set to {count}"
        ).format(count=count)


class AddLinkCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "LINK Adds a link to the download list."
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if not arg:
            raise errors.InvalidArgumentError()

        link = arg.strip()
        if user.id not in self.command_processor.download_links:
            self.command_processor.download_links[user.id] = []

        self.command_processor.download_links[user.id].append(link)
        return self.translator.translate("Added link to the list. Total: {count}").format(
            count=len(self.command_processor.download_links[user.id])
        )


class AddMultipleLinksCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "LINK1 LINK2 ... Adds multiple space-separated links to the download list."
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if not arg:
            raise errors.InvalidArgumentError()

        links = [l.strip() for l in arg.split(" ") if l.strip()]
        if not links:
            raise errors.InvalidArgumentError()

        if user.id not in self.command_processor.download_links:
            self.command_processor.download_links[user.id] = []

        self.command_processor.download_links[user.id].extend(links)
        return self.translator.translate("Added {added_count} links. Total list size: {count}").format(
            added_count=len(links),
            count=len(self.command_processor.download_links[user.id])
        )


class ListLinksCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "Lists all links in the download list."
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        links = self.command_processor.download_links.get(user.id, [])
        if not links:
            return self.translator.translate("The list is empty")

        lines = []
        for i, link in enumerate(links):
            lines.append(f"{i + 1}: {link}")

        return "\n".join(lines)


class RemoveLinkCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "NUMBER_OR_LINK Removes a link from the download list by its index or URL."
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if not arg:
            raise errors.InvalidArgumentError()

        links = self.command_processor.download_links.get(user.id, [])
        if not links:
            return self.translator.translate("The list is empty")

        removed_link = None
        # Try to parse index
        try:
            index = int(arg.strip())
            if index < 1 or index > len(links):
                return self.translator.translate("Out of list")
            removed_link = links.pop(index - 1)
        except ValueError:
            # Match by URL string
            target = arg.strip()
            if target in links:
                links.remove(target)
                removed_link = target
            else:
                return self.translator.translate("Link not found in the list")

        return self.translator.translate("Removed link: {link}").format(link=removed_link)


class DownloadDirectCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "LINK Downloads a link directly and uploads it to the channel."
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        if not arg:
            raise errors.InvalidArgumentError()

        self.run_async(self._process, arg, user)
        return self.translator.translate("Searching and downloading...")

    def _process(self, arg: str, user: User) -> None:
        try:
            tracks = self.module_manager.streamer.get(arg, user.is_admin)
            if not tracks:
                self.ttclient.send_message(
                    self.translator.translate("Nothing is found for your query"),
                    user
                )
                return

            for track in tracks:
                self.module_manager.uploader.run(track, user)
        except Exception as e:
            self.ttclient.send_message(
                self.translator.translate("Error: {}").format(str(e)),
                user
            )


class DownloadListCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "Downloads all links in your list and uploads them to the channel. Can download normally or as a ZIP archive."
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        links = self.command_processor.download_links.get(user.id, [])
        if not links:
            return self.translator.translate("The list is empty")

        arg = arg.strip()
        if not arg:
            self.command_processor.pending_ads_option[user.id] = True
            return self.translator.translate(
                "How do you want to download these links?\n"
                "1. Download individually (Normal)\n"
                "2. Compress all into a ZIP file\n"
                "Respond only with 1 or 2."
            )

        if arg == "1":
            links_copy = list(links)
            self.command_processor.download_links[user.id] = []
            if self.command_processor.adsc_enabled:
                self.run_async(self._process_normal_local, links_copy, user)
                return self.translator.translate("Starting local download of {count} links...").format(count=len(links_copy))
            else:
                self.run_async(self._process_normal, links_copy, user)
                return self.translator.translate("Starting download of {count} links...").format(count=len(links_copy))
        elif arg == "2":
            links_copy = list(links)
            self.command_processor.download_links[user.id] = []
            if self.command_processor.adsc_enabled:
                self.run_async(self._process_zip_local, links_copy, user)
                return self.translator.translate("Resolving and zipping locally {count} links...").format(count=len(links_copy))
            else:
                self.run_async(self._process_zip, links_copy, user)
                return self.translator.translate("Resolving and zipping {count} links...").format(count=len(links_copy))
        else:
            return self.translator.translate("Invalid option. Please send 'ads' again to select.")

    def _process_normal(self, links: List[str], user: User) -> None:
        for i, link in enumerate(links):
            try:
                self.ttclient.send_message(
                    self.translator.translate("Processing link {number}/{total}: {link}").format(
                        number=i + 1, total=len(links), link=link
                    ),
                    user
                )
                tracks = self.module_manager.streamer.get(link, user.is_admin)
                if not tracks:
                    self.ttclient.send_message(
                        self.translator.translate("Nothing is found for: {link}").format(link=link),
                        user
                    )
                    continue

                for track in tracks:
                    self.module_manager.uploader.run(track, user)
            except Exception as e:
                self.ttclient.send_message(
                    self.translator.translate("Error downloading {link}: {error}").format(
                        link=link, error=str(e)
                    ),
                    user
                )

    def _process_normal_local(self, links: List[str], user: User) -> None:
        error_count = 0
        dest_dir = "/home/ttbot/TTMediaBot/data/Downloads/music"
        try:
            os.makedirs(dest_dir, exist_ok=True)
        except Exception as e:
            logging.error(f"Failed to create directory {dest_dir}: {e}")
            self.ttclient.send_message(
                self.translator.translate("Error: {}").format(str(e)),
                user
            )
            return

        for i, link in enumerate(links):
            try:
                self.ttclient.send_message(
                    self.translator.translate("Processing link {number}/{total}: {link}").format(
                        number=i + 1, total=len(links), link=link
                    ),
                    user
                )
                tracks = self.module_manager.streamer.get(link, user.is_admin)
                if not tracks:
                    self.ttclient.send_message(
                        self.translator.translate("Nothing is found for: {link}").format(link=link),
                        user
                    )
                    error_count += 1
                    continue

                for track in tracks:
                    try:
                        if track.type == TrackType.Dynamic:
                            track.url
                        track.download(dest_dir)
                    except Exception as download_err:
                        logging.error(f"Local download failed for track {track.name}: {download_err}")
                        error_count += 1
            except Exception as e:
                logging.error(f"Error processing link {link}: {e}")
                error_count += 1

        if error_count == 0:
            self.ttclient.send_message(
                self.translator.translate("All downloads completed successfully!"),
                user
            )
        else:
            self.ttclient.send_message(
                self.translator.translate("Downloads completed with {error_count} error(s).").format(
                    error_count=error_count
                ),
                user
            )

    def _process_zip(self, links: List[str], user: User) -> None:
        try:
            self.ttclient.send_message(
                self.translator.translate("Resolving links..."),
                user
            )
            tracks = []
            for link in links:
                try:
                    resolved = self.module_manager.streamer.get(link, user.is_admin)
                    if resolved:
                        tracks.extend(resolved)
                except Exception as e:
                    logging.error(f"ADS ZIP: Failed to resolve {link}: {e}")

            if not tracks:
                self.ttclient.send_message(
                    self.translator.translate("Error: No valid tracks found to download."),
                    user
                )
                return

            self.module_manager.playlist_uploader(tracks, user, "Compressed Links")
        except Exception as e:
            self.ttclient.send_message(
                self.translator.translate("Error: {}").format(str(e)),
                user
            )

    def _process_zip_local(self, links: List[str], user: User) -> None:
        error_count = 0
        try:
            self.ttclient.send_message(
                self.translator.translate("Resolving links..."),
                user
            )
            tracks = []
            for link in links:
                try:
                    resolved = self.module_manager.streamer.get(link, user.is_admin)
                    if resolved:
                        tracks.extend(resolved)
                    else:
                        error_count += 1
                except Exception as e:
                    logging.error(f"ADSC ZIP: Failed to resolve {link}: {e}")
                    error_count += 1

            if not tracks:
                self.ttclient.send_message(
                    self.translator.translate("Error: No valid tracks found to download."),
                    user
                )
                return

            temp_dir = tempfile.TemporaryDirectory()
            downloaded_files = []

            for i, track in enumerate(tracks):
                try:
                    if track.type == TrackType.Dynamic:
                        track.url
                    file_path = track.download(temp_dir.name)
                    downloaded_files.append(file_path)
                except Exception as e:
                    logging.error(f"ADSC ZIP: Failed to download track {track.name}: {e}")
                    error_count += 1

            if not downloaded_files:
                self.ttclient.send_message(
                    self.translator.translate("Error: Failed to download any tracks from this playlist."),
                    user
                )
                temp_dir.cleanup()
                return

            dest_dir = "/home/ttbot/TTMediaBot/data/Downloads/zips"
            os.makedirs(dest_dir, exist_ok=True)

            folder_name = "Compressed_Links"
            zip_filename = folder_name + ".zip"
            zip_path = os.path.join(dest_dir, zip_filename)

            counter = 1
            while os.path.exists(zip_path):
                zip_filename = f"{folder_name}_{counter}.zip"
                zip_path = os.path.join(dest_dir, zip_filename)
                counter += 1

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in downloaded_files:
                    arcname = os.path.join(folder_name, os.path.basename(file))
                    zipf.write(file, arcname)

            temp_dir.cleanup()

        except Exception as e:
            logging.error(f"ADSC ZIP processing error: {e}", exc_info=True)
            self.ttclient.send_message(
                self.translator.translate("Error: {}").format(str(e)),
                user
            )
            return

        if error_count == 0:
            self.ttclient.send_message(
                self.translator.translate("All downloads completed successfully!"),
                user
            )
        else:
            self.ttclient.send_message(
                self.translator.translate("Downloads completed with {error_count} error(s).").format(
                    error_count=error_count
                ),
                user
            )


class ToggleLocalDownloadCommand(Command):
    @property
    def help(self) -> str:
        return self.translator.translate(
            "Toggles local download mode for the 'ads' command. When active, files are saved locally to the VPS instead of uploaded to TeamTalk."
        )

    def __call__(self, arg: str, user: User) -> Optional[str]:
        self.command_processor.adsc_enabled = not self.command_processor.adsc_enabled
        if self.command_processor.adsc_enabled:
            return self.translator.translate("Local download mode (adsc) enabled.")
        else:
            return self.translator.translate("Local download mode (adsc) disabled.")




