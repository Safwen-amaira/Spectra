"""
Main entry point for Spectra.
Captures webcam feed, tracks hands, recognizes gestures, and triggers actions.
"""

import cv2
import sys
from src.hand_tracker import HandTracker
from src.gesture_recognizer import GestureRecognizer
from src.action_controller import ActionController


def main():
    """Run the main hand-control loop."""
    # Initialize components
    hand_tracker = HandTracker()
    gesture_recognizer = GestureRecognizer(pinch_threshold=0.05)
    action_controller = ActionController()

    # Open webcam (default device 0)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        sys.exit(1)

    print("Spectra started. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Process frame and get hand landmarks
        annotated_frame, hand_landmarks_list = hand_tracker.process_frame(frame)

        # Recognize gestures from all detected hands
        gestures = gesture_recognizer.get_active_gestures(hand_landmarks_list)
        # Remove duplicates (multiple hands performing same gesture)
        unique_gestures = set(gestures)
        action_controller.execute_gestures(unique_gestures)

        # Display the annotated frame
        cv2.imshow('Spectra - Hand Control', annotated_frame)

        # Exit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    hand_tracker.release()
    print("Spectra stopped.")


if __name__ == "__main__":
    main()

