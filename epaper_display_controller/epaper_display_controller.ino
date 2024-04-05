#include <GxEPD2_BW.h>
#include <Fonts/FreeMonoBold9pt7b.h>
#include <Fonts/FreeMonoBold12pt7b.h> 
#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <esp_task_wdt.h>
#include "FS.h"
#include "LittleFS.h"

// Connections
#define EPD_CS 5
#define EPD_DC 17
#define EPD_RST 16
#define EPD_BUSY 4
#define EPD_MOSI 23
#define EPD_CLK 18

// GxEPD2 display class, set the correct width, height parameters for your display
GxEPD2_BW<GxEPD2_154_D67, GxEPD2_154_D67::HEIGHT> display(GxEPD2_154_D67(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY));

const char *ssid = "FRITZ!Box 6660 Cable IH";
const char *password = "39188923097050675231";

AsyncWebServer server(80);

void displayPicture() {
    const char *filename = "/IMG_0001.bin";
    const int imgWidth = 200;
    const int imgHeight = 200;

    File file = LittleFS.open(filename, "r");
    if (!file) {
        Serial.println("Failed to open file for reading");
        return;
    }
  
    size_t fileSize = file.size();
    uint8_t *buffer = new uint8_t[fileSize];

    if (!buffer) {
        Serial.println("Failed to allocate memory for image");
        file.close();
        return;
    }

    if (file.read(buffer, fileSize) != fileSize) {
        Serial.println("Failed to read the full image data");
        delete[] buffer;
        file.close();
        return;
    }
    file.close();

    display.init();
    display.setRotation(3);
    display.fillScreen(GxEPD_BLACK);
    display.drawBitmap(0, 0, buffer, imgWidth, imgHeight, GxEPD_WHITE);
    display.display();
    delete[] buffer;
}

void clearDisplay() {
    display.init();
    display.fillScreen(GxEPD_WHITE);
    display.display();
}

void displayText(const String &text) {
  display.init();
  display.setRotation(3);
  display.setTextColor(GxEPD_BLACK);
  display.fillScreen(GxEPD_WHITE);
  display.setFont(&FreeMonoBold12pt7b);  
  display.setCursor(3, 16); // Position of the text. 
  display.print(text); // Print the text
  display.display();
}

void displayCross() {
    display.init();
    display.setRotation(3);
    display.fillScreen(GxEPD_WHITE);

    int lineThickness = 10;
    int w = display.width();
    int h = display.height();

    for (int i = -lineThickness / 2; i < lineThickness / 2; i++) {
        display.drawLine(0 + i, 0, w + i, h, GxEPD_BLACK);
        display.drawLine(0, 0 + i, w, h + i, GxEPD_BLACK);
    }

    for (int i = -lineThickness / 2; i < lineThickness / 2; i++) {
        display.drawLine(w - i, 0, 0 - i, h, GxEPD_BLACK);
        display.drawLine(w, 0 + i, 0, h + i, GxEPD_BLACK);
    }

    display.display();
}

void setup() {
    Serial.begin(115200);
    esp_task_wdt_init(8, true);

    if (!LittleFS.begin()) {
        Serial.println("LittleFS Mount Failed, formatting...");
        LittleFS.format();
        if (!LittleFS.begin()) {
            Serial.println("Failed to format and mount LittleFS");
            return;
        }
    }

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    Serial.print("Connected, IP address: ");
    Serial.println(WiFi.localIP());

    server.on("/clear", HTTP_GET, [](AsyncWebServerRequest *request) {
        clearDisplay();
        request->send(200, "text/plain", "Screen cleared");
    });

    // Display text on the screen
    server.on("/displayText", HTTP_POST, [](AsyncWebServerRequest *request) {
        if (request->hasParam("plain", true)) {
            AsyncWebParameter *p = request->getParam("plain", true);
            displayText(p->value());
            request->send(200, "text/plain", "OK");
        } else {
            request->send(400, "text/plain", "Bad Request");
        }
    });

    // Display a black and white cross
    server.on("/cross", HTTP_GET, [](AsyncWebServerRequest *request) {
        displayCross();
        request->send(200, "text/plain", "Black and white cross displayed");
    });

    // File upload handling, which is triggered by a POST request via process_image endpoint in the image_processing_server.py
    server.on("/upload", HTTP_POST, [](AsyncWebServerRequest *request) {
        request->send(200, "text/plain", "File upload successful.");
    }, [](AsyncWebServerRequest *request, const String &filename, size_t index, uint8_t *data, size_t len, bool final) {
        static File uploadFile;
        if (!index) uploadFile = LittleFS.open("/" + filename, "w");
        if (uploadFile) {
            uploadFile.write(data, len);
            if (final) {
                uploadFile.close();
                displayPicture();
            }
        }
    });

    // List files in LittleFS
    server.on("/list", HTTP_GET, [](AsyncWebServerRequest *request) {
        String output = "Files:\n";
        File root = LittleFS.open("/");
        File file = root.openNextFile();
        while (file) {
            output += String(file.name()) + "\n";
            file = root.openNextFile();
        }
        request->send(200, "text/plain", output);
    });

    server.begin();
}

void loop() {
}
