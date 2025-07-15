# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Home Assistant custom integration** for MSpa (hot tub/spa) devices. The integration communicates with MSpa devices through their cloud API to monitor sensors and control switches.

## Architecture

The integration follows Home Assistant's standard structure:

- **Main Integration (`__init__.py`)**: Handles setup/teardown, platform loading (sensor, switch)
- **Configuration Flow (`config_flow.py`)**: User setup wizard for MSpa account credentials (username, password, device_id, product_id)
- **API Client (`mspaapi.py`)**: Async HTTP client for MSpa cloud API communication
- **Platforms**: 
  - `sensor.py`: Temperature sensors and bubble level display
  - `switch.py`: Control switches (heater, filter, bubbles, ozone, UVC, safety lock)
  - `binary_sensor.py`: Status sensors (same functions as switches but read-only)

## Key Components

### API Communication
- Base URL: `https://api.iot.the-mspa.com/api`
- **Authentication**: Username/password-based login flow that automatically obtains access tokens
- **Request Signing**: Dynamic nonce, timestamp, and MD5 signature generation for each request
- Device commands sent to `device/command` endpoint
- Device status fetched from `device/thing_shadow` endpoint
- **Token Management**: Automatic token refresh on expiration with credential fallback

### Data Flow
- **MSPADataUpdateCoordinator**: Manages polling (15-minute intervals) and data sharing between entities
- **Dependency Logic**: Heater/UVC require filter to be on; turning off filter disables heater/ozone/UVC
- **State Management**: Local state updates after successful API commands to improve responsiveness

### Entity Structure
- Temperature sensors use raw API values (already in correct Celsius) with automatic unit conversion
- Bubble level mapped from numeric (0-3) to descriptive states (Off/Low/Medium/High)
- Switch entities include automatic dependency handling

## Development Notes

- Uses `aiohttp` for async HTTP requests (declared in manifest.json)
- Implements proper Home Assistant coordinator pattern for data updates
- Error handling via custom `MSPAAPIException`
- Logging throughout with appropriate levels (debug for API responses, error for failures)

### Authentication System
- **Dynamic Authentication**: Users provide username/password instead of manual API tokens
- **Request Signing**: Each request includes dynamically generated nonce, timestamp, and MD5 signature using the app secret
- **Signature Algorithm**: `MD5(appId + ',' + appSecret + ',' + nonce + ',' + timestamp).toUpperCase()`
- **App Secret**: Extracted from Android APK: `87025c9ecd18906d27225fe79cb68349`
- **Auto-retry Logic**: Failed authentication attempts trigger automatic token refresh
- **Login Endpoint**: `/enduser/get_token/` (discovered via MITM analysis)
- **Backwards Compatibility**: Still supports manual API key if provided

## Testing

The integration includes a connection test in the config flow (`test_connection()` method) that validates API credentials during setup.