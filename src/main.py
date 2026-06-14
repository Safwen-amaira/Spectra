"""
Main entry point for Spectra - Advanced hand control.
"""

import cv2
import sys
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

    # Set higher resolution for better tracking? Optional
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Spectra Advanced started. Press 'q' to quit.")

    prev_gestures = set()
    prev_hand_center = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        annotated_frame, hand_landmarks_list = hand_tracker.process_frame(frame)

        all_gestures = set()
        index_tip_pos = None
        hand_center = None

        if hand_landmarks_list:
            first_hand = hand_landmarks_list[0]
            gestures = gesture_recognizer.recognize_single_hand_gestures(first_hand)
            all_gestures.update(gestures)

            index_tip = first_hand[GestureRecognizer.INDEX_TIP]
            # No inversion here; inversion done in action_controller
            index_tip_pos = (index_tip[0], index_tip[1])

            wrist = first_hand[GestureRecognizer.WRIST]
            hand_center = (wrist[0], wrist[1])

        double_tap = gesture_recognizer.detect_double_tap(all_gestures, prev_gestures)

        hand_movement = None
        if 'index_middle_up' in all_gestures and prev_hand_center is not None and hand_center is not None:
            dx = hand_center[0] - prev_hand_center[0]
            dy = hand_center[1] - prev_hand_center[1]
            # Increase sensitivity for scrolling
            dx = dx * 8.0
            dy = dy * 8.0
            hand_movement = (dx, dy)
        # Update prev_hand_center regardless (if hand_center exists)
        if hand_center is not None:
            prev_hand_center = hand_center

        action_controller.execute_gestures(
            all_gestures,
            index_tip_pos=index_tip_pos if 'only_index_up' in all_gestures else None,
            hand_movement=hand_movement,
            double_tap=double_tap
        )

        # Two-hand gestures
        if len(hand_landmarks_list) >= 2:
            two_hand_gestures = gesture_recognizer.get_two_hand_gestures(hand_landmarks_list)
            if 'keyboard_toggle' in two_hand_gestures:
                action_controller.toggle_virtual_keyboard()
            elif 'clap' in two_hand_gestures:
                if action_controller.keyboard_visible:
                    action_controller.toggle_virtual_keyboard()

        prev_gestures = all_gestures.copy()

        cv2.imshow('Spectra - Advanced Hand Control', annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    hand_tracker.release()
    print("Spectra stopped.")

if __name__ == "__main__":
    main()

