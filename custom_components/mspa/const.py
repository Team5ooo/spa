"""Constants for the MSpa integration."""

DOMAIN = "mspa"
PLATFORMS = ["sensor","switch","climate","binary_sensor","button"]

API_BASE_URL = "https://api.iot.the-mspa.com/api"
#DEVICE_ID = "02d822c7f1c611ee9eabeb5156bace20"
#PRODUCT_ID = "O0N301"
DEVICE_STATUS_ENDPOINT = "device/thing_shadow"
DEFAULT_NAME = "MSpa"

HEADER = {
    "push_type": "Android",
    "authorization": "token API_KEY",
    "appid": "e1c8e068f9ca11eba4dc0242ac120002",
    "nonce": "iL5yjl01Ik4by7OgM7hUYD8v4rw1QS7t",
    "ts": "1718974474",
    "lan_code": "en",
    "sign": "C539A17F82552B986024327A47BB7C77"
}
#SENSOR_TYPES = {
#    "temperature": ["Current Temperature", TEMP_CELSIUS, EntityCategory.DIAGNOSTIC],
    # ... other sensor definitions
#}

STATES = {
    "ON": "1",
    "OFF": "0",
    # Add any other states if needed (e.g., "AUTO")
}