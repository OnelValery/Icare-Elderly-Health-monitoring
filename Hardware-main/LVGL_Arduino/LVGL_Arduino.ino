/*******************************************************
 *  Includes & Configuration
 *******************************************************/
#include <WiFi.h>
#include <esp_http_server.h>
#include <lvgl.h>
#include <TFT_eSPI.h>
#include "lv_conf.h"
#include "CST816S.h"
#include <Wire.h>
#include <math.h>
#include "QMI8658.h"
#include "MAX30105.h"
#include "heartRate.h"
#include "spo2_algorithm.h"
#include "SPIFFS.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"   
#include "esp_timer.h"
#include "index_html.h"
#include <time.h>    
#include "watchface.h"
#include "esp_heap_caps.h"
#include "secrets.h"

// For HTTP requests
#include <HTTPClient.h>

// Include ArduinoJson for geolocation
#include <ArduinoJson.h>

#ifndef LV_RADIUS_CIRCLE
  #define LV_RADIUS_CIRCLE 0x7fff
#endif

// ============================================================
//   Define a structure to hold geolocation data
// ============================================================
struct GeoLocation {
  float lat;
  float lon;
};

static const char* FLASK_POSTDATA_URL = "http://192.168.43.76:5001/postdata";
static const char* FLASK_FALL_URL     = "http://192.168.43.76:5001/fall";

// ============================================================
//                Wi-Fi Credentials
// ============================================================
const char* ssid = "Phone-S";                       // Edit with actual ssid
const char* password = "hotspot-password-project";  // Edit with actual password

// ============ Time Configuration for NTP ============
#define GMT_OFFSET_SEC      -18000  // -5 hours
#define DAYLIGHT_OFFSET_SEC 3600    // +1 hour
const char* ntpServer = "time.nrc.ca";

// ============================================================
//                Serial (CH343P) Config
// ============================================================
#define TX_PIN 43  // UART TX (GPIO43)
#define RX_PIN 44  // UART RX (GPIO44)
HardwareSerial MySerial(0); // Use Serial0 for CH343P USB-to-UART

// ============================================================
//  Web Server Declaration (ESP-IDF HTTP server)
// ============================================================
httpd_handle_t server = NULL;

// ============================================================
//                Constants & Configuration
// ============================================================
constexpr int SCREEN_WIDTH  = 240;
constexpr int SCREEN_HEIGHT = 240;
constexpr int LVGL_TICK_MS  = 2;
constexpr int NUM_SAMPLES   = 50;
constexpr double frate      = 0.95;
constexpr double FSpO2      = 0.2;
constexpr long MIN_IR_THRESHOLD = 20000;  // Lowered for better detection

// Fall detection threshold
constexpr float FALL_ACCEL_THRESHOLD = 25.0f; // m/s^2

// ============================================================
//  Global Variables for SPO2 & Heart Rate Calculation
// ============================================================
double avered = 0.0, aveir = 0.0;
double sumredrms = 0.0, sumirrms = 0.0;
int spO2_sample_count = 0;
double ESpO2 = 0.0;
long lastBeat = 0;
float beatAvg = 0.0;
unsigned long beatCounter = 0;

constexpr int PPG_BUF_SIZE = 1800;  // around 4.5s of data at 400 Hz
float ppgBuffer[PPG_BUF_SIZE];
unsigned long ppgTimestamps[PPG_BUF_SIZE];
int ppgIndex = 0;

int peakIndices[50];  // Store up to 50 peak locations
int peakCount = 0;

// ============================================================
//  Global Variables for Other Sensors/Features
// ============================================================
static int stepCount = 0;
static int displayedStepCount = 0;
static unsigned long lastStepTime = 0;
static float latestTemp = 0.0f;

// Simple “cooldown” to avoid spamming fall alerts
static bool fallRecentlyDetected = false;
static unsigned long lastFallTime = 0;
constexpr unsigned long FALL_COOLDOWN_MS = 3000; // 3 seconds
static bool fallAlertCanceledByUser = false;

TaskHandle_t vitalsPostTaskHandle = NULL;

// ============================================================
//  LVGL Objects & Display Buffers
// ============================================================
static lv_obj_t *battery_label   = nullptr;
static lv_obj_t *vital_label     = nullptr;
static lv_obj_t *debug_label     = nullptr;
static lv_obj_t *carousel        = nullptr;
static lv_obj_t *motion_gyro_label  = nullptr;
static lv_obj_t *motion_accel_label = nullptr;
static lv_obj_t *fall_alert_screen = nullptr;

// We'll display the watchface + clock on the clock page
static lv_obj_t *clock_canvas;
static lv_color_t* clock_canvas_buf;

TFT_eSPI tft(SCREEN_WIDTH, SCREEN_HEIGHT);
CST816S touch(6, 7, 13, 5);
static lv_disp_draw_buf_t draw_buf;
static lv_color_t buf[SCREEN_WIDTH * SCREEN_HEIGHT / 10];

// ============================================================
//             Sensor Objects
// ============================================================
TwoWire maxWire(1);
MAX30105 particleSensor;

// ==================== Heartbeat Waveform ====================
#define HEART_CANVAS_HEIGHT 100

static lv_obj_t* heartbeat_canvas = nullptr;
static lv_color_t* heartbeat_canvas_buf;

constexpr int HEART_BUF_SIZE = SCREEN_WIDTH;
int heartBuf[HEART_BUF_SIZE] = {0};  // stores scaled IR readings
int smoothedBuf[HEART_BUF_SIZE] = {0};
int heartIndex = 0;

// ============================================================
//  Global Variables for Dynamic IR Plotting
// ============================================================
static int irBuf[HEART_BUF_SIZE] = {0};  // Buffer to store raw IR values
static int irIndex = 0;                  // Current index for IR buffer

// Use a sliding window size for local scaling
constexpr int WINDOW_SIZE = 100;

// ============================================================
//  FreeRTOS LVGL Mutex
// ============================================================
SemaphoreHandle_t lvgl_mutex;

// ============================================================
//  Forward Declarations for LVGL Timer Tasks
// ============================================================
static void battery_update_task(lv_timer_t *timer);
static void gyro_update_task(lv_timer_t *timer);
static void accel_update_task(lv_timer_t *timer);

// Clock forward declarations
void update_clock();
void clockTask(void *pvParameters);

/*******************************************************
 *             DISPLAY & TOUCH FUNCTIONS
 *******************************************************/
void my_disp_flush(lv_disp_drv_t *disp_drv, const lv_area_t *area, lv_color_t *color_p) {
  uint32_t w = area->x2 - area->x1 + 1;
  uint32_t h = area->y2 - area->y1 + 1;
  tft.startWrite();
  tft.setAddrWindow(area->x1, area->y1, w, h);
  // If LV_COLOR_16_SWAP == 0 in lv_conf.h, set 'false' for last param
  tft.pushColors((uint16_t *)&color_p->full, w * h, true);
  tft.endWrite();
  lv_disp_flush_ready(disp_drv);
}

