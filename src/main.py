"""
Main entry point for Spectra - Advanced hand control.
"""

import cv2
import sys
import numpy as np
from src.hand_tracker import HandTracker
from src.gesture_recognizer import GestureRecognizer
from src.action_controller import ActionController

def main():
    hand_tracker = HandTracker()
    gesture_recognizer = GestureRecognizer(pinch_threshold=0.05)
    action_controller = ActionController()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        sys.exit(1)

    print("Spectra Advanced started. Press 'q' to quit.")

    # State for double tap detection
    prev_gestures = set()
    # State for hand movement tracking (scrolling)
    prev_hand_center = None  # (x, y) normalized

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        annotated_frame, hand_landmarks_list = hand_tracker.process_frame(frame)

        # Detect gestures for each hand (we'll take first hand for single-hand gestures)
        all_gestures = set()
        index_tip_pos = None
        hand_center = None

        if hand_landmarks_list:
            # Use first hand for single-hand gestures and cursor/scroll
            first_hand = hand_landmarks_list[0]
            gestures = gesture_recognizer.recognize_single_hand_gestures(first_hand)
            all_gestures.update(gestures)

            # Get index tip position for cursor tracking (normalized x,y)
            index_tip = first_hand[GestureRecognizer.INDEX_TIP]
            index_tip_pos = (index_tip[0], index_tip[1])

            # Compute hand center (wrist)
            wrist = first_hand[GestureRecognizer.WRIST]
            hand_center = (wrist[0], wrist[1])

        # Double tap detection (comparing current and previous 'only_index_up')
        double_tap = gesture_recognizer.detect_double_tap(all_gestures, prev_gestures)

        # Compute hand movement for scrolling (if index+middle up)
        hand_movement = None
        if 'index_middle_up' in all_gestures and prev_hand_center is not None and hand_center is not None:
            dx = hand_center[0] - prev_hand_center[0]
            dy = hand_center[1] - prev_hand_center[1]
            # Scale for sensitivity
            dx = dx * action_controller.cursor_speed
            dy = dy * action_controller.cursor_speed
            hand_movement = (dx, dy)
        elif hand_center is not None:
            # Update previous center even if gesture not active? No, only when active we want delta.
            # We need to update prev_hand_center always for next frame's delta, but careful.
            # Actually we should update prev_hand_center regardless, so that when gesture becomes active we have a baseline.
            pass

        # Execute actions
        action_controller.execute_gestures(
            all_gestures,
            index_tip_pos=index_tip_pos if 'only_index_up' in all_gestures else None,
            hand_movement=hand_movement,
            double_tap=double_tap
        )

        # Two-hand gestures (if two hands present)
        if len(hand_landmarks_list) >= 2:
            two_hand_gestures = gesture_recognizer.get_two_hand_gestures(hand_landmarks_list)
            if 'keyboard_toggle' in two_hand_gestures:
                action_controller.toggle_virtual_keyboard()
            elif 'clap' in two_hand_gestures:
                # Clap toggles keyboard off (specific)
                if action_controller.keyboard_visible:
                    action_controller.toggle_virtual_keyboard()

        # Update previous state
        prev_gestures = all_gestures.copy()
        if hand_center is not None:
            prev_hand_center = hand_center

        # Display
        cv2.imshow('Spectra - Advanced Hand Control', annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    hand_tracker.release()
    print("Spectra stopped.")

if __name__ == "__main__":
    main()

