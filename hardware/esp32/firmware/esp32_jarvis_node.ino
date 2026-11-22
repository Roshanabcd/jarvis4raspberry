#include <WiFi.h>
#include <PubSubClient.h>

// ---------------------------------------------------------
// CONFIGURATION
// ---------------------------------------------------------
const char* ssid = "YOUR_WIFI_SSID";         // Replace with your Wi-Fi name
const char* password = "YOUR_WIFI_PASSWORD"; // Replace with your Wi-Fi password
const char* mqtt_server = "192.168.X.X";     // Replace with your Raspberry Pi's IP address

// Jarvis MQTT Topic
const char* device_id = "esp32_lights";
const char* command_topic = "jarvis/devices/esp32_lights/command";

// The onboard LED for ESP32 is usually GPIO 2
const int ledPin = 2;

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);

  // Command Logic matching Jarvis's iot_tool.py
  if (message == "turn_on") {
    digitalWrite(ledPin, HIGH); // Turn the LED on
    Serial.println("Action: Turned ON");
  } 
  else if (message == "turn_off") {
    digitalWrite(ledPin, LOW);  // Turn the LED off
    Serial.println("Action: Turned OFF");
  }
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "JarvisNode-";
    clientId += String(random(0, 1000));
    
    // Attempt to connect
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      // Subscribe to the Jarvis command topic
      client.subscribe(command_topic);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  pinMode(ledPin, OUTPUT);
  Serial.begin(115200);
  
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}
