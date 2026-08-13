# 🕶️ EyeSense - AI Enabled Smart Blind Glasses

An intelligent assistive wearable system designed to enhance the mobility, independence, and situational awareness of visually impaired individuals through real-time environmental perception and voice-guided navigation. 

By combining edge-based AI vision, ultrasonic proximity sensing, Bluetooth communication, and smartphone-assisted voice navigation into a single platform, EyeSense provides an affordable and reliable mobility aid.

---

## 📸 Product Preview

<p align="center">
  <img src="Assets/Product%20Image.png" width="300" alt="EyeSense Prototype">
</p>

---

## 🚀 Key Features

* 👁️ **Real-Time Obstacle Mapping:** Scans the path ahead up to 35cm away to prevent hazards.
* 🤖 **Intelligent Object Classification:** Powered by low-latency local object detection (YOLOv8-tiny) running at 30 FPS.
* ⚡ **Ultra-Low Latency:** Features a stable serial-to-Bluetooth pipeline under 100 milliseconds.
* ☁️ **Zero Cloud Dependency:** Runs entirely locally on the board for reliability in rural or low-connectivity zones.
* 🔋 **Extended Battery Life:** A 10,000mAh power bank supplies up to 12 hours of continuous usage.
* 🗣️ **Auditory Navigation:** Feeds natural Text-to-Speech (TTS) voice alerts directly to the user's phone or headset.

---

## 🛠️ Hardware Architecture & BOM

The system utilizes an integrated star-bus topology managed by a central hub.

| Component Name | Qty | Profile & Purpose |
| :--- | :---: | :--- |
| **Arduino UNO Q** | 1 | Master microcontroller; handles local telemetry and sensor processing. |
| **USB-C Hub** | 1 | Hardware bus expansion; maps downstream ports. |
| **USB 3.0 1080P Webcam** | 1 | High-definition vision capture for the computer vision pipeline. |
| **USB 2.0 to TTL Adapter** | 1 | Bridges standard USB interface to logic-level serial pins (CH340/CP2102). |
| **HC-05 Bluetooth Module** | 1 | Wireless telemetry link mapping communication to the companion app. |
| **HC-SR04 Ultrasonic Sensor** | 1 | Physical proximity rangefinder tracking real-time collision boundaries. |
| **45W USB-C PD Power Supply** | 1 | Centralized system power distributor. |

### 🔌 Circuit Interconnections

<p align="center">
  <img src="Schematics/Circuit%20Diagram.png" width="550" alt="EyeSense Circuit Diagram">
</p>

---

## ⚙️ Application Configuration Files

### `app.yaml`
```yaml
name: Detect Objects on Camera
icon: 📽️
description: This example showcases object detection within a live feed from a USB camera.
bricks:
  - arduino:video_object_detection
  - arduino:web_ui
devices: { dev: ["/dev/ttyUSB0"] }
```

### `sketch.yaml`
```yaml
profiles:
  default:
    fqbn: arduino:zephyr:unoq
    platforms:
      - platform: arduino:zephyr
    libraries:
      - Arduino_RouterBridge (0.3.0)
      - dependency: Arduino_RPClite (0.2.1)
      - dependency: ArxContainer (0.7.0)
      - dependency: ArxTypeTraits (0.3.2)
      - dependency: DebugLog (0.8.4)
      - dependency: MsgPack (0.4.2)

default_profile: default
```

---

## 💻 Execution & Deployment CLI

### 1. Start the App
Navigate to your application folder and initiate the environment using the CLI execution command:
```bash
cd <YOUR_PROJECT_PATH>
arduino-app-cli app start "."
```

### 2. View Live Stream & Container Logs
Monitor active camera feed streams, real-time object detection matrices, or the physical HC-05 connection data stream:
```bash
arduino-app-cli app logs "." -f
```

### 3. Stop the App
Cleanly terminate background services and camera frame ingestion pipelines:
```bash
arduino-app-cli app stop "."
```

💡 **No Sketch Option (Python Only):** If you only want the camera's Python container running on the Linux processor without deploying custom C++ microcontroller code, delete the sketch directory entirely. The CLI will skip MCU compilation:
```bash
rm -rf <YOUR_PROJECT_PATH>/sketch
```

---

## 🔧 Hardware Troubleshooting: Dynamically Remapping Serial Ports

If you unplug your USB to TTL adapter or change ports, follow these structural alignment procedures to correct the device mapping:

### Step 1: Detect the New Kernel TTY Assignment
```bash
sudo dmesg -w
```
*Action:* Unplug your USB adapter, wait 2 seconds, and plug it back in. Observe the final terminal footprint line mapping (e.g., `cp210x converter now attached to ttyUSB1`). Press `Ctrl + C` to exit.

### Step 2: Synchronize Target Configuration Layouts (Example: Updating to `ttyUSB1`)

1. **Modify the Primary Python Script Engine:**
   ```bash
   nano <YOUR_PROJECT_PATH>/python/main.py
   ```
   * modification: Update line 15 to reflect the new assignment: `serial_port = '/dev/ttyUSB1'`
   * Save & Exit: `Ctrl + O` ➡️ `Enter` ➡️ `Ctrl + X`

2. **Modify the App Environment Blueprint:**
   ```bash
   nano <YOUR_PROJECT_PATH>/app.yaml
   ```
   * modification: Update the terminal device mapping field at the footer array:
     ```yaml
     devices: { dev: ["/dev/ttyUSB1"] }
     ```
   * Save & Exit: `Ctrl + O` ➡️ `Enter` ➡️ `Ctrl + X`

### Step 3: Clear Orchestrator Cache and Force Environment Rebuild
```bash
# Target project root
cd <YOUR_PROJECT_PATH>

# Purge cached hardware rules
rm -rf .cache

# Force start with updated container variables
arduino-app-cli app start "."
```

---

## 🔮 Future Development Path

* 🧪 **Hardware Miniaturization:** Migrating the breadboard layout onto a dedicated surface-mount custom PCB array.
* 📳 **Haptic Feedback Integration:** Embedding precise micro-vibration motor patterns in the chassis arms for tactile navigation.
* 🚨 **Cloud Safety Telemetry:** Developing crash-detection sensor thresholds linked to cellular IoT networks for automatic caregiver alerts.
