#include "esphome.h"
using namespace esphome;

#define PIN_1 18
#define PIN_2 19
#define PIN_3 21


class MyCustomFanoutput : public Component, public FloatOutput {
 public:
  void setup() override {
    // This will be called by App.setup()
    pinMode(PIN_1, OUTPUT);
    pinMode(PIN_2, OUTPUT);
    pinMode(PIN_3, OUTPUT);
  }

  void write_state(float state) override {
     if (state == 0.33) {
       digitalWrite(PIN_1, HIGH);
       delay(25);
       digitalWrite(PIN_1, LOW);
     }
     else if (state == 0.66) { 
       digitalWrite(PIN_2, HIGH);
       delay(25);
       digitalWrite(PIN_2, LOW);
     }
     else if (state == 1) {
        digitalWrite(PIN_3, HIGH);
        delay(25);
        digitalWrite(PIN_3, LOW);
     }
  }
};
