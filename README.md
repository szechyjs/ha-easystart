# EasyStart BLE for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/v/release/szechyjs/ha-easystart)](https://github.com/szechyjs/ha-easystart/releases)

Native Bluetooth integration for [Micro-Air EasyStart](https://www.micro-air.com/products_groups_easystart_soft_starters_microair.cfm) soft starters. No ESP32 or additional hardware required — uses Home Assistant's built-in Bluetooth support to communicate directly with the device.

## Supported Devices

- EasyStart 364
- EasyStart 368

Any EasyStart device that advertises the BLE service UUID `d973f2e0-b19e-11e2-9e96-0800200c9a66` should work.

## Prerequisites

- Home Assistant 2024.1.0 or newer
- A Bluetooth adapter accessible to your HA instance (built-in on HA Yellow, HA Green, Raspberry Pi, or via USB dongle)
- Your EasyStart device must be powered on and within Bluetooth range

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three-dot menu → **Custom repositories**
3. Add `https://github.com/szechyjs/ha-easystart` with category **Integration**
4. Search for "EasyStart" and install
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/easystart` directory into your HA config's `custom_components/` folder
2. Restart Home Assistant

## Configuration

Once installed, Home Assistant will automatically discover nearby EasyStart devices via Bluetooth. A notification will appear in **Settings → Devices & Services** prompting you to add the device.

You can also add it manually:

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "EasyStart"
3. Follow the prompts

## Sensors

The integration exposes the following sensors:

| Sensor | Unit | Description |
|---|---|---|
| Live Current | A | Current draw of the compressor |
| Live Power | W | Calculated power (current × 240 V) |
| Line Frequency | Hz | AC line frequency |
| Last Start Peak | A | Peak current from the most recent start |
| Status | — | Device status (Normal, fault codes, etc.) |
| SCPT Delay | s | Short cycle protection timer delay |
| Total Faults | — | Cumulative fault count |
| Total Starts | — | Cumulative start count |

### Energy Dashboard

The integration automatically creates an **Energy** sensor (kWh) using a Riemann sum of the Live Power sensor. No manual helper setup required.

To add it to the Energy dashboard:

1. Go to **Settings → Dashboards → Energy**
2. Under **Individual devices**, click **Add device**
3. Under **Device energy consumption**, select **Energy** (Air Conditioner)
4. Optionally, under **Device power consumption**, select **Live Power** to show real-time wattage alongside cumulative usage
5. Optionally set a display name and upstream device
6. Click **Save**

> **Note:** A "Statistics not defined" warning may appear for up to 5 minutes after the sensor is first created. This is normal — it clears automatically once HA's statistics engine indexes the new entity.

## How It Works

The integration connects to the EasyStart device over BLE every 10 seconds. On each poll it:

1. Connects to the device
2. Subscribes to the notify characteristic (`d973f2e1-...`)
3. Writes `{"Cmd": ReadLive}` to the write characteristic (`d973f2e2-...`)
4. Waits for the device to push back an 18-byte data packet
5. Parses and publishes the sensor values
6. Disconnects

## Debugging

To enable debug logging, add this to your `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.easystart: debug
```

Logs are viewable under **Settings → System → Logs**.

## Credits

- [Derek Seaman](https://github.com/DerekSeaman) — reverse engineered the EasyStart BLE protocol and published the [ESPHome implementation](https://github.com/DerekSeaman/ESPHome-Micro-Air-EasyStart) that this integration is based on

## Contributing

Pull requests are welcome. Please open an issue first for significant changes.

## License

MIT
