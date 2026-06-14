"""
Action controller with advanced features: cursor tracking, scrolling, double click, cooldowns.
"""

import pyautogui
import time
from typing import Set, Tuple, Optional

class ActionController:
    def __init__(self, screen_width=None, screen_height=None):
        self.screen_width = screen_width or pyautogui.size().width
        self.screen_height = screen_height or pyautogui.size().height
        pyautogui.PAUSE = 0.01  # very small pause for smooth movement

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

        # Cursor tracking parameters
        self.cursor_speed = 6.0  # increased from 4.0
        self.smoothing_factor = 0.3  # lower = smoother but slower; 0.3 is good
        self.smoothed_pos = None   # (x, y) normalized
        self.dead_zone = 0.01      # ignore movements smaller than this

        # To prevent cursor movement during click
        self.click_lock_until = 0
        self.click_lock_duration = 0.3  # seconds after a click, cursor doesn't move

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
        Smooth cursor movement and apply dead zone.
        raw_pos: (x, y) normalized (0..1)
        """
        # If click lock is active, ignore cursor movement
        if time.time() < self.click_lock_until:
            return

        # Smoothing
        if self.smoothed_pos is None:
            self.smoothed_pos = raw_pos
        else:
            self.smoothed_pos = (
                self.smoothed_pos[0] * (1 - self.smoothing_factor) + raw_pos[0] * self.smoothing_factor,
                self.smoothed_pos[1] * (1 - self.smoothing_factor) + raw_pos[1] * self.smoothing_factor
            )

        # Apply dead zone (if movement is tiny, skip to reduce jitter)
        # We'll compute delta from last applied position, but we don't store last applied.
        # Instead, we directly map smoothed position to screen.
        screen_x = int(self.smoothed_pos[0] * self.screen_width)
        screen_y = int(self.smoothed_pos[1] * self.screen_height)

        # Invert Y if needed? Usually hand moving up (decreasing y) should move cursor up.
        # But MediaPipe y increases downward, so we need to invert: cursor_y = height - (y * height)
        # Actually most users expect moving hand up = cursor up. So we invert Y.
        screen_y = self.screen_height - screen_y

        # Clamp
        screen_x = max(0, min(screen_x, self.screen_width))
        screen_y = max(0, min(screen_y, self.screen_height))

        # Only move if distance is beyond dead zone (optional: check delta from last mouse pos)
        # But pyautogui.moveTo will handle tiny moves; we can skip to reduce CPU.
        # For now, always move.
        pyautogui.moveTo(screen_x, screen_y)

    def perform_click(self):
        if self.is_cooldown_after_fist():
            return
        if self._can_perform('click', 0.2):
            # Lock cursor movement for a short time to avoid accidental movement while clicking
            self.click_lock_until = time.time() + self.click_lock_duration
            pyautogui.click()
            print("Action: Click")

    def perform_double_click(self):
        if self.is_cooldown_after_fist():
            return
        if self._can_perform('double_click', 0.5):
            self.click_lock_until = time.time() + self.click_lock_duration
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

        # Invert scroll direction for natural feel: hand up (negative dy) should scroll up?
        # We'll keep as is but allow config later.
        if abs(dy) > abs(dx):
            if dy > 0:
                direction = 'down'
            else:
                direction = 'up'
            amount = int(abs(dy) * 15)  # increased sensitivity
            if amount == 0:
                return
            now = time.time()
            if self.last_scroll_direction != direction:
                if now - self.last_scroll_time < self.scroll_direction_change_cooldown:
                    return
                else:
                    self.last_scroll_direction = direction
            self.last_scroll_time = now
            clicks = amount if direction in ('up', 'down') else 1
            pyautogui.scroll(clicks if direction == 'up' else -clicks)
            print(f"Action: Scroll {direction} {clicks}")
        elif abs(dx) > 0:
            direction = 'right' if dx > 0 else 'left'
            amount = int(abs(dx) * 15)
            if amount == 0:
                return
            now = time.time()
            if self.last_scroll_direction != direction:
                if now - self.last_scroll_time < self.scroll_direction_change_cooldown:
                    return
                else:
                    self.last_scroll_direction = direction
            self.last_scroll_time = now
            for _ in range(min(amount, 10)):
                if direction == 'right':
                    pyautogui.press('right')
                else:
                    pyautogui.press('left')
            print(f"Action: Scroll {direction} {amount}")

    def toggle_virtual_keyboard(self):
        if self.keyboard_visible:
            pyautogui.hotkey('ctrl', 'alt', 'k')
            print("Virtual keyboard off")
        else:
            pyautogui.hotkey('ctrl', 'alt', 'k')
            print("Virtual keyboard on")
        self.keyboard_visible = not self.keyboard_visible

    def execute_gestures(self, gestures: Set[str],
                         index_tip_pos: Optional[Tuple[float, float]] = None,
                         hand_movement: Optional[Tuple[float, float]] = None,
                         double_tap: bool = False):
        if 'fist' in gestures:
            self.last_fist_time = time.time()
            self.last_scroll_direction = None
            return

        if 'only_index_up' in gestures and index_tip_pos is not None:
            self.update_cursor(index_tip_pos)

        if double_tap:
            self.perform_double_click()

        if 'click' in gestures:
            self.perform_click()
        if 'zoom_in' in gestures:
            self.perform_zoom_in()
        if 'zoom_out' in gestures:
            self.perform_zoom_out()

        if 'index_middle_up' in gestures and hand_movement is not None:
            dx, dy = hand_movement
            self.perform_scroll(dx, dy)

