#include <Arduino.h>

const int VOL_PIN   = A0;
const int BRI_PIN   = A2;
const int THRESHOLD = 8;    // threshold noise level (to prevent small changes being reported)
const int BAUD      = 9600;

int lastVolRaw = -999;
int lastBriRaw = -999;

void setup() {
  Serial.begin(BAUD);
  // Short startup delay so the host serial bridge is ready
  delay(1500);
  Serial.println("SYS_KNOBS_READY");
}

void loop() {
  int volRaw = 1023-analogRead(VOL_PIN);  // 0 – 1023 (I Inverted the wires so i need to invert the value)
  int briRaw = 1023-analogRead(BRI_PIN);  // 0 – 1023

  bool volChanged = abs(volRaw - lastVolRaw) > THRESHOLD;
  bool briChanged = abs(briRaw - lastBriRaw) > THRESHOLD;

  if (volChanged || briChanged) {
    // Map the analog value to the percentage output of each
    int volPct = map(volRaw, 0, 1023, 0, 100);
    int briPct = map(briRaw, 0, 1023, 0, 100);

    // Format: "V:XX B:XX"  
    Serial.print("V:");
    Serial.print(volPct);
    Serial.print(" B:");
    Serial.println(briPct);

    lastVolRaw = volRaw;
    lastBriRaw = briRaw;
  }

  delay(50);  // polls every 50ms
}
