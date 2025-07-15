# MSpa Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/Team5ooo/spa.svg)](https://github.com/Team5ooo/spa/releases)
[![License](https://img.shields.io/github/license/Team5ooo/spa.svg)](LICENSE)

A Home Assistant custom integration for MSpa (hot tub/spa) devices. Control and monitor your MSpa through Home Assistant using your MSpa account credentials.

## Features

- **🌡️ Temperature Control**: Full climate entity with temperature setting and HVAC control
- **🌡️ Temperature Monitoring**: Water temperature and target temperature sensors
- **🔛 Device Control**: Control heater, filter, bubbles, ozone, UVC, and safety lock
- **📊 Status Sensors**: Binary sensors for all device states
- **🫧 Bubble Level Control**: Adjustable bubble intensity (Low/Medium/High)
- **🌡️ Temperature Units**: Toggle between Celsius and Fahrenheit
- **🔄 Automatic Authentication**: Uses username/password - no manual token required
- **⚡ Instant Updates**: Immediate state refresh after commands (like mobile app)
- **🔐 Secure**: All communication encrypted with proper API authentication

## Supported Devices

This integration works with MSpa devices that use the MSpa mobile app for control.

## Installation

### HACS (Recommended)

1. **Add Custom Repository**:
   - Open HACS in Home Assistant
   - Click on "Integrations"
   - Click the 3-dot menu and select "Custom repositories"
   - Add this repository URL: `https://github.com/Team5ooo/spa`
   - Category: "Integration"
   - Click "Add"

2. **Install Integration**:
   - Find "MSpa" in the HACS integrations list
   - Click "Download"
   - Restart Home Assistant

### Manual Installation

1. **Download Files**:
   - Download the latest release from GitHub
   - Extract the files

2. **Copy to Home Assistant**:
   - Copy the `mspa` folder to your `config/custom_components/` directory
   - Restart Home Assistant

## Configuration

### Prerequisites

Before setting up the integration, you'll need:

1. **MSpa Account**: Username and password for your MSpa app
2. **Device Information**:
   - **Device ID**: Found in your MSpa app settings
   - **Product ID**: Also found in your MSpa app settings

### Setup Steps

1. **Add Integration**:
   - Go to Home Assistant Settings → Devices & Services
   - Click "Add Integration"
   - Search for "MSpa"
   - Click on the MSpa integration

2. **Enter Credentials**:
   - **Username**: Your MSpa account email
   - **Password**: Your MSpa account password
   - **Device ID**: Your MSpa device ID
   - **Product ID**: Your MSpa product ID

3. **Complete Setup**:
   - The integration will test the connection
   - If successful, your MSpa devices will be added to Home Assistant

## Entities

The integration creates the following entities:

### Climate
- `climate.mspa_temperature` - Temperature control with heating modes and target temperature

### Sensors
- `sensor.mspa_water_temperature` - Current water temperature
- `sensor.mspa_target_temperature` - Target temperature setting
- `sensor.mspa_bubble_level` - Bubble level (Off/Low/Medium/High)

### Switches
- `switch.mspa_heater` - Heater control
- `switch.mspa_filter` - Filter control
- `switch.mspa_bubbles_state` - Bubble on/off control
- `switch.mspa_ozone` - Ozone control
- `switch.mspa_uvc` - UVC control
- `switch.mspa_safety_lock` - Safety lock control
- `switch.mspa_temperature_unit_f` - Temperature unit toggle (°C/°F)

### Buttons
- `button.mspa_bubble_level` - Cycle bubble intensity levels (only when bubbles are on)

### Binary Sensors
- `binary_sensor.mspa_heater` - Heater status
- `binary_sensor.mspa_filter` - Filter status
- `binary_sensor.mspa_bubbles` - Bubble status
- `binary_sensor.mspa_ozone` - Ozone status
- `binary_sensor.mspa_uvc` - UVC status
- `binary_sensor.mspa_safety_lock` - Safety lock status

## Automation Examples

### Set temperature and turn on heater at sunset
```yaml
automation:
  - alias: "MSpa Evening Warmup"
    trigger:
      platform: sun
      event: sunset
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.mspa_temperature
        data:
          temperature: 38
      - service: climate.set_hvac_mode
        target:
          entity_id: climate.mspa_temperature
        data:
          hvac_mode: heat
```

### Bubble routine - start low and increase
```yaml
automation:
  - alias: "MSpa Bubble Sequence"
    trigger:
      platform: state
      entity_id: switch.mspa_bubbles_state
      to: "on"
    action:
      - delay: "00:05:00"  # 5 minutes at current level
      - service: button.press
        target:
          entity_id: button.mspa_bubble_level
      - delay: "00:05:00"  # 5 minutes at next level
      - service: button.press
        target:
          entity_id: button.mspa_bubble_level
```

### Notify when temperature reaches target
```yaml
automation:
  - alias: "MSpa Temperature Ready"
    trigger:
      platform: template
      value_template: "{{ states('sensor.mspa_water_temperature') | float >= states('sensor.mspa_target_temperature') | float }}"
    action:
      service: notify.notify
      data:
        message: "MSpa has reached target temperature!"
```

### Auto temperature unit based on weather
```yaml
automation:
  - alias: "MSpa Temperature Unit Auto"
    trigger:
      platform: homeassistant
      event: start
    action:
      - service: switch.turn_{{ 'on' if states('weather.home') | state_attr('temperature_unit') == '°F' else 'off' }}
        target:
          entity_id: switch.mspa_temperature_unit_f
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**:
   - Verify your username and password are correct
   - Check your device ID and product ID
   - Ensure your MSpa account is active

2. **Connection Issues**:
   - Check your internet connection
   - Verify Home Assistant can reach the MSpa API
   - Check Home Assistant logs for error details

3. **Device Not Responding**:
   - Ensure your MSpa device is connected to WiFi
   - Check if the device works in the MSpa mobile app
   - Restart the integration

### Debug Logging

To enable debug logging, add this to your `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.mspa: debug
```

## Development

### Architecture

The integration uses the following architecture:

- **API Client (`mspaapi.py`)**: Handles authentication and API communication
- **Configuration Flow (`config_flow.py`)**: User setup wizard
- **Platforms**: Sensor, switch, and binary sensor implementations
- **Coordinator**: Manages data updates and sharing between entities

### Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review Home Assistant logs
3. Search existing [GitHub issues](https://github.com/Team5ooo/spa/issues)
4. Create a new issue if needed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the Home Assistant community
- MSpa device owners who provided testing and feedback
- Contributors who helped with development and testing

## Disclaimer

This integration is not affiliated with or endorsed by MSpa. It is a community-developed integration for Home Assistant users.