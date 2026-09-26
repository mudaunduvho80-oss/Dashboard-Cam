# ========================================
# DASHBOARD CAM
# ========================================

# Import os so we can find project files correctly
import os

# Import threading so the camera and website can run at the same time
import threading

# Import OpenCV so we can use the computer camera
import cv2

# Import MediaPipe so we can detect an open palm
import mediapipe as mp

# Import Flask so Python can run our local website
from flask import Flask, send_from_directory

# Import datetime so we can record the alert time
from datetime import datetime

# Import requests so we can get approximate location information
import requests

# Import the MediaPipe tools needed for hand detection
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# ========================================
# PROJECT FOLDERS
# ========================================

# Get the folder where main.py is located
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# Find the website folder
WEBSITE_DIR = os.path.join(
    BASE_DIR,
    "Website_Security"
)


# ========================================
# FLASK WEBSITE
# ========================================

# Create the Flask website
app = Flask(__name__)


# ========================================
# WEBSITE ROUTES
# ========================================

# Open the main website page
@app.route("/")
def home():

    return send_from_directory(
        WEBSITE_DIR,
        "index.html"
    )


# Send the CSS file to the browser
@app.route("/style.css")
def style():

    return send_from_directory(
        WEBSITE_DIR,
        "style.css"
    )


# Send the JavaScript file to the browser
@app.route("/script.js")
def script():

    return send_from_directory(
        WEBSITE_DIR,
        "script.js"
    )


# Send the background video to the browser
@app.route("/Home.mp4")
def background_video():

    return send_from_directory(
        WEBSITE_DIR,
        "Home.mp4"
    )


# Send the Dashboard Cam logo
@app.route("/logo.jpeg")
def logo():

    return send_from_directory(
        WEBSITE_DIR,
        "logo.jpeg"
    )


# Send the alarm sound
@app.route("/alarm.mp3")
def alarm_sound():

    return send_from_directory(
        WEBSITE_DIR,
        "alarm.mp3"
    )


# Send the alert picture
@app.route("/alert.jpg")
def alert_image():

    return send_from_directory(
        BASE_DIR,
        "alert.jpg"
    )


# ========================================
# ALERT API
# ========================================

# Send alert information to the website
@app.route("/api/alert")
def alert_information():

    # Find the alert information file
    alert_file = os.path.join(
        BASE_DIR,
        "alert.txt"
    )

    # If there is no alert file,
    # tell the website there is no alert
    if not os.path.exists(alert_file):

        return {
            "alert": False
        }


    # Create empty alert values
    alert_time = ""
    latitude = ""
    longitude = ""
    maps_link = ""


    # Read the alert information
    try:

        with open(
            alert_file,
            "r",
            encoding="utf-8"
        ) as file:

            lines = file.readlines()

    except Exception as error:

        print(
            "Could not read alert file:",
            error
        )

        return {
            "alert": False
        }


    # Read each line
    for line in lines:

        # Read alert time
        if line.startswith("Time:"):

            alert_time = line.replace(
                "Time:",
                ""
            ).strip()


        # Read latitude
        elif line.startswith("Latitude:"):

            latitude = line.replace(
                "Latitude:",
                ""
            ).strip()


        # Read longitude
        elif line.startswith("Longitude:"):

            longitude = line.replace(
                "Longitude:",
                ""
            ).strip()


        # Read Google Maps link
        elif line.startswith("Google Maps:"):

            maps_link = line.replace(
                "Google Maps:",
                ""
            ).strip()


    # Send information to JavaScript
    return {
        "alert": True,
        "time": alert_time,
        "latitude": latitude,
        "longitude": longitude,
        "maps": maps_link
    }


# ========================================
# START WEBSITE
# ========================================

def start_website():

    # Start Flask
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )


# Create website thread
website_thread = threading.Thread(
    target=start_website,
    daemon=True
)

# Start website
website_thread.start()


# Show website information
print()
print("================================")
print("       DASHBOARD CAM WEBSITE")
print("================================")
print("Website:")
print("http://127.0.0.1:5000")
print("================================")
print()


# ========================================
# MEDIAPIPE HAND DETECTION
# ========================================

# Find the MediaPipe model
MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "hand_landmarker.task"
)


# Configure MediaPipe
base_options = python.BaseOptions(
    model_asset_path=MODEL_PATH
)


# Configure the hand detector
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1
)


# Create the hand detector
detector = vision.HandLandmarker.create_from_options(
    options
)


# ========================================
# CAMERA
# ========================================

# Open the default camera
camera = cv2.VideoCapture(1)


# Check if camera opened successfully
if not camera.isOpened():

    print("ERROR: Could not open the camera.")
    detector.close()
    raise SystemExit


# MediaPipe timestamp
timestamp = 0


# This prevents the same open palm
# from creating many alerts continuously
alert_sent = False


# ========================================
# LOCATION
# ========================================

