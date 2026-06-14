"""
Gesture recognition module.
Detects finger collapse (pinch) between thumb and other fingertips.
"""

import math
from typing import List, Tuple, Optional


class GestureRecognizer:
    """Recognizes hand gestures based on landmark distances."""

    # MediaPipe hand landmark indices
    THUMB_TIP = 4
    INDEX_TIP = 8
    MIDDLE_TIP = 12
    RING_TIP = 16
    PINKY_TIP = 20

    # Distance threshold (normalized coordinates, approx 0-1)
    PINCH_THRESHOLD = 0.05

    def __init__(self, pinch_threshold: float = 0.05):
        """
        Initialize recognizer.

        Args:
            pinch_threshold: Maximum normalized distance between thumb and
                             another fingertip to consider them "collapsed".
        """
        self.pinch_threshold = pinch_threshold

    @staticmethod
    def _distance(point1: Tuple[float, float, float],
                  point2: Tuple[float, float, float]) -> float:
        """Euclidean distance between two 3D points."""
        return math.sqrt((point1[0] - point2[0]) ** 2 +
                         (point1[1] - point2[1]) ** 2 +
                         (point1[2] - point2[2]) ** 2)

    def is_pinch(self,
                 landmarks: List[Tuple[float, float, float]],
                 finger_tip_index: int) -> bool:
        """
        Check if thumb tip is pinched with a given finger tip.

        Args:
            landmarks: List of 21 hand landmarks (x,y,z normalized).
            finger_tip_index: MediaPipe index of the finger tip to check.

        Returns:
            True if distance between thumb tip and finger tip is below threshold.
        """
        thumb_pos = landmarks[self.THUMB_TIP]
        finger_pos = landmarks[finger_tip_index]
        dist = self._distance(thumb_pos, finger_pos)
        return dist < self.pinch_threshold

    def get_active_gestures(self,
                            hand_landmarks_list: List[List[Tuple[float, float, float]]]
                            ) -> List[str]:
        """
        Analyze all detected hands and return list of active gesture names.

        Gestures:
            - "click": thumb + index pinch
            - "zoom_in": thumb + middle pinch
            - "zoom_out": thumb + ring pinch

        Args:
            hand_landmarks_list: List of hand landmark sets (each is list of 21 points).

        Returns:
            List of gesture strings (may contain duplicates if multiple hands).
        """
        gestures = []
        for landmarks in hand_landmarks_list:
            if self.is_pinch(landmarks, self.INDEX_TIP):
                gestures.append("click")
            if self.is_pinch(landmarks, self.MIDDLE_TIP):
                gestures.append("zoom_in")
            if self.is_pinch(landmarks, self.RING_TIP):
                gestures.append("zoom_out")
        return gestures

