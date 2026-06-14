"""
Action controller module.
Translates gestures into mouse/keyboard actions using PyAutoGUI.
"""

import pyautogui
import time
from typing import Set


class ActionController:
    """Executes system actions based on gestures."""

    # Cooldown between repeated same actions (seconds)
    CLICK_COOLDOWN = 0.5
    ZOOM_COOLDOWN = 0.3

    def __init__(self):
        """Initialize controller with cooldown timers."""
        self.last_action_time = {
            "click": 0,
            "zoom_in": 0,
            "zoom_out": 0
        }
        # Safety: add a small delay for pyautogui
        pyautogui.PAUSE = 0.05

    def _can_perform(self, action: str) -> bool:
        """Check if enough time has passed since last same action."""
        now = time.time()
        cooldown = self.CLICK_COOLDOWN if action == "click" else self.ZOOM_COOLDOWN
        if now - self.last_action_time[action] >= cooldown:
            self.last_action_time[action] = now
            return True
        return False

    def perform_click(self):
        """Simulate a left mouse click."""
        if self._can_perform("click"):
            pyautogui.click()
            print("Action: Click")

    def perform_zoom_in(self):
        """Zoom in using Ctrl + '+'."""
        if self._can_perform("zoom_in"):
            pyautogui.hotkey('ctrl', '+')
            print("Action: Zoom In")

    def perform_zoom_out(self):
        """Zoom out using Ctrl + '-'."""
        if self._can_perform("zoom_out"):
            pyautogui.hotkey('ctrl', '-')
            print("Action: Zoom Out")

    def execute_gestures(self, gestures: Set[str]):
        """
        Execute actions for a set of gestures.

        Args:
            gestures: Set of gesture names (unique per frame).
        """
        for gesture in gestures:
            if gesture == "click":
                self.perform_click()
            elif gesture == "zoom_in":
                self.perform_zoom_in()
            elif gesture == "zoom_out":
                self.perform_zoom_out()

