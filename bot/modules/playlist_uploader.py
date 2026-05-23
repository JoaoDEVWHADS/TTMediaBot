from __future__ import annotations
import logging
import threading
import time
import os
import tempfile
import zipfile
from typing import TYPE_CHECKING, List
from queue import Empty

from bot.player.track import Track
from bot.player.enums import TrackType
from bot.TeamTalk.structs import ErrorType, User
from bot import app_vars, utils

if TYPE_CHECKING:
    from bot import Bot


class PlaylistUploader:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = bot.config
        self.ttclient = bot.ttclient
        self.translator = bot.translator
        self.current_status = {} # Track status per user/channel

    def __call__(self, tracks: List[Track], user: User, playlist_name: str = "Playlist") -> None:
        thread = threading.Thread(
            target=self.run,
            daemon=True,
            args=(
                tracks,
                user,
                playlist_name,
            ),
        )
        thread.start()

    def get_status(self, user_id: int) -> Optional[str]:
        return self.current_status.get(user_id)

    def run(self, tracks: List[Track], user: User, playlist_name: str) -> None:
        logging.info(f"PlaylistUploader started for {len(tracks)} tracks requested by {user.username}")
        user_id = user.id
        
        # Limit tracks to prevent resource exhaustion
        max_tracks = 100 # Default limit
        if len(tracks) > max_tracks:
            self.ttclient.send_message(
                self.translator.translate("Error: This playlist is too large (max {} tracks).").format(max_tracks),
                user
            )
            return

        error_exit = False
        temp_dir = tempfile.TemporaryDirectory()
        try:
            downloaded_files = []
            
            status_msg = self.translator.translate("Downloading playlist: {}").format(playlist_name)
            self.current_status[user_id] = status_msg
            self.ttclient.send_message(status_msg, user.id, 1) # 1 = UserMessage (Private)

            for i, track in enumerate(tracks):
                try:
                    progress_info = f"{i+1}/{len(tracks)}"
                    current_track_msg = self.translator.translate("Downloading track {}: {}").format(progress_info, track.name)
                    self.current_status[user_id] = current_track_msg
                    
                    # Update user every few tracks or for small playlists to avoid spamming too much
                    if len(tracks) <= 10 or (i + 1) % 5 == 0 or i == 0 or (i + 1) == len(tracks):
                        self.ttclient.send_message(current_track_msg, user.id, 1)
                    
                    logging.info(f"PlaylistUploader: {current_track_msg}")
                    
                    # Fetch stream data if it's dynamic
                    if track.type == TrackType.Dynamic:
                        try:
                            track.url # Trigger fetch
                        except Exception as e:
                            logging.warning(f"PlaylistUploader: Failed to fetch data for track {i+1}: {e}")
                            continue

                    file_path = track.download(temp_dir.name)
                    downloaded_files.append(file_path)
                except Exception as e:
                    logging.error(f"PlaylistUploader: Failed to download track {i+1}: {e}")
                    continue

            if not downloaded_files:
                self.current_status.pop(user_id, None)
                self.ttclient.send_message(
                    self.translator.translate("Error: Failed to download any tracks from this playlist."),
                    user.id,
                    1
                )
                return

            zip_status = self.translator.translate("Zipping tracks...")
            self.current_status[user_id] = zip_status
            self.ttclient.send_message(zip_status, user.id, 1)

            # Create ZIP file with subfolder
            folder_name = utils.clean_file_name(playlist_name)
            zip_filename = folder_name + ".zip"
            zip_path = os.path.join(temp_dir.name, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in downloaded_files:
                    # Write file into a subfolder inside the ZIP
                    arcname = os.path.join(folder_name, os.path.basename(file))
                    zipf.write(file, arcname)

            upload_status = self.translator.translate("Uploading ZIP: {}").format(zip_filename)
            self.current_status[user_id] = upload_status
            logging.info(f"PlaylistUploader: Sending ZIP file '{zip_path}' to channel {self.ttclient.channel.id}")
            self.ttclient.send_message(upload_status, user.id, 1)
            
            command_id = self.ttclient.send_file(self.ttclient.channel.id, zip_path)
            
            while True:
                try:
                    file = self.ttclient.uploaded_files_queue.get_nowait()
                    if file.name == zip_filename:
                        break
                    else:
                        self.ttclient.uploaded_files_queue.put(file)
                except Empty:
                    pass
                try:
                    error = self.ttclient.errors_queue.get_nowait()
                    if error.command_id == command_id:
                        logging.error(f"PlaylistUploader: Error uploading zip: {error.message} (Type: {error.type})")
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
                
        except Exception as e:
            logging.error(f"PlaylistUploader error: {e}", exc_info=True)
            self.ttclient.send_message(
                self.translator.translate("Error: {}").format(str(e)),
                user
            )
        finally:
            self.current_status.pop(user_id, None)
            logging.debug("PlaylistUploader: Cleaning up local temporary directory")
            temp_dir.cleanup()

        if error_exit:
            return
