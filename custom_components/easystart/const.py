"""Constants for the EasyStart integration."""

DOMAIN = "easystart"

# BLE service and characteristic UUIDs
SERVICE_UUID = "d973f2e0-b19e-11e2-9e96-0800200c9a66"
NOTIFY_CHARACTERISTIC_UUID = "d973f2e1-b19e-11e2-9e96-0800200c9a66"
WRITE_CHARACTERISTIC_UUID = "d973f2e2-b19e-11e2-9e96-0800200c9a66"

# {"Cmd": ReadLive} — triggers the device to push a live data notification
READ_LIVE_COMMAND = bytes(
    [
        0x7B,
        0x22,
        0x43,
        0x6D,
        0x64,
        0x22,
        0x3A,
        0x20,
        0x52,
        0x65,
        0x61,
        0x64,
        0x4C,
        0x69,
        0x76,
        0x65,
        0x7D,
    ]
)

# How often to poll the device (seconds)
SCAN_INTERVAL = 10

# Assumed line voltage for power calculation (EasyStart is used on A/C units)
VOLTAGE = 240.0

# Minimum expected packet length from the notify characteristic
MIN_PACKET_LENGTH = 18

# Timeout (seconds) waiting for a BLE notification after sending the read command
NOTIFY_TIMEOUT = 5.0

# Status strings indexed by byte[2] of the notify packet
STATUS_STRINGS = [
    "Normal",
    "Unexpected Curr Flt",
    "Short Cycle Delay",
    "Pwr Intrrptn Fault",
    "Stall Fault",
    "Stuck SR Fault",
    "Open Ovrld Fault",
    "Overcurrent Fault",
    "Bad Wiring Fault",
    "Wrong Voltage Flt",
]