void my_touchpad_read(lv_indev_drv_t *indev_drv, lv_indev_data_t *data) {
  if (!touch.available()) {
    data->state = LV_INDEV_STATE_REL;
  } else {
    data->state   = LV_INDEV_STATE_PR;
    data->point.x = touch.data.x;
    data->point.y = touch.data.y;
  }
}

/*******************************************************
 *               LVGL TICK HANDLER
 *******************************************************/
void lv_tick_task(void *arg) {
  lv_tick_inc(LVGL_TICK_MS);
}

/*******************************************************
 *  GEOLCATION FUNCTIONS FOR TRIANGULATION
 *******************************************************/
GeoLocation getLocation() {
  GeoLocation loc = {0.0, 0.0};
  int n = WiFi.scanNetworks();
  if (n == 0) {
    MySerial.println("No WiFi networks found for triangulation.");
  } else {
    DynamicJsonDocument doc(2048);
    doc["considerIp"] = true;
    JsonArray wifiArray = doc.createNestedArray("wifiAccessPoints");
    for (int i = 0; i < n; i++) {
      JsonObject ap = wifiArray.createNestedObject();
      ap["macAddress"] = WiFi.BSSIDstr(i);
      ap["signalStrength"] = WiFi.RSSI(i);
    }
    String jsonPayload;
    serializeJson(doc, jsonPayload);
    MySerial.println("Sending WiFi scan results for triangulation:");
    MySerial.println(jsonPayload);
    HTTPClient http;
    String googleUrl = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + String(GOOGLE_API_KEY);
    http.begin(googleUrl);
    http.addHeader("Content-Type", "application/json");
    int httpResponseCode = http.POST(jsonPayload);
    MySerial.print("HTTP Response Code: ");
    MySerial.println(httpResponseCode);
    if (httpResponseCode == 200) {
      String response = http.getString();
      MySerial.println("Response from geolocation service:");
      MySerial.println(response);
      DynamicJsonDocument respDoc(1024);
      DeserializationError error = deserializeJson(respDoc, response);
      if (!error) {
        loc.lat = respDoc["location"]["lat"].as<float>();
        loc.lon = respDoc["location"]["lng"].as<float>();
        MySerial.printf("Triangulated Location: %.5f, %.5f\n", loc.lat, loc.lon);
      } else {
        MySerial.print("Failed to parse geolocation response: ");
        MySerial.println(error.c_str());
      }
    } else {
      MySerial.println("Failed to get location from Google API");
    }
    http.end();
  }
  return loc;
}

/*******************************************************
 *  FALL ALERT: POST to Our Local or External API
 *******************************************************/
void sendFallAlert() {
  MySerial.println("Sending fall alert...");
  GeoLocation loc = getLocation();
  String url = FLASK_FALL_URL;
  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  // Compose JSON with required fields
  String jsonPayload = "{";
  jsonPayload += "\"client_id\":\"ESP32_001\","; 
  jsonPayload += "\"fallDetected\":true,";
  jsonPayload += "\"time\":";
  jsonPayload += millis();
  jsonPayload += ",\"lat\":";
  jsonPayload += loc.lat;
  jsonPayload += ",\"lon\":";
  jsonPayload += loc.lon;
  jsonPayload += "}";

  int httpCode = http.POST(jsonPayload);
  if (httpCode > 0) {
    MySerial.print("Fall alert POST response code: ");
    MySerial.println(httpCode);
    String resp = http.getString();
    MySerial.print("Response: ");
    MySerial.println(resp);
  } else {
    MySerial.print("[Flask POST] failed, error code: ");
    MySerial.println(httpCode);
  }
  http.end();
}

static lv_timer_t* fallCountdownTimer = nullptr;
static int countdownSeconds = 5;
static lv_obj_t* countdownLabel = nullptr;
static bool fallAlertSent = false;

