import serial
import time
import threading
from arduino.app_utils import App, Bridge # Added Bridge for STM32 MCU communications
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection
from datetime import datetime, UTC

# ==========================================
# 1. HC-05 BLUETOOTH SERIAL SETUP
# ==========================================
serial_port = '/dev/ttyUSB0'
baud_rate = 9600 

print(f"Attempting to connect to HC-05 on {serial_port}...")
try:
    hc05 = serial.Serial(serial_port, baud_rate, timeout=1)
    print("SUCCESS: HC-05 Serial connection established!")
except Exception as e:
    print(f"WARNING: Could not open serial port. Is the USB adapter plugged in?")
    print(f"Error details: {e}")
    hc05 = None 

# ==========================================
# 2. ARDUINO APP LAB & NAVIGATION SETUP
# ==========================================
ui = WebUI()
detection_stream = VideoObjectDetection(confidence=0.5, debounce_sec=0.0)

# --- Navigation Zones ---
FRAME_WIDTH = 640 
LEFT_ZONE = FRAME_WIDTH / 3
RIGHT_ZONE = (FRAME_WIDTH / 3) * 2

# --- Thread Shared States & Locks ---
state_lock = threading.Lock()
last_bt_send_time = 0
cooldown_seconds = 5 

# Shared variables updated by camera and read by alert loop
latest_object = None
latest_center_x = None
last_camera_update_time = 0

def safe_override(sid, threshold):
    try:
        detection_stream.override_threshold(threshold)
    except AttributeError:
        pass

ui.on_message("override_th", safe_override)

# ==========================================
# 3. CAMERA DETECTION CALLBACK
# ==========================================
def send_detections_to_ui(detections: dict):
    global latest_object, latest_center_x, last_camera_update_time
    
    highest_conf_obj = None
    highest_conf_val = 0
    center_point = None

    # Process and send to UI Web Dashboard
    for key, values in detections.items():
        for value in values:
            conf = value.get("confidence", 0)
            
            entry = {
                "content": key,
                "confidence": conf,
                "timestamp": datetime.now(UTC).isoformat()
            }
            ui.send_message("detection", message=entry)

            # Find the most confident AI object in this frame
            if conf > highest_conf_val:
                highest_conf_val = conf
                highest_conf_obj = key
                
                bbox = value.get("bounding_box_xyxy")
                if bbox and len(bbox) == 4:
                    x1, _, x2, _ = bbox
                    center_point = (x1 + x2) / 2

    # Safely update shared state for the asynchronous alert loop
    with state_lock:
        latest_object = highest_conf_obj
        latest_center_x = center_point
        last_camera_update_time = time.time()

# Register the callback function
detection_stream.on_detect_all(send_detections_to_ui)

# ==========================================
# 4. INDEPENDENT HARDWARE & ALERT LOOP (THREAD)
# ==========================================
def asynchronous_alert_worker():
    global last_bt_send_time, latest_object, latest_center_x
    
    print("Asynchronous Hardware Alert loop started.")
    while True:
        # 4a. Read Real-time Distance directly from Ultrasonic Sensor
        try:
            hardware_distance = Bridge.call("get_distance")
        except Exception as e:
            hardware_distance = 999.0

        current_time = time.time()
        
        # Safely fetch snapshot of latest camera targets
        with state_lock:
            # If camera data is older than 1.5 seconds, consider it expired/stale
            if current_time - last_camera_update_time > 1.5:
                highest_conf_obj = None
                center_point = None
            else:
                highest_conf_obj = latest_object
                center_point = latest_center_x

        # 4b. Voice Alert Logic with Crisp Ultrasonic Priority
        if hc05 is not None:
            # CRITICAL OVERRIDE: Check if anything is within 35cm (Immediate Action)
            # We skip the standard 5s cooldown if an obstacle suddenly pops up close!
            if hardware_distance <= 35.0:
                # Prevent spamming the serial line too aggressively (0.8s emergency pacing)
                if (current_time - last_bt_send_time) > 0.8:
                    message = f"warning close obstacle detected {int(hardware_distance)} centimeters away\n"
                    print(f"CRITICAL OVERRIDE: Obstacle at {hardware_distance:.1f} cm! Sending Bluetooth Alert.")
                    try:
                        hc05.write(message.encode('utf-8'))
                        last_bt_send_time = current_time
                    except Exception as e:
                        print(f"Serial write error: {e}")
            
            # STANDARD NAVIGATION LOGIC (Enforces standard 5-second cooldown)
            elif (current_time - last_bt_send_time) > cooldown_seconds:
                message = None
                
                if highest_conf_obj is not None:
                    if center_point is None:
                        direction = "ahead"
                    else:
                        if center_point < LEFT_ZONE:
                            direction = "on left, turn slight right"
                        elif center_point > RIGHT_ZONE:
                            direction = "on right, turn slight left"
                        else:
                            direction = "directly ahead, please turn left or right"
                    
                    message = f"{highest_conf_obj} {direction}\n"
                    print(f"AI Detection Sent: {message.strip()} (Center X: {center_point})")
                    
                else:
                    message = "Path clear, walk straight\n"
                    print("Environment Status: All Clear.")
                
                if message:
                    try:
                        hc05.write(message.encode('utf-8'))
                        last_bt_send_time = current_time
                    except Exception as e:
                        print(f"Serial write error: {e}")

        # High polling frequency for the ultrasonic loop (100ms)
        time.sleep(0.1)

# Start the hardware background thread before opening App UI loop
alert_thread = threading.Thread(target=asynchronous_alert_worker, daemon=True)
alert_thread.start()

# Start the application
App.run()
