"""Audio notification utilities."""
from __future__ import annotations
import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional
from myTime.core.models import SessionType


class AudioManager:
    """Manages audio notifications using system sounds or custom files."""
    
    # Freedesktop sound theme names
    SOUND_MAP = {
        SessionType.WORK: "message-new-instant",
        SessionType.SHORT_BREAK: "bell",
        SessionType.LONG_BREAK: "complete",
        "journey_complete": "service-login",
        "error": "dialog-error",
        "warning": "dialog-warning",
    }
    
    def __init__(self, enabled: bool = True, custom_sounds_dir: Optional[str] = None):
        self.enabled = enabled
        self.custom_sounds_dir = Path(custom_sounds_dir) if custom_sounds_dir else None
        self._canberra = shutil.which("canberra-gtk-play")
        self._paplay = shutil.which("paplay")
        self._aplay = shutil.which("aplay")
        
    def is_available(self) -> bool:
        """Check if any audio player is available."""
        return bool(self._canberra or self._paplay or self._aplay)
    
    def play(self, session_type: SessionType, volume: float = 1.0) -> bool:
        """Play sound for session type."""
        if not self.enabled:
            return False
            
        sound_name = self.SOUND_MAP.get(session_type, "message-new-instant")
        
        # Try custom sound file first
        if self.custom_sounds_dir:
            custom_file = self._find_custom_sound(sound_name)
            if custom_file and custom_file.exists():
                return self._play_file(custom_file, volume)
        
        # Try system sound via canberra-gtk-play (best for freedesktop)
        if self._canberra:
            return self._play_canberra(sound_name)
        
        # Try paplay (PulseAudio)
        if self._paplay:
            return self._play_paplay(sound_name)
            
        # Try aplay (ALSA)
        if self._aplay:
            return self._play_aplay(sound_name)
            
        return False
    
    def play_custom(self, sound_file: str, volume: float = 1.0) -> bool:
        """Play a custom sound file."""
        if not self.enabled:
            return False
        path = Path(sound_file)
        if not path.exists():
            return False
        return self._play_file(path, volume)
    
    def _find_custom_sound(self, base_name: str) -> Optional[Path]:
        """Find custom sound file with various extensions."""
        if not self.custom_sounds_dir:
            return None
        for ext in [".wav", ".ogg", ".oga", ".mp3"]:
            candidate = self.custom_sounds_dir / f"{base_name}{ext}"
            if candidate.exists():
                return candidate
        return None
    
    def _play_canberra(self, sound_name: str) -> bool:
        """Play using canberra-gtk-play."""
        try:
            subprocess.run([
                self._canberra,
                "-i", sound_name,
                "-d", "myTime"
            ], check=False, timeout=3, capture_output=True)
            return True
        except (subprocess.SubprocessError, TimeoutError):
            return False
    
    def _play_paplay(self, sound_name: str) -> bool:
        """Play using paplay (PulseAudio)."""
        # Try freedesktop sound theme locations
        sound_dirs = [
            "/usr/share/sounds/freedesktop/stereo",
            "/usr/share/sounds/ubuntu/stereo",
            os.path.expanduser("~/.local/share/sounds"),
        ]
        
        for sound_dir in sound_dirs:
            sound_file = Path(sound_dir) / f"{sound_name}.oga"
            if sound_file.exists():
                return self._play_file(sound_file)
        return False
    
    def _play_aplay(self, sound_name: str) -> bool:
        """Play using aplay (ALSA)."""
        sound_dirs = [
            "/usr/share/sounds/alsa",
            "/usr/share/sounds",
        ]
        
        for sound_dir in sound_dirs:
            sound_file = Path(sound_dir) / f"{sound_name}.wav"
            if sound_file.exists():
                return self._play_file(sound_file)
        return False
    
    def _play_file(self, file_path: Path, volume: float = 1.0) -> bool:
        """Play a sound file using available player."""
        if self._paplay:
            try:
                subprocess.run([
                    self._paplay,
                    "--volume", str(int(volume * 65536)),
                    str(file_path)
                ], check=False, timeout=5, capture_output=True)
                return True
            except (subprocess.SubprocessError, TimeoutError):
                pass
                
        if self._aplay:
            try:
                subprocess.run([
                    self._aplay,
                    "-q",  # quiet
                    str(file_path)
                ], check=False, timeout=5, capture_output=True)
                return True
            except (subprocess.SubprocessError, TimeoutError):
                pass
                
        return False
    
    def play_journey_complete(self) -> bool:
        """Play journey completion sound."""
        return self.play(SessionType.LONG_BREAK)  # Reuse complete sound
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable audio notifications."""
        self.enabled = enabled
    
    def set_custom_sounds_dir(self, path: str) -> None:
        """Set custom sounds directory."""
        self.custom_sounds_dir = Path(path)
