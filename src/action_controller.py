"""
Action controller with advanced features: cursor tracking, scrolling, double click, cooldowns.
"""

import pyautogui
import time
import subprocess
import os
from typing import Set, Tuple, Optional

class ActionController:
    def __init__(self, screen_width=None, screen_height=None):
        self.screen_width = screen_width or pyautogui.size().width
        self.screen_height = screen_height or pyautogui.size().height
        pyautogui.PAUSE = 0.01

        # Cooldown timers
        self.last_action_time = {
            'zoom_in': 0,
            'zoom_out': 0,
            'click': 0,
            'double_click': 0,
            'scroll': 0,
        }
        self.last_fist_time = 0
        self.fist_cooldown_duration = 2.0

        # Scrolling state
        self.last_scroll_direction = None
        self.last_scroll_time = 0
        self.scroll_direction_change_cooldown = 1.0

        # Virtual keyboard state
        self.keyboard_visible = False
        self.keyboard_process = None

        # Cursor tracking with smoothing
        self.cursor_speed = 2.0  # lower for less shaking
        self.smooth_factor = 0.3  # exponential moving average (0=no smooth, 1=full smooth)
        self.filtered_cursor_pos = None  # (x, y)

        # Prevent cursor movement during pinch click
        self.pinch_active = False

    def _can_perform(self, action: str, cooldown: float) -> bool:
        now = time.time()
        if now - self.last_action_time.get(action, 0) >= cooldown:
            self.last_action_time[action] = now
            return True
        return False

    def is_cooldown_after_fist(self) -> bool:
        return (time.time() - self.last_fist_time) < self.fist_cooldown_duration

    def update_cursor(self, raw_pos: Tuple[float, float]):
        """
        Smooth cursor movement using exponential moving average.
        raw_pos: (x, y) normalized 0..1
        """
        # Map to screen coordinates
        target_x = raw_pos[0] * self.screen_width
        target_y = raw_pos[1] * self.screen_height
        target_x = max(0, min(target_x, self.screen_width))
        target_y = max(0, min(target_y, self.screen_height))

        if self.filtered_cursor_pos is None:
            self.filtered_cursor_pos = (target_x, target_y)
        else:
            # Exponential moving average
            self.filtered_cursor_pos = (
                self.filtered_cursor_pos[0] * (1 - self.smooth_factor) + target_x * self.smooth_factor,
                self.filtered_cursor_pos[1] * (1 - self.smooth_factor) + target_y * self.smooth_factor
            )
        
        # Optionally apply speed multiplier (but smoothing already reduces shakiness)
        final_x = int(self.filtered_cursor_pos[0])
        final_y = int(self.filtered_cursor_pos[1])
        pyautogui.moveTo(final_x, final_y)

    def perform_click(self):
        if self.is_cooldown_after_fist():
            return
        if self._can_perform('click', 0.2):
            # Temporarily disable cursor movement for a short time to avoid moving during click
            pyautogui.click()
            print("Action: Click")

    def perform_double_click(self):
        if self.is_cooldown_after_fist():
            return
        if self._can_perform('double_click', 0.5):
            pyautogui.doubleClick()
            print("Action: Double click")

    def perform_zoom_in(self):
        if self.is_cooldown_after_fist():
            return
        if self._can_perform('zoom_in', 1.0):
            pyautogui.hotkey('ctrl', '+')
            print("Action: Zoom In")

    def perform_zoom_out(self):
        if self.is_cooldown_after_fist():
            return
        if self._can_perform('zoom_out', 1.0):
            pyautogui.hotkey('ctrl', '-')
            print("Action: Zoom Out")

    def perform_scroll(self, dx: float, dy: float):
        if self.is_cooldown_after_fist():
            return

        # Scale movement to scroll amount
        scroll_sensitivity = 15.0
        dx_scroll = dx * scroll_sensitivity
        dy_scroll = dy * scroll_sensitivity

        # Determine primary scroll direction
        if abs(dy_scroll) > abs(dx_scroll):
            if dy_scroll > 0:
                direction = 'down'
                amount = min(int(abs(dy_scroll)), 10)
            else:
                direction = 'up'
                amount = min(int(abs(dy_scroll)), 10)
            if amount == 0:
                return
            now = time.time()
            if self.last_scroll_direction != direction:
                if now - self.last_scroll_time < self.scroll_direction_change_cooldown:
                    return
                else:
                    self.last_scroll_direction = direction
            self.last_scroll_time = now
            pyautogui.scroll(amount if direction == 'up' else -amount)
            print(f"Action: Scroll {direction} {amount}")
        elif abs(dx_scroll) > 0:
            direction = 'right' if dx_scroll > 0 else 'left'
            amount = min(int(abs(dx_scroll)), 10)
            if amount == 0:
                return
            now = time.time()
            if self.last_scroll_direction != direction:
                if now - self.last_scroll_time < self.scroll_direction_change_cooldown:
                    return
                else:
                    self.last_scroll_direction = direction
            self.last_scroll_time = now
            # Horizontal scroll: use left/right arrow keys
            for _ in range(amount):
                if direction == 'right':
                    pyautogui.press('right')
                else:
                    pyautogui.press('left')
            print(f"Action: Scroll {direction} {amount}")

    def toggle_virtual_keyboard(self):
        """Toggle onboard virtual keyboard using xdotool."""
        try:
            # Check if onboard is running
            result = subprocess.run(['pgrep', '-x', 'onboard'], capture_output=True)
            if result.returncode == 0:
                # Kill onboard
                subprocess.run(['pkill', '-x', 'onboard'])
                self.keyboard_visible = False
                print("Virtual keyboard off")
            else:
                # Start onboard
                subprocess.Popen(['onboard'])
                self.keyboard_visible = True
                print("Virtual keyboard on")
        except Exception as e:
            print(f"Failed to toggle virtual keyboard: {e}")

    def execute_gestures(self, gestures: Set[str],
                         index_tip_pos: Optional[Tuple[float, float]] = None,
                         hand_movement: Optional[Tuple[float, float]] = None,
                         double_tap: bool = False):
        """
        Execute actions based on recognized gestures.
        """
        # Fist: reset cooldown and also clear cursor smoothing state
        if 'fist' in gestures:
            self.last_fist_time = time.time()
            self.last_scroll_direction = None
            self.filtered_cursor_pos = None  # reset smoothing
            return

        # Check if any pinch gesture is active (to potentially inhibit cursor movement)
        pinch_active = any(g in gestures for g in ['click', 'zoom_in', 'zoom_out'])
        
        # Only index up -> cursor tracking (but not if pinch active to avoid interference)
        if 'only_index_up' in gestures and index_tip_pos is not None and not pinch_active:
            self.update_cursor(index_tip_pos)

        # Double tap
        if double_tap:
            self.perform_double_click()

        # Pinch gestures (click, zoom)
        if 'click' in gestures:
            self.perform_click()
        if 'zoom_in' in gestures:
            self.perform_zoom_in()
        if 'zoom_out' in gestures:
            self.perform_zoom_out()

        # Index+middle up -> scrolling
        if 'index_middle_up' in gestures and hand_movement is not None:
            dx, dy = hand_movement
            self.perform_scroll(dx, dy)

