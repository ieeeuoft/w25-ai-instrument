from pedalboard import Pedalboard, Chorus, Reverb, Delay, Distortion
import numpy as np

class EffectBoard:
    def __init__(self, effects=None):
        """
        Initialize a pedalboard with optional effects.
        
        Args:
            effects (list): List of effect instances to add to the pedalboard
        """
        self.board = Pedalboard()
        if effects:
            for effect in effects:
                self.board.append(effect)
    
    #chorus doesn't work well (makes it sound like a bad radio)
    def add_chorus(self, rate_hz=1.0, depth=0.3, mix=0.3):
        """
        Add a chorus effect to the pedalboard.
        
        Args:
            rate_hz (float): Rate of the chorus modulation in Hz (default: 1.0)
            depth (float): Depth of the chorus effect (0.0 to 1.0, default: 0.3)
            mix (float): Mix of the effect (0.0 to 1.0, default: 0.3)
        """
        chorus = Chorus(rate_hz=rate_hz, depth=depth, mix=mix)
        self.board.append(chorus)
        return chorus
    
    def add_reverb(self, room_size=0.5, wet_level=0.2, dry_level=0.8):
        """
        Add a reverb effect to the pedalboard.
        
        Args:
            room_size (float): Size of the reverb room (0.0 to 1.0, default: 0.5)
            wet_level (float): Level of the wet signal (0.0 to 1.0, default: 0.2)
            dry_level (float): Level of the dry signal (0.0 to 1.0, default: 0.8)
        """
        reverb = Reverb(room_size=room_size, wet_level=wet_level, dry_level=dry_level)
        self.board.append(reverb)
        return reverb
    
    def add_delay(self, delay_seconds=0.3, feedback=0.2, mix=0.3):
        """
        Add a delay effect to the pedalboard.
        
        Args:
            delay_seconds (float): Delay time in seconds (default: 0.3)
            feedback (float): Amount of feedback (0.0 to 1.0, default: 0.2)
            mix (float): Mix of the effect (0.0 to 1.0, default: 0.3)
        """
        delay = Delay(delay_seconds=delay_seconds, feedback=feedback, mix=mix)
        self.board.append(delay)
        return delay
    
    def add_distortion(self, drive_db=10):
        """
        Add a distortion effect to the pedalboard.
        
        Args:
            drive_db (float): Amount of drive in decibels (default: 10)
        """
        distortion = Distortion(drive_db=drive_db)
        self.board.append(distortion)
        return distortion
    
    def remove_effect(self, index):
        """Remove an effect from the pedalboard by index."""
        if 0 <= index < len(self.board):
            self.board.pop(index)
    
    def clear_effects(self):
        """Remove all effects from the pedalboard."""
        self.board.clear()
    
    def apply(self, audio, sample_rate, normalize=True):
        """
        Apply all effects in the pedalboard to the audio.
        
        Args:
            audio (numpy.ndarray): Input audio signal
            sample_rate (int): Sample rate of the audio
            normalize (bool): Whether to normalize the output to prevent clipping
        """
        processed = self.board(audio, sample_rate)
        
        if normalize:
            # Normalize if the signal exceeds 1.0
            max_amplitude = np.max(np.abs(processed))
            if max_amplitude > 1.0:
                processed = processed / max_amplitude
        
        return processed
