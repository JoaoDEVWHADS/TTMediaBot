from __future__ import annotations
import logging
import threading
import time
import os
import tempfile
from typing import TYPE_CHECKING
from queue import Empty


from bot.player.track import Track
from bot.player.enums import TrackType
from bot.TeamTalk.structs import ErrorType, User
from bot import app_vars

if TYPE_CHECKING:
    from bot import Bot


class Uploader:
    def __init__(self, bot: Bot):
        self.config = bot.config
        self.ttclient = bot.ttclient
        self.translator = bot.translator

    def __call__(self, track: Track, user: User, video: bool = False) -> None:
        thread = threading.Thread(
            target=self.run,
            daemon=True,
            args=(
                track,
                user,
                video,
            ),
        )
        thread.start()

    def run(self, track: Track, user: User, video: bool = False) -> None:
        logging.info(f"Uploader started for track '{track.name}' (Type: {track.type}, Video: {video}) requested by {user.username}")
        error_exit = False
        temp_dir = None
        try:
            if track.type == TrackType.Default or track.service in ['yt', 'ytm']:
                temp_dir = tempfile.TemporaryDirectory()
                logging.info(f"Uploader: Downloading track to {temp_dir.name} (Video: {video})")
                file_path = track.download(temp_dir.name, video=video)
            else:
                logging.info(f"Uploader: Using direct URL/path: {track.url}")
                file_path = track.url
            
            if not os.path.exists(file_path):
                # Check if it exists with another extension just in case
                base_path = file_path.rsplit(".", 1)[0]
                found = False
                for ext in ["mp4", "mkv", "webm", "mp3", "m4a", "opus"]:
                    if os.path.exists(f"{base_path}.{ext}"):
                        file_path = f"{base_path}.{ext}"
                        file_name = os.path.basename(file_path)
                        found = True
                        logging.warning(f"Uploader: Expected file not found, but found '{file_path}' instead. Using it.")
                        break
                if not found:
                    logging.error(f"Uploader: File not found at '{file_path}' and no alternative extensions found.")
                    self.ttclient.send_message(self.translator.translate("Error: Downloaded file not found."), user)
                    return

            logging.info(f"Uploader: Sending file '{file_path}' to channel {self.ttclient.channel.id}")
            command_id = self.ttclient.send_file(self.ttclient.channel.id, file_path)
            file_name = os.path.basename(file_path)
            while True:
                try:
                    file = self.ttclient.uploaded_files_queue.get_nowait()
                    if file.name == file_name:
                        logging.info(f"Uploader: File '{file_name}' successfully uploaded")
                        break
                    else:
                        self.ttclient.uploaded_files_queue.put(file)
                except Empty:
                    pass
                try:
                    error = self.ttclient.errors_queue.get_nowait()
                    if error.command_id == command_id:
                        logging.error(f"Uploader: Error uploading file: {error.message} (Type: {error.type})")
                        self.ttclient.send_message(
                            self.translator.translate("Error: {}").format(error.message),
                            user,
                        )
                        error_exit = True
                        break
                    else:
                        self.ttclient.errors_queue.put(error)
                except Empty:
                    pass
                time.sleep(app_vars.loop_timeout)
        finally:
            if temp_dir:
                logging.debug("Uploader: Cleaning up local temporary directory")
                temp_dir.cleanup()

        if error_exit:
            return

        if self.config.general.delete_uploaded_files_after > 0:
            timeout = self.config.general.delete_uploaded_files_after
            def delete_after_timeout():
                time.sleep(timeout)
                try:
                    self.ttclient.delete_file(file.channel.id, file.id)
                except Exception as e:
                    logging.error(f"Uploader: Failed to delete file {file.id}: {e}")

            threading.Thread(target=delete_after_timeout, daemon=True).start()

