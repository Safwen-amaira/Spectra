"""
Hand tracking module using MediaPipe.
Detects hand landmarks from webcam frames.
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import List, Tuple, Optional


class HandTracker:
    """Hand landmark detector and tracker."""

    def __init__(self,
                 static_image_mode: bool = False,
                 max_num_hands: int = 2,
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5):
        """
        Initialize MediaPipe Hands solution.

        Args:
            static_image_mode: Whether to treat input as static images.
            max_num_hands: Maximum number of hands to detect.
            min_detection_confidence: Minimum confidence for detection.
            min_tracking_confidence: Minimum confidence for tracking.
        """
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[List]]:
        """
        Process a BGR frame and draw hand landmarks.

        Args:
            frame: Input image in BGR format.

        Returns:
            Tuple of (annotated_frame, hand_landmarks_list)
            hand_landmarks_list is a list of lists of (x,y,z) for each hand.
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        annotated_frame = frame.copy()
        hand_landmarks_list = []

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Extract landmarks as (x, y, z) normalized coordinates
                landmarks = [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]
                hand_landmarks_list.append(landmarks)

                # Draw landmarks and connections on the annotated frame
                self.mp_drawing.draw_landmarks(
                    annotated_frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )

        return annotated_frame, hand_landmarks_list

    def release(self):
        """Release MediaPipe resources."""
        self.hands.close()

