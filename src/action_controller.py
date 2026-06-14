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
        self.fist_cooldown_duration = 2.0  # seconds after fist no actions

        # Scrolling state
        self.last_scroll_direction = None  # 'up', 'down', 'left', 'right'
        self.last_scroll_time = 0
        self.scroll_direction_change_cooldown = 1.0  # seconds

        # Virtual keyboard state
        self.keyboard_visible = False

        # For cursor tracking
        self.cursor_speed = 4.0  # multiplier for hand movement to cursor movement

    def _can_perform(self, action: str, cooldown: float) -> bool:
        """Check if enough time has passed since last same action."""
        now = time.time()
        if now - self.last_action_time.get(action, 0) >= cooldown:
            self.last_action_time[action] = now
            return True
        return False

    def is_cooldown_after_fist(self) -> bool:
        """Return True if still in cooldown after fist gesture."""
        return (time.time() - self.last_fist_time) < self.fist_cooldown_duration

    def update_cursor(self, index_tip_pos: Tuple[float, float]):
        """
        Move mouse cursor based on normalized index tip position (x, y in 0..1).
        Maps to screen coordinates with speed factor.
        """
        # Smooth movement: map directly to screen
        screen_x = int(index_tip_pos[0] * self.screen_width)
        screen_y = int(index_tip_pos[1] * self.screen_height)
        # Clamp to screen
        screen_x = max(0, min(screen_x, self.screen_width))
        screen_y = max(0, min(screen_y, self.screen_height))
        pyautogui.moveTo(screen_x, screen_y)

    def perform_click(self):
        if self.is_cooldown_after_fist():
            return
        if self._can_perform('click', 0.2):  # 0.2s cooldown between clicks
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
        """
        Scroll based on hand movement (dx, dy normalized).
        dx>0 scroll right, dx<0 left; dy>0 scroll down, dy<0 up.
        Applies direction change cooldown.
        """
        if self.is_cooldown_after_fist():
            return

        # Determine primary scroll direction (vertical has priority if both)
        if abs(dy) > abs(dx):
            if dy > 0:
                direction = 'down'
            else:
                direction = 'up'
            amount = int(abs(dy) * 10)  # scale
            if amount == 0:
                return
            now = time.time()
            # Check direction change
            if self.last_scroll_direction != direction:
                if now - self.last_scroll_time < self.scroll_direction_change_cooldown:
                    return  # wait before changing direction
                else:
                    self.last_scroll_direction = direction
            self.last_scroll_time = now
            # Perform scroll
            clicks = amount if direction in ('up', 'down') else 1
            pyautogui.scroll(clicks if direction == 'up' else -clicks)
            print(f"Action: Scroll {direction} {clicks}")
        elif abs(dx) > 0:
            # Horizontal scroll (not natively in pyautogui, but we can simulate with keys)
            direction = 'right' if dx > 0 else 'left'
            amount = int(abs(dx) * 10)
            if amount == 0:
                return
            now = time.time()
            if self.last_scroll_direction != direction:
                if now - self.last_scroll_time < self.scroll_direction_change_cooldown:
                    return
                else:
                    self.last_scroll_direction = direction
            self.last_scroll_time = now
            # For horizontal scroll, use left/right arrow keys (or shift+scroll)
            for _ in range(min(amount, 10)):  # limit to 10 presses per frame
                if direction == 'right':
                    pyautogui.press('right')
                else:
                    pyautogui.press('left')
            print(f"Action: Scroll {direction} {amount}")

    def toggle_virtual_keyboard(self):
        """Toggle on-screen keyboard visibility (Linux: onboard, etc.)."""
        if self.keyboard_visible:
            # Hide keyboard
            pyautogui.hotkey('ctrl', 'alt', 'k')  # example shortcut; adjust as needed
            print("Virtual keyboard off")
        else:
            pyautogui.hotkey('ctrl', 'alt', 'k')
            print("Virtual keyboard on")
        self.keyboard_visible = not self.keyboard_visible

    def execute_gestures(self, gestures: Set[str],
                         index_tip_pos: Optional[Tuple[float, float]] = None,
                         hand_movement: Optional[Tuple[float, float]] = None,
                         double_tap: bool = False):
        """
        Execute actions based on recognized gestures.

        Args:
            gestures: Set of gesture strings.
            index_tip_pos: (x,y) normalized for cursor control.
            hand_movement: (dx, dy) normalized movement for scrolling.
            double_tap: whether a double tap was detected.
        """
        # Fist: reset cooldown
        if 'fist' in gestures:
            self.last_fist_time = time.time()
            # Also reset scroll direction to avoid stuck state
            self.last_scroll_direction = None
            return

        # Only index up -> cursor tracking
        if 'only_index_up' in gestures and index_tip_pos is not None:
            self.update_cursor(index_tip_pos)

        # Double tap (detected separately)
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

