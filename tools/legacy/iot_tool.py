import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt

# Configuration for local MQTT Broker (e.g., Mosquitto running on Pi)
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

def iot_action(device_id, action, payload=None):
    """
    Sends an MQTT message to an IoT device (like an ESP32).
    """
    topic = f"jarvis/devices/{device_id}/command"
    
    try:
        msg = f"{action}:{payload}" if payload else action
        print(f"Sending IoT Command to {device_id}: {msg}")
        publish.single(topic, msg, hostname=MQTT_BROKER, port=MQTT_PORT)
        return f"Command '{action}' sent successfully to device {device_id}."
    except Exception as e:
        return f"Failed to send IoT command: {e}. Is the MQTT broker running?"

iot_tool_schema = {
    "type": "function",
    "function": {
        "name": "iot_action",
        "description": "Call this tool to interact with local IoT devices like the ESP32 developer kit, speed measure device, or atmosphere monitor.",
        "parameters": {
            "type": "object",
            "properties": {
                "device_id": {
                    "type": "string",
                    "description": "The ID of the device (e.g., 'esp32_lights', 'atmosphere_sensor')."
                },
                "action": {
                    "type": "string",
                    "description": "The action to perform (e.g., 'turn_on', 'read_temp')."
                },
                "payload": {
                    "type": "string",
                    "description": "Optional payload for the action."
                }
            },
            "required": ["device_id", "action"]
        }
    }
}
