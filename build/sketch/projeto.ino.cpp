#include <Arduino.h>
#line 1 "C:\\Python\\Projeto\\projeto\\projeto.ino"
#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;
const int buttonPin1 = 7; // Pino onde o botão está conectado
const int buttonPin2 = 8; // Pino onde o segundo botão está conectado

// Variáveis para média móvel
const int numReadings = 10; // Número de leituras para a média
int readings[numReadings];  // Armazena as leituras
int readIndex = 0;          // Índice da leitura atual
long total = 0;             // Soma das leituras
int average = 0;            // Média das leituras

#line 15 "C:\\Python\\Projeto\\projeto\\projeto.ino"
void setup();
#line 35 "C:\\Python\\Projeto\\projeto\\projeto.ino"
void loop();
#line 15 "C:\\Python\\Projeto\\projeto\\projeto.ino"
void setup() {
  Serial.begin(115200);
  Wire.begin();
  mpu.initialize();

  // Configura o DLPF para reduzir o ruído
  mpu.setDLPFMode(MPU6050_DLPF_BW_5); // Frequência de corte de 5Hz

  // Configura a faixa de sensibilidade do acelerômetro para ±2g
  mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_2);

  pinMode(buttonPin1, INPUT_PULLUP);
  pinMode(buttonPin2, INPUT_PULLUP);

  // Inicializa o array de leituras com zero
  for (int thisReading = 0; thisReading < numReadings; thisReading++) {
    readings[thisReading] = 0;
  }
}

void loop() {
  int16_t ax, ay, az;
  int16_t gx, gy, gz;

  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  int buttonState1 = digitalRead(buttonPin1);
  int buttonState2 = digitalRead(buttonPin2);

  buttonState2 = !buttonState2;

  // Implementa a média móvel para 'ay'
  total = total - readings[readIndex];   // Subtrai a leitura mais antiga
  readings[readIndex] = ay;              // Lê o novo valor
  total = total + readings[readIndex];   // Adiciona a nova leitura
  readIndex = readIndex + 1;             // Avança para o próximo índice

  // Se chegamos ao final do array, voltamos ao início
  if (readIndex >= numReadings) {
    readIndex = 0;
  }

  // Calcula a média
  average = total / numReadings;

  // Formatar a saída serial
  Serial.print("ay:");
  Serial.print(average);
  Serial.print(",button1:");
  Serial.print(buttonState1);
  Serial.print(",button2:");
  Serial.print(buttonState2);
  Serial.println();  // Garante a quebra de linha

  delay(20);  // Reduz o delay para melhorar a taxa de atualização
}