def get_location():

    # Request approximate location
    response = requests.get(
        "http://ip-api.com/json/",
        timeout=5
    )

    # Convert response to Python data
    data = response.json()

    # Check whether location was found
    if data.get("status") == "success":

        # Get latitude
        latitude = data["lat"]

        # Get longitude
        longitude = data["lon"]

        # Create Google Maps link
        maps_link = (
            f"https://www.google.com/maps?q="
            f"{latitude},{longitude}"
        )

        # Return location information
        return (
            latitude,
            longitude,
            maps_link
        )


    # Location unavailable
    return (
        None,
        None,
        None
    )


# ========================================
# CAMERA LOOP
# ========================================

print("Camera started.")
print("Show an open palm to create an alert.")
print("Press Q to stop.")
print()


while True:

    # Capture camera frame
    success, frame = camera.read()


    # Stop if camera fails
    if not success:

        print(
            "ERROR: Could not read camera frame."
        )

        break


    # Flip camera horizontally
    frame = cv2.flip(
        frame,
        1
    )


    # Convert BGR to RGB
    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    # Create MediaPipe image
    image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )


    # Increase timestamp
    timestamp += 1


    # Detect hand
    result = detector.detect_for_video(
        image,
        timestamp
    )


    # ========================================
    # OPEN PALM DETECTION
    # ========================================

    # Variable to remember whether
    # an open palm is currently visible
    open_palm_detected = False


    # Check if a hand was detected
    if result.hand_landmarks:

        # Get first hand
        hand = result.hand_landmarks[0]


        # Check index finger
        index = (
            hand[8].y <
            hand[6].y
        )


        # Check middle finger
        middle = (
            hand[12].y <
            hand[10].y
        )


        # Check ring finger
        ring = (
            hand[16].y <
            hand[14].y
        )


        # Check little finger
        pinky = (
            hand[20].y <
            hand[18].y
        )


        # Check if all four fingers are raised
        if (
            index
            and middle
            and ring
            and pinky
        ):

            open_palm_detected = True


            # Display detection message
            cv2.putText(
                frame,
                "OPEN PALM DETECTED!",
                (30, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )


    # ========================================
    # CREATE ALERT
    # ========================================

    if open_palm_detected:

        # Only create an alert if one
        # has not already been created
        if not alert_sent:

            # Get current date and time
            alert_time = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )


            # ========================================
            # GET LOCATION
            # ========================================

            try:

                latitude, longitude, maps_link = (
                    get_location()
                )

            except Exception as error:

                print(
                    "Location error:",
                    error
                )

                latitude = None
                longitude = None
                maps_link = None


            # ========================================
            # SAVE ALERT IMAGE
            # ========================================

            alert_picture = os.path.join(
                BASE_DIR,
                "alert.jpg"
            )


            # Save current camera frame
            cv2.imwrite(
                alert_picture,
                frame
            )


            # ========================================
            # SAVE ALERT INFORMATION
            # ========================================

            alert_file = os.path.join(
                BASE_DIR,
                "alert.txt"
            )


            with open(
                alert_file,
                "w",
                encoding="utf-8"
            ) as file:

                # Alert type
                file.write(
                    "ALERT: Open Palm Detected\n"
                )

                # Alert time
                file.write(
                    f"Time: {alert_time}\n"
                )


                # Save location
                if latitude is not None:

                    file.write(
                        f"Latitude: {latitude}\n"
                    )

                    file.write(
                        f"Longitude: {longitude}\n"
                    )

                    file.write(
                        f"Google Maps: {maps_link}\n"
                    )

                else:

                    file.write(
                        "Location: Could not be found\n"
                    )


            # ========================================
            # SHOW ALERT IN TERMINAL
            # ========================================

            print()
            print("================================")
            print("        OPEN PALM ALERT")
            print("================================")
            print(
                "Time:",
                alert_time
            )


            # Display location
            if latitude is not None:

                print(
                    "Latitude:",
                    latitude
                )

                print(
                    "Longitude:",
                    longitude
                )

                print(
                    "Google Maps:",
                    maps_link
                )

            else:

                print(
                    "Location could not be found"
                )


            print(
                "Picture saved as: alert.jpg"
            )

            print(
                "Alert information saved as: alert.txt"
            )

            print("================================")
            print()


            # Remember that an alert was created
            alert_sent = True


    else:

        # The open palm is no longer visible.
        #
        # This allows another open palm
        # to create a new alert later.
        alert_sent = False


    # ========================================
    # SHOW CAMERA
    # ========================================

    cv2.imshow(
        "Dashboard Cam",
        frame
    )


    # ========================================
    # STOP CAMERA
    # ========================================

    # Press Q to stop
    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# ========================================
# CLEAN UP
# ========================================

# Release camera
camera.release()


# Close OpenCV windows
cv2.destroyAllWindows()


# Close MediaPipe detector
detector.close()


print()
print("Dashboard Cam stopped.")