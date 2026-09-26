// ========================================
// DASHBOARD CAM
// ========================================

// Alarm sound
const alarmSound = new Audio("/alarm.mp3");

// Make the alarm repeat while it is active
alarmSound.loop = false;

// Alarm status
let alarmEnabled = false;

// Remember the last alert time
let lastAlertTime = null;


// ========================================
// ENABLE ALARM BUTTON
// ========================================

document.getElementById("enableAlarm").addEventListener(
    "click",
    function () {

        alarmEnabled = true;

        this.textContent = "🔔 Alarm Enabled";

        // Test the alarm and unlock browser audio
        alarmSound.currentTime = 0;

        alarmSound.play()
            .then(() => {

                // Stop the test sound
                alarmSound.pause();

                alarmSound.currentTime = 0;

                console.log("Alarm enabled successfully.");

            })
            .catch(error => {

                console.error(
                    "Could not enable alarm:",
                    error
                );

            });
    }
);


// ========================================
// CHECK SERVER
// ========================================

function checkServer() {

    fetch("/api/alert")
        .then(response => {

            if (!response.ok) {

                throw new Error(
                    "Server returned an error."
                );
            }

            return response.json();
        })

        .then(data => {

            console.log(
                "Server response:",
                data
            );


            // ========================================
            // ALERT DETECTED
            // ========================================

            if (data.alert) {

                document.getElementById("status").textContent =
                    "🚨 ALERT DETECTED!";


                // ========================================
                // CHECK FOR NEW ALERT
                // ========================================

                if (
                    alarmEnabled &&
                    data.time &&
                    data.time !== lastAlertTime
                ) {

                    console.log(
                        "NEW ALERT DETECTED!"
                    );

                    console.log(
                        "Playing alarm..."
                    );


                    // Remember this alert
                    lastAlertTime = data.time;


                    // Start alarm
                    alarmSound.currentTime = 0;

                    alarmSound.play()
                        .then(() => {

                            console.log(
                                "🚨 ALARM IS RINGING!"
                            );

                        })
                        .catch(error => {

                            console.error(
                                "ALARM ERROR:",
                                error
                            );

                        });
                }


                // ========================================
                // SHOW ALERT IMAGE
                // ========================================

                document.getElementById(
                    "alertImage"
                ).src =
                    "/alert.jpg?" +
                    new Date().getTime();

                document.getElementById(
                    "alertImage"
                ).style.display = "block";

                document.getElementById(
                    "noImage"
                ).style.display = "none";


                // ========================================
                // SHOW TIME
                // ========================================

                document.getElementById(
                    "alertTime"
                ).textContent =
                    "Time: " + data.time;


                // ========================================
                // SHOW LOCATION
                // ========================================

                if (
                    data.latitude &&
                    data.longitude
                ) {

                    document.getElementById(
                        "location"
                    ).textContent =
                        "Location: " +
                        data.latitude +
                        ", " +
                        data.longitude;


                    if (data.maps) {

                        document.getElementById(
                            "mapsLink"
                        ).href = data.maps;

                        document.getElementById(
                            "mapsLink"
                        ).style.display =
                            "inline-block";
                    }

                } else {

                    document.getElementById(
                        "location"
                    ).textContent =
                        "Location: Could not be found";
                }

            }


            // ========================================
            // NO ALERT
            // ========================================

            else {

                document.getElementById(
                    "status"
                ).textContent =
                    "System connected - waiting for an alert...";
            }

        })

        .catch(error => {

            document.getElementById(
                "status"
            ).textContent =
                "Dashboard server is not connected.";

            console.error(
                "Connection error:",
                error
            );

        });
}


// ========================================
// START CHECKING
// ========================================

// Check immediately
checkServer();

// Check every second
setInterval(
    checkServer,
    1000
);