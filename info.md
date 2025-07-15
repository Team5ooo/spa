# MSpa Integration for Home Assistant

Control and monitor your MSpa (hot tub/spa) devices directly from Home Assistant.

## Features

- **Temperature Monitoring**: Track water temperature and target temperature
- **Device Control**: Control heater, filter, bubbles, ozone, UVC, and safety lock
- **Status Monitoring**: Binary sensors for all device states
- **Automatic Authentication**: Uses your MSpa account credentials - no manual token required

## Installation

This integration can be installed through HACS (Home Assistant Community Store).

### Requirements

- MSpa account credentials (username/password)
- Your MSpa device ID and product ID (found in the MSpa mobile app)

### Setup

1. Add this integration through HACS
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "MSpa" and select it
5. Enter your MSpa credentials and device information
6. Complete the setup

## Configuration

You'll need to provide:
- **Username**: Your MSpa account email
- **Password**: Your MSpa account password  
- **Device ID**: Found in your MSpa app settings
- **Product ID**: Found in your MSpa app settings

## Entities Created

The integration creates sensors and switches for:
- Water temperature monitoring
- Heater, filter, bubble, ozone, UVC, and safety lock control
- Status monitoring for all device functions

## Support

For issues, please check the [GitHub repository](https://github.com/Team5ooo/spa) and create an issue if needed.