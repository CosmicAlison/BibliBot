#include <Servo.h> 

#include <AFMotor.h>

AF_DCMotor motor1(2);//right motor
AF_DCMotor motor2(3);//left motor
const int trigPin = A0;  
const int echoPin = A1; 
float duration, distance; 
bool found = 0; 
int reading;
bool result;
Servo myservo;	// create servo object to control a servo
int pos;	// variable to store the servo position
int count;
int x; //stores command from python script 

void setup() {
  // put your setup code here, to run once:
	pinMode(trigPin, OUTPUT);  
	pinMode(echoPin, INPUT);  
	Serial.begin(9600);  

  // attaches the servo on pin 10 to the servo object
	myservo.attach(9);   
  myservo.write(80);
  motor1.setSpeed(150);
  motor2.setSpeed(150);

}

void greet(){
  motor1.run(FORWARD);
  motor2.run(FORWARD);
  delay(600);
  motor1.run(RELEASE);
  motor2.run(RELEASE);
}

void shake_head(){
  myservo.write(45);
  delay(18);
  myservo.write(80);
  delay(18);
  myservo.write(115);
  delay(18);
  myservo.write(80);
}

void dance(){
    motor1.run(FORWARD);
    motor2.run(FORWARD);
    delay(400);
    motor1.run(RELEASE);
    motor2.run(RELEASE);
    delay(200);
    motor1.run(BACKWARD);
    motor2.run(BACKWARD);
    delay(400);
    motor1.run(RELEASE);
    motor2.run(RELEASE);
    delay(1000);
}

float read(){
  digitalWrite(trigPin, LOW);  
	delayMicroseconds(2);  
	digitalWrite(trigPin, HIGH);  
	delayMicroseconds(10);  
	digitalWrite(trigPin, LOW); 
  duration = pulseIn(echoPin, HIGH);  
  distance = (duration/5)/29.1;
  return distance;
}

void loop() {
  // put your main code here, to run repeatedly:
	while (Serial.available()>0)
  {
    x = Serial.read();
    //command 1 asks arduino to check for a nearby object 
    if (x == 'a'){
      reading = read();
      Serial.println(reading);
      delay(500);  
    }
    //command 2 asks arduino to shake head 
    if (x == 'b'){
      shake_head();
    }
    //command 3 asks arduino to dance 
    if (x == 'c'){
      dance();
    }
    if (x == 'd'){
      greet();
    }
  }
}
