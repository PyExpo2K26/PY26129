#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// --- Configuration ---
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Flask Server API endpoint (Replace with your computer's IP address)
const char* serverUrl = "http://192.168.1.100:5000/api/update";

// Hardware Pins
const int moisturePin = 34;    // Analog pin for Capacitive Soil Moisture Sensor
const int flowSensorPin = 2;   // Digital pin for Water Flow Sensor
const int relayPin = 4;        // Digital pin for 4-Channel Relay Module (Pump)
const int lightPin = 5;        // Digital pin for Smart Light (LED or Relay)
const int gate1Pin = 13;       // LED representing Gate 1
const int gate2Pin = 12;       // LED representing Gate 2
// Note: Servo and extra DC motors can be connected to other free pins like 14, 27, etc.

// Thresholds & Calibration
// You need to calibrate these values based on your specific moisture sensor
const int airValue = 3500;   // Analog value when sensor is in dry air
const int waterValue = 1500; // Analog value when sensor is in water

// Variables
volatile int flowPulseCount = 0;
float flowRate = 0.0;
unsigned long oldTime = 0;
String currentPumpStatus = "OFF";

// Interrupt Service Routine for Flow Sensor
void IRAM_ATTR pulseCounter() {
  flowPulseCount++;
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Initialize Pins
  pinMode(relayPin, OUTPUT);
  digitalWrite(relayPin, HIGH); // Assuming active LOW relay (HIGH = OFF)
  
  pinMode(lightPin, OUTPUT);
  digitalWrite(lightPin, LOW);  // Turn off light by default

  pinMode(gate1Pin, OUTPUT);
  digitalWrite(gate1Pin, LOW);  // Turn off Gate 1 LED by default
  
  pinMode(gate2Pin, OUTPUT);
  digitalWrite(gate2Pin, LOW);  // Turn off Gate 2 LED by default
  
  pinMode(flowSensorPin, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(flowSensorPin), pulseCounter, FALLING);

  // Connect to WiFi
  connectToWiFi();
}

void loop() {
  // 1. Read Soil Moisture
  int rawMoisture = analogRead(moisturePin);
  
  // Convert to percentage (0-100%)
  // Map reverses the logic: higher analog value = lower moisture
  int moisturePercent = map(rawMoisture, airValue, waterValue, 0, 100);
  moisturePercent = constrain(moisturePercent, 0, 100);

  // 2. Read Water Flow (Calculate flow rate in Liters/minute)
  if ((millis() - oldTime) > 1000) { 
    // Disable interrupt while calculating
    detachInterrupt(digitalPinToInterrupt(flowSensorPin));
    
    // Standard calibration factor for YF-S201 is 4.5
    // Flow rate (L/min) = (Pulse count / 4.5)
    flowRate = ((1000.0 / (millis() - oldTime)) * flowPulseCount) / 4.5;
    
    // Reset variables
    oldTime = millis();
    flowPulseCount = 0;
    
    // Re-enable interrupt
    attachInterrupt(digitalPinToInterrupt(flowSensorPin), pulseCounter, FALLING);
  }

  Serial.printf("Moisture: %d%% | Flow: %.2f L/min\n", moisturePercent, flowRate);

  // 3. Send Data to Flask Backend and Receive Pump Command
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    // Create JSON payload matching the Flask backend's expected structure
    StaticJsonDocument<300> jsonDoc;
    
    // Moisture as a nested dict: {"field_1": value, ...}
    // Since ESP32 has 1 sensor, assign the same reading to all fields for now
    // In production, use multiple sensors on different pins
    JsonObject moisture = jsonDoc.createNestedObject("moisture");
    moisture["field_1"] = moisturePercent;
    moisture["field_2"] = moisturePercent;
    moisture["field_3"] = moisturePercent;
    moisture["field_4"] = moisturePercent;
    moisture["field_5"] = moisturePercent;
    moisture["field_6"] = moisturePercent;
    
    jsonDoc["water_flow"] = flowRate;
    
    String jsonPayload;
    serializeJson(jsonDoc, jsonPayload);
    
    // Send POST Request
    int httpResponseCode = http.POST(jsonPayload);
    
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Response: " + response);
      
      // Parse response to control pump, light, and gates
      StaticJsonDocument<512> responseDoc;
      DeserializationError error = deserializeJson(responseDoc, response);
      
      if (!error) {
        String newPumpStatus = responseDoc["pump_status"].as<String>();
        
        // Control Relay based on desired status
        if (newPumpStatus == "ON") {
          digitalWrite(relayPin, LOW); // Active LOW relay (LOW = ON)
          currentPumpStatus = "ON";
          Serial.println("Pump turned ON by server");
        } else {
          digitalWrite(relayPin, HIGH); // Active LOW relay (HIGH = OFF)
          currentPumpStatus = "OFF";
          Serial.println("Pump turned OFF by server");
        }

        // Control Smart Light based on status
        if (responseDoc.containsKey("light_status")) {
          String lightStatus = responseDoc["light_status"].as<String>();
          digitalWrite(lightPin, (lightStatus == "ON") ? HIGH : LOW);
          Serial.println("Light status updated to: " + lightStatus);
        }

        // Control Gates (represented by LEDs) based on status
        if (responseDoc.containsKey("gates")) {
          JsonObject gates = responseDoc["gates"];
          
          if (gates.containsKey("G1")) {
            String g1Status = gates["G1"].as<String>();
            digitalWrite(gate1Pin, (g1Status == "OPEN") ? HIGH : LOW);
            Serial.println("Gate 1 LED updated to: " + g1Status);
          }
          
          if (gates.containsKey("G2")) {
            String g2Status = gates["G2"].as<String>();
            digitalWrite(gate2Pin, (g2Status == "OPEN") ? HIGH : LOW);
            Serial.println("Gate 2 LED updated to: " + g2Status);
          }
          // Add more gates (G3-G8) here if more LEDs are connected
        }
      }
    } else {
      Serial.print("Error sending POST: ");
      Serial.println(httpResponseCode);
    }
    
    http.end();
  } else {
    Serial.println("WiFi Disconnected. Attempting to reconnect...");
    connectToWiFi();
  }

  // Delay before next reading (e.g., 2 seconds)
  delay(2000);
}

void connectToWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}