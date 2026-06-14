"""
Gesture recognition module with advanced gestures.
Detects finger extensions, pinches, double taps, fist, and two-hand gestures.
"""

import math
import time
from typing import List, Tuple, Optional, Set

class GestureRecognizer:
    """Recognizes advanced hand gestures."""

    # MediaPipe landmark indices
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12
    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

    # Pinch threshold
    PINCH_THRESHOLD = 0.05

    def __init__(self, pinch_threshold: float = 0.05):
        self.pinch_threshold = pinch_threshold
        # Double tap detection state
        self.last_index_tap_time = 0
        self.index_tap_cooldown = 0.5  # seconds
        self.last_gestures: Set[str] = set()

    @staticmethod
    def _distance(point1: Tuple[float, float, float],
                  point2: Tuple[float, float, float]) -> float:
        return math.sqrt((point1[0]-point2[0])**2 +
                         (point1[1]-point2[1])**2 +
                         (point1[2]-point2[2])**2)

    def is_pinch(self, landmarks: List[Tuple[float, float, float]],
                 finger_tip_index: int) -> bool:
        thumb_pos = landmarks[self.THUMB_TIP]
        finger_pos = landmarks[finger_tip_index]
        return self._distance(thumb_pos, finger_pos) < self.pinch_threshold

    def is_finger_extended(self, landmarks: List[Tuple[float, float, float]],
                           tip_idx: int, pip_idx: int) -> bool:
        """
        Check if a finger is extended (straight) by comparing tip and PIP y-coordinate.
        In normalized image coordinates (0..1), y increases downward.
        Extended finger: tip_y < pip_y (finger pointing up).
        """
        tip_y = landmarks[tip_idx][1]
        pip_y = landmarks[pip_idx][1]
        return tip_y < pip_y

    def get_finger_states(self, landmarks: List[Tuple[float, float, float]]) -> dict:
        """Return dict with booleans for each finger: thumb, index, middle, ring, pinky."""
        # Thumb extension is different; treat as "up" if thumb tip is far from index base
        thumb_tip = landmarks[self.THUMB_TIP]
        index_mcp = landmarks[self.INDEX_MCP]
        thumb_extended = self._distance(thumb_tip, index_mcp) > 0.1  # rough threshold

        index_extended = self.is_finger_extended(landmarks, self.INDEX_TIP, self.INDEX_PIP)
        middle_extended = self.is_finger_extended(landmarks, self.MIDDLE_TIP, self.MIDDLE_PIP)
        ring_extended = self.is_finger_extended(landmarks, self.RING_TIP, self.RING_PIP)
        pinky_extended = self.is_finger_extended(landmarks, self.PINKY_TIP, self.PINKY_PIP)

        return {
            'thumb': thumb_extended,
            'index': index_extended,
            'middle': middle_extended,
            'ring': ring_extended,
            'pinky': pinky_extended
        }

    def recognize_single_hand_gestures(self, landmarks: List[Tuple[float, float, float]]) -> Set[str]:
        """
        Recognize gestures from one hand.
        Returns set of gesture names: 'only_index_up', 'index_middle_up', 'fist', 'click', 'zoom_in', 'zoom_out'
        """
        gestures = set()
        finger_states = self.get_finger_states(landmarks)

        # Fist: all fingers not extended (thumb also not extended)
        if not any([finger_states['index'], finger_states['middle'],
                    finger_states['ring'], finger_states['pinky'], finger_states['thumb']]):
            gestures.add('fist')

        # Only index finger up (others down)
        if (finger_states['index'] and not finger_states['middle'] and
            not finger_states['ring'] and not finger_states['pinky']):
            gestures.add('only_index_up')

        # Index and middle up (others down)
        if (finger_states['index'] and finger_states['middle'] and
            not finger_states['ring'] and not finger_states['pinky']):
            gestures.add('index_middle_up')

        # Pinch gestures (always detected regardless of other fingers)
        if self.is_pinch(landmarks, self.INDEX_TIP):
            gestures.add('click')
        if self.is_pinch(landmarks, self.MIDDLE_TIP):
            gestures.add('zoom_in')
        if self.is_pinch(landmarks, self.RING_TIP):
            gestures.add('zoom_out')

        return gestures

    def detect_double_tap(self, current_gestures: Set[str], prev_gestures: Set[str]) -> bool:
        """Detect double tap on index finger (down-up-down within cooldown)."""
        now = time.time()
        tap_detected = False
        if 'only_index_up' in current_gestures and 'only_index_up' not in prev_gestures:
            # rising edge: index just went up
            if now - self.last_index_tap_time < self.index_tap_cooldown:
                tap_detected = True
            self.last_index_tap_time = now
        return tap_detected

    def get_two_hand_gestures(self, hand_landmarks_list: List[List[Tuple[float, float, float]]]) -> Set[str]:
        """
        Detect gestures involving two hands: both thumb-index pinch (together) and clap.
        Returns set of 'keyboard_toggle', 'clap'
        """
        if len(hand_landmarks_list) < 2:
            return set()

        # For simplicity, assume first two hands are left and right
        left = hand_landmarks_list[0]
        right = hand_landmarks_list[1]

        left_pinch = self.is_pinch(left, self.INDEX_TIP)
        right_pinch = self.is_pinch(right, self.INDEX_TIP)

        if left_pinch and right_pinch:
            # Both hands pinching thumb+index
            # Measure distance between left thumb and right thumb
            left_thumb = left[self.THUMB_TIP]
            right_thumb = right[self.THUMB_TIP]
            dist = self._distance(left_thumb, right_thumb)
            if dist < 0.15:  # hands close together (touching)
                return {'clap'}
            else:
                return {'keyboard_toggle'}
        return set()