void showFallOverlay(float lat, float lon) {
  if (fall_alert_screen) return;
  countdownSeconds = 5;
  fallAlertSent = false;
  fall_alert_screen = lv_obj_create(lv_scr_act());
  lv_obj_set_size(fall_alert_screen, SCREEN_WIDTH, SCREEN_HEIGHT);
  lv_obj_set_style_bg_color(fall_alert_screen, lv_color_black(), 0);
  lv_obj_set_style_bg_opa(fall_alert_screen, LV_OPA_COVER, 0);
  lv_obj_clear_flag(fall_alert_screen, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_set_style_radius(fall_alert_screen, LV_RADIUS_CIRCLE, 0);
  // Title
  lv_obj_t* title = lv_label_create(fall_alert_screen);
  lv_label_set_text(title, "Fall Detected!");
  lv_obj_set_style_text_color(title, lv_color_hex(0xFF4C4C), 0);
  lv_obj_set_style_text_font(title, &lv_font_montserrat_22, 0);
  lv_obj_align(title, LV_ALIGN_TOP_MID, 0, 30);
  // Countdown Label
  countdownLabel = lv_label_create(fall_alert_screen);
  lv_label_set_text_fmt(countdownLabel, "Sending help in %d...", countdownSeconds);
  lv_obj_set_style_text_color(countdownLabel, lv_color_white(), 0);
  lv_obj_set_style_text_font(countdownLabel, &lv_font_montserrat_20, 0);
  lv_obj_align(countdownLabel, LV_ALIGN_CENTER, 0, -10);
  // Cancel Button
  lv_obj_t* btn = lv_btn_create(fall_alert_screen);
  lv_obj_set_style_bg_color(btn, lv_color_hex(0xE74C3C), 0);
  lv_obj_set_size(btn, 140, 50);
  lv_obj_align(btn, LV_ALIGN_BOTTOM_MID, 0, -20);
  lv_obj_t* label = lv_label_create(btn);
  lv_label_set_text(label, "Cancel");
  lv_obj_center(label);
  lv_obj_add_event_cb(btn, [](lv_event_t* e) {
    if (fall_alert_screen) {
      if (fallCountdownTimer) lv_timer_del(fallCountdownTimer);
      lv_obj_del(fall_alert_screen);
      fall_alert_screen = nullptr;
      fallAlertCanceledByUser = true;
      fallRecentlyDetected = false;
      MySerial.println("User canceled fall alert.");
    }
  }, LV_EVENT_CLICKED, NULL);
  // Start the 1-second countdown timer
  fallCountdownTimer = lv_timer_create([](lv_timer_t* t) {
    countdownSeconds--;
    lv_label_set_text_fmt(countdownLabel, "Sending help in %d...", countdownSeconds);
    if (countdownSeconds <= 0) {
      lv_timer_del(fallCountdownTimer);
      fallCountdownTimer = nullptr;
      if (!fallAlertCanceledByUser && !fallAlertSent) {
        xTaskCreatePinnedToCore(fallReportingTask, "FallReportTask", 8192, NULL, 1, NULL, 1);
        fallAlertSent = true;
        lv_label_set_text(countdownLabel, "Help is on the way!");
        lv_obj_t* btn = lv_obj_get_child(fall_alert_screen, NULL);
        if (btn) {
          lv_obj_t* lbl = lv_obj_get_child(btn, NULL);
          if (lbl) lv_label_set_text(lbl, "Cancel Help");
        }
      }
    }
  }, 1000, NULL);
}

/*******************************************************
 *     FreeRTOS Task: Vitals POST Updates
 *******************************************************/
 void vitalsPostTask(void *pvParameters) {
  for (;;) {
    // Wait for the task to be notified (blocking wait)
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

    sendVitalsToServer();
  }
}

/*******************************************************
 *     FreeRTOS Task: Sensor & UI Updates
 *******************************************************/
static int lastSentHeartIndex = 0;
void sendVitalsToServer() {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  http.begin(FLASK_POSTDATA_URL);
  http.addHeader("Content-Type", "application/json");
  String payload = "{";
  payload += "\"client_id\":\"ESP32_001\",";
  payload += "\"hr\":" + String((int)beatAvg) + ",";
  payload += "\"spo2\":" + String((int)ESpO2) + ",";
  payload += "\"temperature\":" + String(latestTemp) + ",";
  payload += "\"stepCount\":" + String(stepCount);
  payload += ",\"fall\":" + String(fallRecentlyDetected ? "true" : "false");
  const int MAX_SEND = 400;
  payload += ",\"waveform\":[";
  int count = 0;
  while (count < MAX_SEND && lastSentHeartIndex != irIndex) {
      int mappedValue = robustMapIRToY(irBuf[lastSentHeartIndex]);
      payload += String(mappedValue);
      lastSentHeartIndex = (lastSentHeartIndex + 1) % HEART_BUF_SIZE;
      if (++count < MAX_SEND && lastSentHeartIndex != irIndex) {
          payload += ",";
      }
  }
  payload += "]";
  payload += ",\"peaks\":[";
  for (int i = 0; i < peakCount; i++) {
      payload += String(peakIndices[i]);
      if (i != peakCount - 1) payload += ",";
  }
  payload += "]";
  payload += "}";
  int code = http.POST(payload);
  if (code > 0) {
    MySerial.printf("[Vitals POST] Code: %d, Response: %s\n", code, http.getString().c_str());
  } else {
    MySerial.printf("[Vitals POST] Failed, Error: %s\n", http.errorToString(code).c_str());
  }
  http.end();
}

/*******************************************************
 *      Battery & Motion Timer Tasks
 *******************************************************/
static void battery_update_task(lv_timer_t *timer) {
  char buf_str[64];
  int adc_val = analogRead(GPIO_NUM_1);
  float voltage = (3.3f / (1 << 12)) * 3.0f * adc_val;
  float percentage = ((voltage - 3.3f) / (4.2f - 3.3f)) * 100.0f;
  if (percentage > 100.0f) percentage = 100.0f;
  if (percentage < 0.0f) percentage = 0.0f;
  sprintf(buf_str, "Battery:\n%.2f V\n%.0f%%", voltage, percentage);
  lv_label_set_text(battery_label, buf_str);
}

static void gyro_update_task(lv_timer_t *timer) {
  char buf_str[96];
  float gyro[3] = {0.0f, 0.0f, 0.0f};
  QMI8658_read_gyro_xyz(gyro);
  sprintf(buf_str, "Gyroscope:\nX:%.2f dps\nY:%.2f dps\nZ:%.2f dps",
          gyro[0], gyro[1], gyro[2]);
  lv_label_set_text(motion_gyro_label, buf_str);
}

/**
 * Accelerometer logic: steps + fall detection
 */
static void accel_update_task(lv_timer_t *timer) {
  char buf_str[96];
  float acc[3] = {0.0f, 0.0f, 0.0f};
  QMI8658_read_acc_xyz(acc);
  float mag = sqrt(acc[0]*acc[0] + acc[1]*acc[1] + acc[2]*acc[2]);
  unsigned long now = millis();
  if (mag > 12.0f && (now - lastStepTime) > 300) {
    stepCount++;
    lastStepTime = now;
  }
  if (mag > FALL_ACCEL_THRESHOLD) {
    if (!fallRecentlyDetected) {
      MySerial.println("Fall detected! Acceleration spike!");
      showFallOverlay(0.0, 0.0);
      xTaskCreatePinnedToCore(fallReportingTask, "FallReportTask", 8192, NULL, 1, NULL, 1);
      fallRecentlyDetected = true;
      lastFallTime = now;
    }
  }
  if (fallAlertCanceledByUser) {
    fallRecentlyDetected = false;
    fallAlertCanceledByUser = false;
  }
  sprintf(buf_str, "Steps: %d", stepCount);
  displayedStepCount = stepCount;
  lv_label_set_text(motion_accel_label, buf_str);
  MySerial.print("Accel: ");
  MySerial.print(acc[0]); MySerial.print(", ");
  MySerial.print(acc[1]); MySerial.print(", ");
  MySerial.println(acc[2]);
  MySerial.print("Magnitude: ");
  MySerial.println(mag);
}

/*******************************************************
 *  Sensor Data Processing Functions
 *******************************************************/
void updateSpO2() {
  long irValue = particleSensor.getIR();
  long redValue = particleSensor.getRed();
  if (irValue < MIN_IR_THRESHOLD) {
    MySerial.println("No finger detected.");
    beatAvg = 0.0;
    ESpO2 = 0.0;
    lv_label_set_text(vital_label, "Pulse: -- bpm\nSpO2: -- %");
    return;
  }
  spO2_sample_count++;
  double fred = (double)redValue;
  double fir = (double)irValue;
  avered = avered * frate + fred * (1.0 - frate);
  aveir  = aveir  * frate + fir  * (1.0 - frate);
  sumredrms += (fred - avered) * (fred - avered);
  sumirrms  += (fir  - aveir ) * (fir  - aveir );
  if (spO2_sample_count >= NUM_SAMPLES) {
    double R = (sqrt(sumredrms) / avered) / (sqrt(sumirrms) / aveir);
    double rawSpO2 = -23.3 * (R - 0.4) + 100;
    ESpO2 = FSpO2 * ESpO2 + (1.0 - FSpO2) * rawSpO2;
    spO2_sample_count = 0;
    sumredrms = 0.0;
    sumirrms  = 0.0;
    lv_label_set_text_fmt(vital_label, "Pulse: %d bpm\nSpO2: %d%%", (int)beatAvg, (int)ESpO2);
  }
}

/*******************************************************
 *  Helper Functions for Dynamic IR Plotting (Pure IR)
 *******************************************************/

int robustMapIRToY(int sample) {
  int startIndex = (irIndex - WINDOW_SIZE + HEART_BUF_SIZE) % HEART_BUF_SIZE;
  float sum = 0;
  for (int i = 0; i < WINDOW_SIZE; i++) {
    int idx = (startIndex + i) % HEART_BUF_SIZE;
    sum += irBuf[idx];
  }
  float mean = sum / WINDOW_SIZE;
  
  float sumSq = 0;
  for (int i = 0; i < WINDOW_SIZE; i++) {
    int idx = (startIndex + i) % HEART_BUF_SIZE;
    float diff = irBuf[idx] - mean;
    sumSq += diff * diff;
  }
  float stdDev = sqrt(sumSq / WINDOW_SIZE);
  
  float lowerBound = mean - 2 * stdDev;
  float upperBound = mean + 2 * stdDev;
  
  // Clamp the sample to the robust range.
  if (sample < lowerBound) sample = lowerBound;
  if (sample > upperBound) sample = upperBound;
  
  int mapped = (int)((sample - lowerBound) * (HEART_CANVAS_HEIGHT - 1) / (upperBound - lowerBound));
  mapped = (HEART_CANVAS_HEIGHT - 1) - mapped;
  return mapped;
}

void draw_dynamic_ir_waveform() {
  lv_canvas_fill_bg(heartbeat_canvas, lv_color_hex(0xF3FCFC), LV_OPA_COVER);
  lv_draw_line_dsc_t line_dsc;
  lv_draw_line_dsc_init(&line_dsc);
  line_dsc.color = lv_color_hex(0x2596BE);
  line_dsc.width = 2;
  for (int i = 1; i < HEART_BUF_SIZE; i++) {
    int index1 = (irIndex + i - 1) % HEART_BUF_SIZE;
    int index2 = (irIndex + i) % HEART_BUF_SIZE;
    int y1 = robustMapIRToY(irBuf[index1]);
    int y2 = robustMapIRToY(irBuf[index2]);
    lv_point_t line_points[2] = {
      { i - 1, y1 },
      { i,     y2 }
    };
    lv_canvas_draw_line(heartbeat_canvas, line_points, 2, &line_dsc);
  }
}

/*******************************************************
 *  Modified updateHeartRate Function (Pure IR Graph)
 *******************************************************/
void updateHeartRate() {
  long currentSample = particleSensor.getIR();
  static float filteredIR = 0;
  const float irSmoothingAlpha = 0.1;  // lower = more smoothing, higher = less smoothing

  if (currentSample < MIN_IR_THRESHOLD) {
    int centerY = HEART_CANVAS_HEIGHT / 2;
    irBuf[irIndex] = centerY;
    irIndex = (irIndex + 1) % HEART_BUF_SIZE;
    draw_dynamic_ir_waveform();
    return;
  }
  
  // Heart rate detection logic
  static long sampleBuffer[3] = {0, 0, 0};
  sampleBuffer[0] = sampleBuffer[1];
  sampleBuffer[1] = sampleBuffer[2];
  sampleBuffer[2] = currentSample;
  static float movingAvg = 0;
  static bool initialized = false;
  const float smoothing = 0.01;
  if (!initialized) {
    movingAvg = currentSample;
    initialized = true;
  } else {
    movingAvg = (1.0 - smoothing) * movingAvg + smoothing * currentSample;
  }
  const float margin = 500.0;
  float dynamicThreshold = movingAvg + margin;
  bool isPeak = (sampleBuffer[1] > sampleBuffer[0]) &&
                (sampleBuffer[1] > sampleBuffer[2]) &&
                (sampleBuffer[1] > dynamicThreshold);
  unsigned long now = millis();
  const unsigned long minBeatInterval = 300;
  if (isPeak && (now - lastBeat > minBeatInterval)) {
    float currentBPM = 60.0f * 1000.0f / (now - lastBeat);
    lastBeat = now;
    if (currentBPM > 20 && currentBPM < 255) {
      if (beatAvg == 0.0)
        beatAvg = currentBPM;
      else
        beatAvg = (beatAvg * 0.9f) + (currentBPM * 0.1f);
      beatCounter++;
      MySerial.print("Beat detected! BPM = ");
      MySerial.println(currentBPM);
    }
  }
  
  // Update the filtered IR value (exponential moving average)
  filteredIR = (1 - irSmoothingAlpha) * filteredIR + irSmoothingAlpha * currentSample;

  // Use filteredIR for further processing and plotting
  irBuf[irIndex] = (int)filteredIR;
  irIndex = (irIndex + 1) % HEART_BUF_SIZE;
  draw_dynamic_ir_waveform();

  // // Store raw IR value and redraw the pure IR waveform.
  // irBuf[irIndex] = (int)currentSample;
  // irIndex = (irIndex + 1) % HEART_BUF_SIZE;
  // draw_dynamic_ir_waveform();
  
  MySerial.print("IR: ");
  MySerial.print(currentSample);
  MySerial.print(" | MovingAvg: ");
  MySerial.print(movingAvg);
  MySerial.print(" | Threshold: ");
  MySerial.print(dynamicThreshold);
  MySerial.print(" | Buffer: [");
  MySerial.print(sampleBuffer[0]); MySerial.print(", ");
  MySerial.print(sampleBuffer[1]); MySerial.print(", ");
  MySerial.print(sampleBuffer[2]); MySerial.println("]");
}

void updateUI() {
  if (beatAvg == 0.0) {
    lv_label_set_text(vital_label, "Pulse: -- bpm\nSpO2: -- %");
  } else {
    char vitalBuf[128];
    sprintf(vitalBuf, "Pulse: %d bpm\nSpO2: %d%%", (int)beatAvg, (int)ESpO2);
    lv_label_set_text(vital_label, vitalBuf);
  }
}

void updateDebugPage() {
  if (!debug_label) return;
  long irValue = particleSensor.getIR();
  long redValue = particleSensor.getRed();
  char dbgBuf[160];
  sprintf(dbgBuf, "Debug Info\nIR: %ld\nRED: %ld\nBPM(avg): %d\nBeats: %lu",
          irValue, redValue, (int)beatAvg, beatCounter);
  lv_label_set_text(debug_label, dbgBuf);
}

void draw_heartbeat_waveform() {
  lv_canvas_fill_bg(heartbeat_canvas, lv_color_hex(0xF3FCFC), LV_OPA_COVER);
  lv_draw_line_dsc_t line_dsc;
  lv_draw_line_dsc_init(&line_dsc);
  line_dsc.color = lv_color_hex(0x2596BE);
  line_dsc.width = 2;
  const int SPREAD = 1;
  for (int x = 1; x < HEART_BUF_SIZE; x++) {
    int y1 = heartBuf[(heartIndex + x - 1) % HEART_BUF_SIZE];
    int y2 = heartBuf[(heartIndex + x) % HEART_BUF_SIZE];
    lv_point_t line_points[2] = {
      {(x - 1) * SPREAD, y1},
      {x * SPREAD, y2}
    };
    lv_canvas_draw_line(heartbeat_canvas, line_points, 2, &line_dsc);
  }
}

void injectFakeQRS() {
  const int qrsShape[] = { 0, -5, -20, 0, 25, -10, 0 };
  int centerY = HEART_CANVAS_HEIGHT / 2;
  const int shapeLen = sizeof(qrsShape) / sizeof(qrsShape[0]);
  for (int i = 0; i < shapeLen; i++) {
    int y = constrain(centerY - qrsShape[i], 0, HEART_CANVAS_HEIGHT - 1);
    heartBuf[heartIndex] = y;
    heartIndex = (heartIndex + 1) % HEART_BUF_SIZE;
  }
}

/*******************************************************
 *     FreeRTOS Task: Fall Reporting
 *******************************************************/
void fallReportingTask(void *pvParameters) {
  GeoLocation loc = getLocation();
  sendFallAlert(); // Uses loc internally, or could tweak it to accept loc as arg
  vTaskDelete(NULL); 
}

/*******************************************************
 *     FreeRTOS Task: Sensor & UI Updates
 *******************************************************/
unsigned long lastPost = 0;
void sensorTask(void *pvParameters) {
  for (;;) {
    if (xSemaphoreTake(lvgl_mutex, portMAX_DELAY) == pdTRUE) {
      updateSpO2();
      updateHeartRate();
      updateUI();
      updateDebugPage();
      lv_timer_handler();
      xSemaphoreGive(lvgl_mutex);
    }
    unsigned long now = millis();
    if (now - lastPost > 5000) {  // Every 5 seconds
      if (vitalsPostTaskHandle != NULL) {
        xTaskNotifyGive(vitalsPostTaskHandle);  // Trigger background POST
      }
      lastPost = now;
    }
    vTaskDelay(pdMS_TO_TICKS(20));
  }
}

/*******************************************************
 *     FreeRTOS Task: Analog Clock Updates
 *   (Updates the clock canvas every 50ms)
 *******************************************************/
void clockTask(void *pvParameters) {
  while (1) {
    if (xSemaphoreTake(lvgl_mutex, portMAX_DELAY) == pdTRUE) {
      update_clock();
      xSemaphoreGive(lvgl_mutex);
    }
    vTaskDelay(pdMS_TO_TICKS(50));
  }
}

/*******************************************************
 *               Analog Clock Drawing Function
 *******************************************************/
static time_t baseTime = 0;
static unsigned long baseMillis = 0;
static bool firstRun = true;
void drawDatePills(lv_obj_t* canvas, struct tm* timeinfo) {
  int center = SCREEN_WIDTH / 2;
  char day_text[4];    
  char date_text[10]; 
  strftime(day_text, sizeof(day_text), "%a", timeinfo);
  strftime(date_text, sizeof(date_text), "%b %d", timeinfo);
  lv_draw_rect_dsc_t pill_dsc;
  lv_draw_rect_dsc_init(&pill_dsc);
  pill_dsc.bg_color = lv_color_hex(0x7ACBEA);
  pill_dsc.bg_opa = LV_OPA_COVER;
  pill_dsc.radius = 20;
  lv_draw_label_dsc_t label_dsc;
  lv_draw_label_dsc_init(&label_dsc);
  label_dsc.color = lv_color_hex(0xFFFFFF);
  label_dsc.align = LV_TEXT_ALIGN_CENTER;
  int top_pill_w = 70;
  int top_pill_h = 28;
  int top_x = center - top_pill_w / 2;
  int top_y = center - 40;
  lv_canvas_draw_rect(canvas, top_x, top_y, top_pill_w, top_pill_h, &pill_dsc);
  int top_text_y = top_y + (top_pill_h - 16) / 2;
  lv_canvas_draw_text(canvas, top_x, top_text_y, top_pill_w, &label_dsc, day_text);
  int bot_pill_w = 90;
  int bot_pill_h = 28;
  int bot_x = center - bot_pill_w / 2;
  int bot_y = center + 20;
  lv_canvas_draw_rect(canvas, bot_x, bot_y, bot_pill_w, bot_pill_h, &pill_dsc);
  int bot_text_y = bot_y + (bot_pill_h - 16) / 2;
  lv_canvas_draw_text(canvas, bot_x, bot_text_y, bot_pill_w, &label_dsc, date_text);
}

void update_clock() {
  time_t now;
  time(&now);
  if (firstRun || now != baseTime) {
    baseTime = now;
    baseMillis = millis();
    firstRun = false;
  }
  float elapsed = (millis() - baseMillis) / 1000.0f;
  struct tm *local = localtime(&baseTime);
  float secDisplay = local->tm_sec + elapsed;
  if (secDisplay >= 60.0f) secDisplay -= 60.0f;
  float minuteContinuous = local->tm_min + secDisplay / 60.0f;
  float hourContinuous = (local->tm_hour % 12) + minuteContinuous / 60.0f;
  float sec_angle  = secDisplay * 6.0f;
  float min_angle  = minuteContinuous * 6.0f;
  float hour_angle = hourContinuous * 30.0f;
  float sec_rad  = sec_angle  * (M_PI / 180.0f);
  float min_rad  = min_angle  * (M_PI / 180.0f);
  float hour_rad = hour_angle * (M_PI / 180.0f);
  int center = SCREEN_WIDTH / 2;
  int radius = center - 8;
  lv_draw_img_dsc_t img_dsc;
  lv_draw_img_dsc_init(&img_dsc);
  img_dsc.blend_mode = LV_BLEND_MODE_NORMAL;
  lv_canvas_draw_img(clock_canvas, 0, 0, &watchface, &img_dsc);
  drawDatePills(clock_canvas, local);
  for (int i = 0; i < 12; i++) {
    float angle = i * 30 * (M_PI / 180.0f);
    int x = center + (int)((radius - 10) * sin(angle));
    int y = center - (int)((radius - 10) * cos(angle));
    if (i % 3 == 0) {
      const char* label;
      switch (i) {
        case 0: label = "12"; break;
        case 3: label = "3"; break;
        case 6: label = "6"; break;
        case 9: label = "9"; break;
        default: label = ""; break;
      }
      lv_draw_label_dsc_t tick_label_dsc;
      lv_draw_label_dsc_init(&tick_label_dsc);
      tick_label_dsc.color = lv_color_hex(0x1E8FA6);
      tick_label_dsc.align = LV_TEXT_ALIGN_CENTER;
      lv_canvas_draw_text(clock_canvas, x - 6, y - 8, 20, &tick_label_dsc, label);
    } else {
      lv_draw_rect_dsc_t dot_dsc;
      lv_draw_rect_dsc_init(&dot_dsc);
      dot_dsc.radius = LV_RADIUS_CIRCLE;
      dot_dsc.bg_color = lv_color_hex(0x44E3FC);
      dot_dsc.bg_opa = LV_OPA_COVER;
      lv_canvas_draw_rect(clock_canvas, x - 2, y - 2, 4, 4, &dot_dsc);
    }
  }
  int hour_length = (int)(radius * 0.5);
  int hour_x = center + (int)(hour_length * sin(hour_rad));
  int hour_y = center - (int)(hour_length * cos(hour_rad));
  lv_point_t hour_line[2] = { {center, center}, {hour_x, hour_y} };
  lv_draw_line_dsc_t hour_line_dsc;
  lv_draw_line_dsc_init(&hour_line_dsc);
  hour_line_dsc.color = lv_color_hex(0x2596BE);
  hour_line_dsc.width = 4;
  lv_canvas_draw_line(clock_canvas, hour_line, 2, &hour_line_dsc);
  int min_length = (int)(radius * 0.7);
  int min_x = center + (int)(min_length * sin(min_rad));
  int min_y = center - (int)(min_length * cos(min_rad));
  lv_point_t min_line[2] = { {center, center}, {min_x, min_y} };
  lv_draw_line_dsc_t min_line_dsc;
  lv_draw_line_dsc_init(&min_line_dsc);
  min_line_dsc.color = lv_color_hex(0x809CA2);
  min_line_dsc.width = 3;
  lv_canvas_draw_line(clock_canvas, min_line, 2, &min_line_dsc);
  int sec_length = (int)(radius * 0.9);
  int sec_x = center + (int)(sec_length * sin(sec_rad));
  int sec_y = center - (int)(sec_length * cos(sec_rad));
  lv_point_t sec_line[2] = { {center, center}, {sec_x, sec_y} };
  lv_draw_line_dsc_t sec_line_dsc;
  lv_draw_line_dsc_init(&sec_line_dsc);
  sec_line_dsc.color = lv_color_hex(0x448A96);
  sec_line_dsc.width = 2;
  lv_canvas_draw_line(clock_canvas, sec_line, 2, &sec_line_dsc);
}

/*******************************************************
 *  Web Server URI Handlers (ESP-IDF HTTP Server)
 *******************************************************/
esp_err_t root_get_handler(httpd_req_t *req) {
  httpd_resp_set_type(req, "text/html");
  httpd_resp_send(req, index_html, HTTPD_RESP_USE_STRLEN);
  return ESP_OK;
}

esp_err_t data_get_handler(httpd_req_t *req) {
  char json[2048];  // increased buffer size
  int waveformSampleCount = 100;
  String waveformStr = "[";
  int idx = (irIndex - waveformSampleCount + HEART_BUF_SIZE) % HEART_BUF_SIZE;
  for (int i = 0; i < waveformSampleCount; i++) {
    // waveformStr += String(irBuf[idx]);  // use IR buffer instead of heartBuf
    int mappedValue = robustMapIRToY(irBuf[idx]);
    waveformStr += String(mappedValue);
    if (i != waveformSampleCount - 1) waveformStr += ",";
    idx = (idx + 1) % HEART_BUF_SIZE;
  }
  waveformStr += "]";

  sprintf(json,
    "{\"bpm\":%d,\"spo2\":%d,\"temperature\":%.2f,\"stepCount\":%d, ... }",
    (int)beatAvg, (int)ESpO2, latestTemp, displayedStepCount,
    fallRecentlyDetected ? "true" : "false", waveformStr.c_str()
  );
  httpd_resp_set_type(req, "application/json");
  httpd_resp_send(req, json, HTTPD_RESP_USE_STRLEN);
  return ESP_OK;
}

esp_err_t post_data_handler(httpd_req_t *req) {
  char buf[256];
  int ret = httpd_req_recv(req, buf, sizeof(buf) - 1);
  if (ret <= 0) {
    httpd_resp_send_408(req);
    return ESP_FAIL;
  }
  buf[ret] = '\0';
  MySerial.print("Received POST data: ");
  MySerial.println(buf);
  const char* resp = "Data received";
  httpd_resp_send(req, resp, HTTPD_RESP_USE_STRLEN);
  return ESP_OK;
}

esp_err_t fall_post_handler(httpd_req_t *req) {
  char buf[256];
  int ret = httpd_req_recv(req, buf, sizeof(buf) - 1);
  if (ret <= 0) {
    httpd_resp_send_408(req);
    return ESP_FAIL;
  }
  buf[ret] = '\0';
  MySerial.print("Received FALL POST data: ");
  MySerial.println(buf);
  const char* resp = "Fall alert received";
  httpd_resp_send(req, resp, HTTPD_RESP_USE_STRLEN);
  return ESP_OK;
}

httpd_uri_t uri_root = {
  .uri      = "/",
  .method   = HTTP_GET,
  .handler  = root_get_handler,
  .user_ctx = NULL
};

httpd_uri_t uri_data = {
  .uri      = "/data",
  .method   = HTTP_GET,
  .handler  = data_get_handler,
  .user_ctx = NULL
};

httpd_uri_t uri_postdata = {
  .uri      = "/postdata",
  .method   = HTTP_POST,
  .handler  = post_data_handler,
  .user_ctx = NULL
};

httpd_uri_t uri_fall = {
  .uri      = "/fall",
  .method   = HTTP_POST,
  .handler  = fall_post_handler,
  .user_ctx = NULL
};

httpd_handle_t start_webserver() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  httpd_handle_t server = NULL;
  if (httpd_start(&server, &config) == ESP_OK) {
    httpd_register_uri_handler(server, &uri_root);
    httpd_register_uri_handler(server, &uri_data);
    httpd_register_uri_handler(server, &uri_postdata);
    httpd_register_uri_handler(server, &uri_fall);
  }
  return server;
}

