## Overview

The ePaper Display Controller is a comprehensive solution for controlling a 1.54-inch e-paper display using an ESP32 microcontroller. This system allows users to send commands over Wi-Fi to the ESP32 to display text, images, and patterns on the e-paper screen. This README document provides detailed information on setting up the system, including hardware connections, software libraries, installation, and usage instructions.

## Table of Contents

- [1. Features](#1-features)
- [2. Hardware Requirements](#2-hardware-requirements)
- [3. Software Requirements](#3-software-requirements)
- [4. Installation](#4-installation)
- [5. Hardware Setup](#5-hardware-setup)
- [6. Software Configuration](#6-software-configuration)
- [7. API Endpoints](#7-api-endpoints)
- [8. Usage](#8-usage)
- [9. Sample Outputs](#9-sample-outputs)
- [10. Troubleshooting](#10-troubleshooting)
- [11. Contributing](#11-contributing)
- [12. License](#12-license)

## 1. Features

- **Text Display:** Display custom text messages on the e-paper screen.
- **Image Display:** Showcase images or patterns on the display.
- **Cross Pattern:** Generate a cross pattern for testing or display purposes.
- **File Management:** Upload images and list files stored on the ESP32 filesystem.

## 2. Hardware Requirements

- ESP32 microcontroller
- 1.54-inch e-paper display (SPI interface)
- Jumper wires for connections

## 3. Software Requirements

- Arduino IDE or compatible ESP32 programming environment
- Required libraries:
  - GxEPD2 for e-paper control
  - ESPAsyncWebServer for handling web requests
  - LittleFS for file system operations
  - Fonts library (FreeMonoBold9pt7b, FreeMonoBold18pt7b, etc.)
- Python environment with the following packages for the server-side image processing:
  - Flask
  - Pillow
  - numpy
  - requests

The required Python packages are listed in the provided `requirements.txt` file.

## 4. Installation

To set up the ePaper Display Controller, follow these steps:

1. **Arduino IDE Setup:**
   - Install the Arduino IDE from the official website.
   - Add the ESP32 board to your Arduino IDE.
   - Install the following libraries through the Library Manager: `GxEPD2`, `ESPAsyncWebServer`, and `LittleFS`.

2. **Python Environment Setup:**
   - Ensure that Python is installed on your server.
   - Use the `requirements.txt` file to install the necessary Python packages with the command:
     ```
     pip install -r requirements.txt
     ```

## 5. Hardware Setup

Connect the e-paper display to the ESP32 according to the pin definitions in the provided code:

- `EPD_CS`: Pin 5
- `EPD_DC`: Pin 17
- `EPD_RST`: Pin 16
- `EPD_BUSY`: Pin 4
- `EPD_MOSI`: Pin 23
- `EPD_CLK`: Pin 18

## 6. Software Configuration

Upload the `epaper_display_controller.ino` file to your ESP32 using the Arduino IDE. This script initializes the Wi-Fi connection and starts a web server with multiple endpoints to control the e-paper display.

## 7. API Endpoints

The system provides the following endpoints:

- `/clear`: Clears the e-paper display.
- `/displayText`: Displays the provided text on the e-paper.
- `/cross`: Displays a cross pattern on the e-paper.
- `/upload`: Handles file uploads to the ESP32 file system.
- `/list`: Lists the files stored on the ESP32.
