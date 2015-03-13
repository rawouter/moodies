/*
 * Moodies "That was cloudy!" button POC code
 *
 * Wiring:
 *    - push button down pin D3, interrupt 1
 *    - push button up pin A1 or 15
 *    - piezo pin A0 or 14
 *    - Ethernet shield is attached to pins 10, 11, 12, 13
 *    PWM are: 3, 5, 6, 9, 10, and 11. Provide 8-bit PWM output with the analogWrite() function.
 *    - so RGB is at: 5,6,9 (100 ohm to each colors)
 *    - Led matrix: 16,17,18 (DIN, CLK, CS) or A2, A3, A4
 *    LEFT: 1,2,4,7,8 and a few analog
 *
 * Author: RaphYot
 * Created on: 2015 Feb 10th
 */
 
#include <SPI.h>
#include <UIPEthernet.h>
#include <PusherClient.h>

//////
// Ethernet vars
//////
#define DEVICE_ID 1

byte mac[] = {0x52, 0x61, 0x70, 0x68, 0x07, 1+DEVICE_ID};
PusherClient client;
//////
// Button vars
//////
#define BUTTON_D 3
#define BUTTON_U 15
#define BUTTON_INTER 1
#define DEBOUNCE_UP 150 // This can be 50 on some hardware, or 150 on other (so far) test by doing one long push. Less is best.
static unsigned long push_time = 0;
static int push_counter = 1;
static bool push_counting = false;
static bool push_sent = true;

////////
// RGB
////////

#define RPIN 5
#define GPIN 6
#define BPIN 9

///////
// Piezo vars
///////
int speakerOut = 14;
char melody[32];
uint8_t melody_ptr = 0;  // Points to the melody
bool play_melody = true;

void setup() {
  
  Serial.begin(9600);
  // RGB
  pinMode(RPIN, OUTPUT);
  pinMode(GPIN, OUTPUT);
  pinMode(BPIN, OUTPUT);
  set_color("0,50,255");
  // Ethernet
  if (Ethernet.begin(mac) == 0) {
    Serial.println("Init Ethernet failed");
    for(;;)
      ;
  }
  Serial.println(Ethernet.localIP());

  if(client.connect("your-api-key-here")) {
    client.bind("hello", helloWorld);
  }
  else {
    while(1) {Serial.println("No connection to pushingobx");}
  }
  
  // Button
  pinMode(BUTTON_U, INPUT);
  pinMode(BUTTON_D, INPUT);
  attachInterrupt(BUTTON_INTER, pushed, HIGH);
  
}

void loop() {
  if (client.connected()) {
    client.monitor();
  }
  else {
    Serial.println("Not connected");
  }
}

void helloWorld(String data) {
  Serial.println("Got an hello!");
}

/**********************************
 * Hardware interface functions
 **********************************/


///////////////////////////////
// Piezo
///////////////////////////////


/*
 * Play a melody, input is a string of notes
 * Notes defined in names and tones
 *
 * The calculation of the tones is made following the mathematical
 * operation:
 *
 *       timeHigh = 1/(2 * toneFrequency) = period / 2
 *
 * where the different tones are described as in the table:
 *
 * note         frequency       period  PW (timeHigh)   
 * c            261 Hz          3830    1915    
 * d            294 Hz          3400    1700    
 * e            329 Hz          3038    1519    
 * f            349 Hz          2864    1432    
 * g            392 Hz          2550    1275    
 * a            440 Hz          2272    1136    
 * b            493 Hz          2028    1014    
 * C            523 Hz          1912    956

 */
void play_note() {
  byte names[] = {'c', 'd', 'e', 'f', 'g', 'a', 'b', 'C'};  
  int tones[] = {1915, 1700, 1519, 1432, 1275, 1136, 1014, 956};
  
    for (int note_len = 0; note_len <= (melody[melody_ptr*2] - 48) * 30; note_len++) {
      for (int name_ptr=0;name_ptr<8;name_ptr++) {
        if (names[name_ptr] == melody[melody_ptr*2 + 1]) {       
          analogWrite(speakerOut,500);
          delayMicroseconds(tones[name_ptr]);
          analogWrite(speakerOut, 0);
          delayMicroseconds(tones[name_ptr]);
          break;
        } 
        if (melody[melody_ptr*2 + 1] == 'p') {
          // make a pause of a certain size
          analogWrite(speakerOut, 0);
          delayMicroseconds(500);
          break;
        }
      }
    }
}

///////////////////////////////
// RGB
///////////////////////////////


/* Set the button color
 *
 * value is a String being "r,g,b"
 */
void set_color(String value){
  int commaIndex = value.indexOf(',');  
  analogWrite(RPIN, value.substring(0, commaIndex).toInt());
  analogWrite(GPIN, value.substring(commaIndex+1, value.indexOf(',', commaIndex+1)).toInt());
  analogWrite(BPIN, value.substring(value.indexOf(',', commaIndex+1)+1).toInt());
}

///////////////////////////////
// Button
///////////////////////////////

/*
 * Interrupt raised when button is being pushed
 * Could do without but this ensure we quickly read the button
 */
void pushed()
{
/*  Serial.print("Interrupt, last was ");
  Serial.print(millis()-push_time);
  Serial.print(" ago, are we counting: ");
  Serial.println(push_counting);*/
  if (!push_counting)
  {
    Serial.println("Down");
    push_counting = true;
    push_sent = false;
    push_time = millis();
  }
}

