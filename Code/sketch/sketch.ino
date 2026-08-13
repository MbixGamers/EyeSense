#include <Arduino_RouterBridge.h>

// Explicitly use Digital Pin macros for safe Zephyr hardware mapping
const int trigPin = D11;
const int echoPin = D12;

// Global variable shared with Python
volatile float currentDistance = 999.0;

// Expose this function to Python
float get_distance() {
    return currentDistance;
}

void setup() {
    // Initialize Communication Layer
    Bridge.begin();
    
    // Setup Sensor Pins
    pinMode(trigPin, OUTPUT);
    pinMode(echoPin, INPUT);
    pinMode(LED_BUILTIN, OUTPUT); 

    // Map the C++ function so Python can trigger it
    Bridge.provide("get_distance", get_distance);
}

void loop() {
    // 1. Clear the trigPin
    digitalWrite(trigPin, LOW);
    delayMicroseconds(5);
    
    // 2. Trigger the sensor with an exact 10 microsecond pulse
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);
    
    // 3. Zephyr RTOS compatible pulse timing logic
    unsigned long startTimeout = micros();
    bool timeoutError = false;

    // Wait for the echo pin to go HIGH with a safety timeout
    while (digitalRead(echoPin) == LOW) {
        if (micros() - startTimeout > 30000) { // 30ms timeout (~5 meters)
            timeoutError = true;
            break;
        }
    }
    
    if (!timeoutError) {
        // Record the precise start timestamp
        unsigned long startTime = micros();
        
        // Measure how long the echo pin stays HIGH
        while (digitalRead(echoPin) == HIGH) {
            if (micros() - startTime > 30000) { // Safety loop escape
                timeoutError = true;
                break;
            }
        }
        
        if (!timeoutError) {
            // Record the precise stop timestamp and calculate duration
            unsigned long stopTime = micros();
            long duration = stopTime - startTime;
            
            // 4. Calculate distance in centimeters
            if (duration > 0) {
                currentDistance = (float)duration * 0.0343 / 2.0;
            } else {
                currentDistance = 999.0;
            }
        }
    }

    // Force default reset value if a timeout threshold was triggered
    if (timeoutError) {
        currentDistance = 999.0;
    }
    
    // Local Hardware Alert: Light up LED if obstacle is <= 35cm (Updated from 20cm)
    if (currentDistance > 0.1 && currentDistance <= 35.0) {
        digitalWrite(LED_BUILTIN, HIGH);
    } else {
        digitalWrite(LED_BUILTIN, LOW);
    }
    
    delay(60); // Standard stabilization delay between pings
}