void getDailyStepsFromServer() {
  HTTPClient http;
  String url = "http://192.168.43.76:5001/steps/ESP32_001";  
  http.begin(url);
  int httpCode = http.GET();

  if (httpCode > 0) {
    String payload = http.getString();
    DynamicJsonDocument doc(256);
    DeserializationError err = deserializeJson(doc, payload);
    if (!err) {
      stepCount = doc["stepCount"].as<int>();
      MySerial.printf("[INIT] Step count received from server: %d\n", stepCount);
    } else {
      MySerial.println("[ERROR] Failed to parse stepCount JSON");
    }
  } else {
    MySerial.printf("[ERROR] Failed GET /steps (code %d)\n", httpCode);
  }

  http.end();
}

/*******************************************************
 *                     SETUP
 *******************************************************/
void setup() {
  MySerial.begin(115200, SERIAL_8N1, RX_PIN, TX_PIN);
  delay(1000);
  MySerial.println("\nESP32-S3 Setup Started...");
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  MySerial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    MySerial.print(".");
  }
  MySerial.println("\nWiFi connected!");
  getDailyStepsFromServer();
  MySerial.print("IP Address: ");
  MySerial.println(WiFi.localIP());
  MySerial.print("Gateway IP: ");
  MySerial.println(WiFi.gatewayIP());
  MySerial.print("DNS IP: ");
  MySerial.println(WiFi.dnsIP());
  
  MySerial.print("Resolving ");
  MySerial.print(ntpServer);
  MySerial.println("...");
  IPAddress ntpIP;
  if (WiFi.hostByName(ntpServer, ntpIP)) {
    MySerial.print("NTP server IP: ");
    MySerial.println(ntpIP);
  } else {
    MySerial.println("Failed to resolve NTP server! Possibly a DNS issue.");
  }
  
  MySerial.println("Configuring time via NTP...");
  configTime(GMT_OFFSET_SEC, DAYLIGHT_OFFSET_SEC, "pool.ntp.org", "time.nist.gov", "time.google.com");
  unsigned long startAttempt = millis();
  const unsigned long TIMEOUT_MS = 30000;
  struct tm timeinfo;
  while (!getLocalTime(&timeinfo)) {
    if (millis() - startAttempt >= TIMEOUT_MS) {
      MySerial.println("Time sync failed, continuing anyway...");
      break;
    }
    MySerial.println("Waiting for time sync...");
    delay(1000);
  }
  if (getLocalTime(&timeinfo)) {
    MySerial.print("Current time: ");
    MySerial.println(&timeinfo, "%A, %B %d %Y %H:%M:%S");
  }
  
  server = start_webserver();
  if (server != NULL) {
    MySerial.println("HTTP server started");
  } else {
    MySerial.println("Failed to start HTTP server");
  }
  
  lv_init();
  tft.begin();
  tft.setRotation(0);
  touch.begin();
  lv_disp_draw_buf_init(&draw_buf, buf, nullptr, SCREEN_WIDTH * SCREEN_HEIGHT / 10);
  static lv_disp_drv_t disp_drv;
  lv_disp_drv_init(&disp_drv);
  disp_drv.hor_res = SCREEN_WIDTH;
  disp_drv.ver_res = SCREEN_HEIGHT;
  disp_drv.flush_cb = my_disp_flush;
  disp_drv.draw_buf = &draw_buf;
  lv_disp_drv_register(&disp_drv);
  static lv_indev_drv_t indev_drv;
  lv_indev_drv_init(&indev_drv);
  indev_drv.type = LV_INDEV_TYPE_POINTER;
  indev_drv.read_cb = my_touchpad_read;
  lv_indev_drv_register(&indev_drv);
  
  const esp_timer_create_args_t lvgl_tick_timer_args = {
    .callback = lv_tick_task,
    .arg = NULL,
    .name = "lvgl_tick"
  };
  esp_timer_handle_t lvgl_tick_timer = NULL;
  esp_timer_create(&lvgl_tick_timer_args, &lvgl_tick_timer);
  esp_timer_start_periodic(lvgl_tick_timer, LVGL_TICK_MS * 1000);
  
  carousel = lv_obj_create(lv_scr_act());
  lv_obj_set_size(carousel, SCREEN_WIDTH, SCREEN_HEIGHT);
  lv_obj_set_pos(carousel, 0, 0);
  lv_obj_set_style_pad_all(carousel, 0, LV_PART_MAIN);
  lv_obj_set_style_clip_corner(carousel, true, LV_PART_MAIN);
  lv_obj_set_style_radius(carousel, LV_RADIUS_CIRCLE, LV_PART_MAIN);
  lv_obj_set_style_border_width(carousel, 0, LV_PART_MAIN);
  lv_obj_set_scrollbar_mode(carousel, LV_SCROLLBAR_MODE_OFF);
  lv_obj_set_scroll_dir(carousel, LV_DIR_HOR);
  lv_obj_set_scroll_snap_x(carousel, true);
  
  // Page 0: Battery
  lv_obj_t *page0 = lv_obj_create(carousel);
  lv_obj_set_size(page0, SCREEN_WIDTH, SCREEN_HEIGHT);
  lv_obj_set_pos(page0, 0, 0);
  lv_obj_set_style_pad_all(page0, 0, LV_PART_MAIN);
  lv_obj_set_style_clip_corner(page0, true, LV_PART_MAIN);
  lv_obj_set_style_radius(page0, LV_RADIUS_CIRCLE, LV_PART_MAIN);
  lv_obj_set_style_bg_opa(page0, LV_OPA_COVER, LV_PART_MAIN);
  lv_obj_set_style_bg_color(page0, lv_color_hex(0xF3FCFC), LV_PART_MAIN);
  battery_label = lv_label_create(page0);
  lv_label_set_text(battery_label, "Battery:\n0.00 V\n0%");
  lv_obj_set_style_text_font(battery_label, &lv_font_montserrat_16, 0);
  lv_obj_align(battery_label, LV_ALIGN_CENTER, 0, 0);
  lv_timer_create(battery_update_task, 500, nullptr);
  
  // Page 1: Clock (Watchface)
  lv_obj_t *page1 = lv_obj_create(carousel);
  lv_obj_set_size(page1, SCREEN_WIDTH, SCREEN_HEIGHT);
  lv_obj_set_pos(page1, SCREEN_WIDTH, 0);
  lv_obj_set_style_pad_all(page1, 0, LV_PART_MAIN);
  lv_obj_set_style_clip_corner(page1, true, LV_PART_MAIN);
  lv_obj_set_style_radius(page1, LV_RADIUS_CIRCLE, LV_PART_MAIN);
  lv_obj_set_style_bg_opa(page1, LV_OPA_COVER, LV_PART_MAIN);
  lv_obj_set_style_bg_color(page1, lv_color_white(), LV_PART_MAIN);
  lv_obj_clear_flag(page1, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_set_scrollbar_mode(page1, LV_SCROLLBAR_MODE_OFF);
  clock_canvas = lv_canvas_create(page1);
  clock_canvas_buf = (lv_color_t*) heap_caps_malloc(SCREEN_WIDTH * SCREEN_HEIGHT * sizeof(lv_color_t), MALLOC_CAP_SPIRAM);
  heartbeat_canvas_buf = (lv_color_t*) heap_caps_malloc(LV_IMG_BUF_SIZE_TRUE_COLOR(SCREEN_WIDTH, HEART_CANVAS_HEIGHT), MALLOC_CAP_SPIRAM);
  if (!clock_canvas_buf || !heartbeat_canvas_buf) {
    MySerial.println("ERROR: Failed to allocate PSRAM canvas buffers!");
    while (1);
  }
  lv_canvas_set_buffer(clock_canvas, clock_canvas_buf, SCREEN_WIDTH, SCREEN_HEIGHT, LV_IMG_CF_TRUE_COLOR);
  lv_obj_align(clock_canvas, LV_ALIGN_CENTER, 0, 0);
  lv_obj_clear_flag(clock_canvas, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_set_scrollbar_mode(clock_canvas, LV_SCROLLBAR_MODE_OFF);
  
  // Page 2: Steps only
  lv_obj_t *page2 = lv_obj_create(carousel);
  lv_obj_set_size(page2, SCREEN_WIDTH, SCREEN_HEIGHT);
  lv_obj_set_pos(page2, SCREEN_WIDTH * 2, 0);
  lv_obj_set_style_pad_all(page2, 0, LV_PART_MAIN);
  lv_obj_set_style_clip_corner(page2, true, LV_PART_MAIN);
  lv_obj_set_style_radius(page2, LV_RADIUS_CIRCLE, LV_PART_MAIN);
  lv_obj_set_style_bg_opa(page2, LV_OPA_COVER, LV_PART_MAIN);
  lv_obj_set_style_bg_color(page2, lv_color_hex(0xA4F4FC), LV_PART_MAIN);
  lv_obj_clear_flag(page2, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_set_scrollbar_mode(page2, LV_SCROLLBAR_MODE_OFF);
  motion_accel_label = lv_label_create(page2);
  lv_label_set_text_fmt(motion_accel_label, "Steps: %d", stepCount);
  lv_obj_set_style_text_font(motion_accel_label, &lv_font_montserrat_22, 0);
  lv_obj_align(motion_accel_label, LV_ALIGN_CENTER, 0, 0);
  lv_timer_create(accel_update_task, 100, nullptr);
  
  // Page 3: Debug - COMMENTED OUT 
  /*
  lv_obj_t *page3 = lv_obj_create(carousel);
  lv_obj_set_size(page3, SCREEN_WIDTH, SCREEN_HEIGHT);
  lv_obj_set_pos(page3, SCREEN_WIDTH * 3, 0);
  lv_obj_set_style_pad_all(page3, 0, LV_PART_MAIN);
  lv_obj_set_style_clip_corner(page3, true, LV_PART_MAIN);
  lv_obj_set_style_radius(page3, LV_RADIUS_CIRCLE, LV_PART_MAIN);
  lv_obj_set_style_bg_opa(page3, LV_OPA_COVER, LV_PART_MAIN);
  lv_obj_set_style_bg_color(page3, lv_color_hex(0xFFFFFF), LV_PART_MAIN);
  debug_label = lv_label_create(page3);
  lv_label_set_text(debug_label, "Debug:\nIR: --\nRED: --\nBPM: --");
  lv_obj_align(debug_label, LV_ALIGN_CENTER, 0, 0);
  */
  
  // Page 4: Vital Signs (HR + SpO₂ waveform)
  lv_obj_t *page4 = lv_obj_create(carousel);
  lv_obj_set_size(page4, SCREEN_WIDTH, SCREEN_HEIGHT);
  lv_obj_set_pos(page4, SCREEN_WIDTH * 4, 0);
  lv_obj_set_style_pad_all(page4, 0, LV_PART_MAIN);
  lv_obj_set_style_clip_corner(page4, true, LV_PART_MAIN);
  lv_obj_set_style_radius(page4, LV_RADIUS_CIRCLE, LV_PART_MAIN);
  lv_obj_set_style_bg_opa(page4, LV_OPA_COVER, LV_PART_MAIN);
  lv_obj_set_style_bg_color(page4, lv_color_hex(0xB4F6FC), LV_PART_MAIN);
  lv_obj_clear_flag(page4, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_set_scrollbar_mode(page4, LV_SCROLLBAR_MODE_OFF);
  heartbeat_canvas = lv_canvas_create(page4);
  lv_canvas_set_buffer(heartbeat_canvas, heartbeat_canvas_buf, SCREEN_WIDTH, HEART_CANVAS_HEIGHT, LV_IMG_CF_TRUE_COLOR);
  lv_obj_align(heartbeat_canvas, LV_ALIGN_TOP_MID, 0, 20);
  lv_canvas_fill_bg(heartbeat_canvas, lv_color_hex(0xF3FCFC), LV_OPA_COVER);
  vital_label = lv_label_create(page4);
  lv_label_set_text(vital_label, "Pulse: -- bpm\nSpO2: -- %");
  lv_obj_set_style_text_font(vital_label, &lv_font_montserrat_20, 0);
  lv_obj_align(vital_label, LV_ALIGN_BOTTOM_MID, 0, -20);
  
  lv_obj_update_layout(carousel);
  lv_obj_scroll_to_x(carousel, SCREEN_WIDTH, LV_ANIM_OFF);
  
  Wire.begin(6, 7);
  if (QMI8658_init())
    MySerial.println("QMI8658 initialized successfully.");
  else
    MySerial.println("QMI8658 initialization failed!");
  
  maxWire.begin(21, 33);
  if (!particleSensor.begin(maxWire, I2C_SPEED_FAST)) {
    MySerial.println("ERROR: MAX30105 not detected. Check wiring/power!");
    while (1);
  } else {
    MySerial.println("MAX30105 initialized.");
  }
  particleSensor.setup(
    0x1F,   // LED brightness
    4,      // Sample average
    2,      // LED mode (Red + IR)
    100,    // Sample rate in Hz
    69,     // Pulse width
    16384   // ADC range
  );
  particleSensor.setPulseAmplitudeIR(0x7F);
  particleSensor.setPulseAmplitudeRed(0x7F);
  particleSensor.setPulseAmplitudeGreen(0);
  MySerial.println("ESP32-S3 Setup Completed.");
  
  lvgl_mutex = xSemaphoreCreateMutex();
  if (lvgl_mutex == NULL) {
    MySerial.println("Failed to create LVGL mutex!");
  }
  
  xTaskCreatePinnedToCore(sensorTask, "SensorTask", 8192, NULL, 1, NULL, 1);
  xTaskCreatePinnedToCore(clockTask,  "ClockTask", 4096, NULL, 1, NULL, 1);
  xTaskCreatePinnedToCore(vitalsPostTask, "VitalsPostTask", 8192, NULL, 1, &vitalsPostTaskHandle, 1);
}

void loop() {
  vTaskDelay(portMAX_DELAY);
}