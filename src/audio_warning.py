import logging
import os
import platform
import subprocess
import tempfile
import threading

logger = logging.getLogger(__name__)

# Import gTTS and pygame for Google TTS
try:
    import pygame
    from gtts import gTTS

    GTTS_AVAILABLE = True
    logger.info("Google TTS (gTTS) available")
except ImportError:
    GTTS_AVAILABLE = False
    logger.warning("Google TTS not available. Install with: pip install gtts pygame")


class AudioWarningSystem:
    """Text-to-speech audio warning system for fall detection"""

    def __init__(self):
        self.is_enabled = True
        self.volume = 0.8  # 80% volume
        self.voice_speed = 150  # Words per minute
        self.temp_dir = tempfile.gettempdir()

        # Initialize pygame mixer for audio playback
        if GTTS_AVAILABLE:
            try:
                pygame.mixer.init()
                logger.info("Pygame mixer initialized for Google TTS")
            except Exception as e:
                logger.error(f"Failed to initialize pygame mixer: {e}")

        # Check available TTS systems (Google TTS is preferred)
        self.tts_method = self._detect_tts_system()

    def _detect_tts_system(self) -> str:
        """Detect available TTS system on the platform (prioritize Google TTS)"""

        # Priority 1: Google TTS (best quality for Vietnamese)
        if GTTS_AVAILABLE:
            try:
                # Test Google TTS with a simple request
                gTTS(text="test", lang="vi", slow=False)
                logger.info("Using Google Text-to-Speech (gTTS)")
                return "google_tts"
            except Exception as e:
                logger.warning(f"Google TTS test failed: {e}")

        # Fallback to system TTS
        system = platform.system().lower()

        try:
            # Check for espeak-ng (Linux/Windows)
            result = subprocess.run(["espeak-ng", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info("Using espeak-ng for TTS")
                return "espeak-ng"
        except:
            pass

        try:
            # Check for espeak (Linux)
            result = subprocess.run(["espeak", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info("Using espeak for TTS")
                return "espeak"
        except:
            pass

        try:
            # Check for festival (Linux)
            result = subprocess.run(["festival", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info("Using festival for TTS")
                return "festival"
        except:
            pass

        if system == "windows":
            logger.info("Using Windows SAPI for TTS")
            return "windows_sapi"
        elif system == "darwin":  # macOS
            logger.info("Using macOS say command for TTS")
            return "macos_say"
        else:
            # Try to install espeak-ng as fallback
            logger.warning("No TTS system detected. Consider installing espeak-ng: sudo apt-get install espeak-ng")
            return "none"

    def _generate_warning_text(self, analysis_result: str) -> str:
        """Generate contextual warning text based on analysis result"""

        # Extract key information from analysis result
        analysis_lower = analysis_result.lower()

        # Determine person description
        person_desc = "một người"
        if "đàn ông" in analysis_lower or "nam" in analysis_lower:
            person_desc = "một người đàn ông"
        elif "phụ nữ" in analysis_lower or "nữ" in analysis_lower:
            person_desc = "một người phụ nữ"
        elif "trẻ em" in analysis_lower or "em bé" in analysis_lower:
            person_desc = "một trẻ em"
        elif "người cao tuổi" in analysis_lower or "già" in analysis_lower:
            person_desc = "một người cao tuổi"

        # Determine location
        location = "trong khu vực"
        if "phòng" in analysis_lower:
            location = "trong phòng"
        elif "hành lang" in analysis_lower:
            location = "ở hành lang"
        elif "cầu thang" in analysis_lower:
            location = "ở cầu thang"
        elif "phòng tắm" in analysis_lower or "toilet" in analysis_lower:
            location = "trong phòng tắm"
        elif "bếp" in analysis_lower:
            location = "trong bếp"

        # Generate warning message
        warning_text = f"Cảnh báo khẩn cấp! Có {person_desc} đang bị ngã {location}. Cần đến kiểm tra ngay lập tức!"

        return warning_text

    def play_warning_google_tts(self, text: str) -> bool:
        """Play warning using Google Text-to-Speech"""
        try:
            if not GTTS_AVAILABLE:
                logger.error("Google TTS not available")
                return False

            # Create gTTS object for Vietnamese
            tts = gTTS(text=text, lang="vi", slow=False)

            # Save to temporary file
            temp_file = os.path.join(self.temp_dir, "warning_audio.mp3")
            tts.save(temp_file)

            # Play audio using pygame
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()

            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)

            # Clean up
            try:
                os.remove(temp_file)
            except:
                pass

            return True

        except Exception as e:
            logger.error(f"Error playing warning with Google TTS: {e}")
            return False

    def play_warning_espeak(self, text: str, lang: str = "vi") -> bool:
        """Play warning using espeak/espeak-ng"""
        try:
            # espeak-ng command for Vietnamese
            cmd = [
                self.tts_method,
                "-v",
                f"{lang}+f3",  # Vietnamese female voice
                "-s",
                str(self.voice_speed),  # Speed
                "-a",
                str(int(self.volume * 200)),  # Amplitude (0-200)
                text,
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=10)
            return result.returncode == 0

        except Exception as e:
            logger.error(f"Error playing warning with espeak: {e}")
            return False

    def play_warning_festival(self, text: str) -> bool:
        """Play warning using festival"""
        try:
            # Create temporary text file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write(text)
                temp_file = f.name

            # Festival command
            cmd = ["festival", "--tts", temp_file]
            result = subprocess.run(cmd, capture_output=True, timeout=15)

            # Clean up
            os.unlink(temp_file)

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Error playing warning with festival: {e}")
            return False

    def play_warning_windows(self, text: str) -> bool:
        """Play warning using Windows SAPI"""
        try:
            # Use PowerShell for Windows TTS
            ps_script = f"""
            Add-Type -AssemblyName System.Speech
            $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
            $synth.Volume = {int(self.volume * 100)}
            $synth.Rate = {int((self.voice_speed - 100) / 25)}
            $synth.Speak('{text}')
            """

            result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, timeout=15)

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Error playing warning with Windows SAPI: {e}")
            return False

    def play_warning_macos(self, text: str) -> bool:
        """Play warning using macOS say command"""
        try:
            cmd = ["say", "-v", "Ting-Ting", "-r", str(self.voice_speed), text]  # Chinese voice (closest to Vietnamese)

            result = subprocess.run(cmd, capture_output=True, timeout=15)
            return result.returncode == 0

        except Exception as e:
            logger.error(f"Error playing warning with macOS say: {e}")
            return False

    def play_warning_audio(self, analysis_result: str) -> bool:
        """Play audio warning based on analysis result"""
        if not self.is_enabled:
            logger.info("Audio warnings disabled")
            return False

        if self.tts_method == "none":
            logger.warning("No TTS system available")
            return False

        try:
            # Generate contextual warning text
            warning_text = self._generate_warning_text(analysis_result)
            logger.info(f"Playing audio warning: {warning_text}")

            # Play audio based on available TTS system (prioritize Google TTS)
            success = False

            if self.tts_method == "google_tts":
                success = self.play_warning_google_tts(warning_text)
                # Fallback to espeak if Google TTS fails
                if not success and any(method in ["espeak", "espeak-ng"] for method in [self.tts_method]):
                    logger.warning("Google TTS failed, falling back to espeak")
                    success = self.play_warning_espeak(warning_text)
            elif self.tts_method in ["espeak", "espeak-ng"]:
                success = self.play_warning_espeak(warning_text)
            elif self.tts_method == "festival":
                success = self.play_warning_festival(warning_text)
            elif self.tts_method == "windows_sapi":
                success = self.play_warning_windows(warning_text)
            elif self.tts_method == "macos_say":
                success = self.play_warning_macos(warning_text)

            if success:
                logger.info("Audio warning played successfully")
            else:
                logger.error("Failed to play audio warning")

            return success

        except Exception as e:
            logger.error(f"Error in play_warning_audio: {e}")
            return False

    def play_warning_async(self, analysis_result: str):
        """Play warning audio in a separate thread to avoid blocking"""

        def audio_worker():
            self.play_warning_audio(analysis_result)

        thread = threading.Thread(target=audio_worker, daemon=True)
        thread.start()

    def test_audio_system(self) -> str:
        """Test the audio warning system"""
        if self.tts_method == "none":
            return "❌ Không có hệ thống TTS nào được phát hiện"

        success = self.play_warning_audio("PHÁT_HIỆN_TÉ_NGÃ: Đây là kiểm tra hệ thống cảnh báo âm thanh")

        if success:
            return f"✅ Hệ thống âm thanh hoạt động bình thường ({self.tts_method})"
        else:
            return f"❌ Lỗi hệ thống âm thanh ({self.tts_method})"

    def set_enabled(self, enabled: bool):
        """Enable or disable audio warnings"""
        self.is_enabled = enabled
        logger.info(f"Audio warnings {'enabled' if enabled else 'disabled'}")

    def set_volume(self, volume: float):
        """Set audio volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        logger.info(f"Audio volume set to {self.volume * 100:.0f}%")

    def set_speed(self, speed: int):
        """Set speech speed (words per minute)"""
        self.voice_speed = max(80, min(300, speed))
        logger.info(f"Speech speed set to {self.voice_speed} WPM")

    def get_status(self) -> dict:
        """Get current audio system status"""
        return {
            "enabled": self.is_enabled,
            "tts_method": self.tts_method,
            "volume": self.volume,
            "speed": self.voice_speed,
            "available": self.tts_method != "none",
            "google_tts_available": GTTS_AVAILABLE,
        }
