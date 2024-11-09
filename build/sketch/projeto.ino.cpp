#include <Arduino.h>
#line 1 "C:\\Python\\Projeto\\projeto\\projeto.ino"
#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;

// Definição dos pinos dos botões
const int buttonPin1 = 0;  // Pino onde o Botão 1 está conectado
const int buttonPin2 = 2;  // Pino onde o Botão 2 está conectado
const int buttonPin3 = 3; // Pino onde o Botão 3 está conectado
const int buttonPin4 = 4; // Pino onde o Botão 4 está conectado

// Variáveis para média móvel
const int numReadings = 10; // Número de leituras para a média
int readings[numReadings];  // Armazena as leituras
int readIndex = 0;          // Índice da leitura atual
long total = 0;             // Soma das leituras
int average = 0;            // Média das leituras

// Variáveis para estados dos novos botões
int buttonState3 = 0;
int buttonState4 = 0;

#line 23 "C:\\Python\\Projeto\\projeto\\projeto.ino"
void setup();
#line 53 "C:\\Python\\Projeto\\projeto\\projeto.ino"
void loop();
#line 23 "C:\\Python\\Projeto\\projeto\\projeto.ino"
void setup() {
  Serial.begin(115200);
  Wire.begin();
  mpu.initialize();

  // Configura o DLPF para reduzir o ruído
  mpu.setDLPFMode(MPU6050_DLPF_BW_5); // Frequência de corte de 5Hz

  // Configura a faixa de sensibilidade do acelerômetro para ±2g
  mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_2);

  // Configura os pinos dos botões
  pinMode(buttonPin1, INPUT_PULLUP);
  pinMode(buttonPin2, INPUT_PULLUP);
  pinMode(buttonPin3, INPUT_PULLUP); // Configura o Botão 3 como entrada com pull-up
  pinMode(buttonPin4, INPUT_PULLUP); // Configura o Botão 4 como entrada com pull-up

  // Inicializa o array de leituras com zero
  for (int thisReading = 0; thisReading < numReadings; thisReading++) {
    readings[thisReading] = 0;
  }

  // Verifica se o sensor está funcionando corretamente
  if (mpu.testConnection()) {
    Serial.println("MPU6050 funcionando corretamente.");
  } else {
    Serial.println("Falha na conexão com MPU6050.");
  }
}

void loop() {
  int16_t ax, ay, az;
  int16_t gx, gy, gz;

  // Lê os dados do acelerômetro e giroscópio
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  // Leitura dos estados dos botões
  int buttonState1 = digitalRead(buttonPin1);
  int buttonState2 = digitalRead(buttonPin2);
  buttonState3 = digitalRead(buttonPin3); // Leitura do Botão 3
  buttonState4 = digitalRead(buttonPin4); // Leitura do Botão 4

  // Inverte os estados dos botões (INPUT_PULLUP)
  buttonState1 = !buttonState1;
  buttonState2 = !buttonState2;
  buttonState3 = !buttonState3; // Inverte o estado do Botão 3
  buttonState4 = !buttonState4; // Inverte o estado do Botão 4

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
  Serial.print(",button3:");
  Serial.print(buttonState3); // Inclui o estado do Botão 3
  Serial.print(",button4:");
  Serial.print(buttonState4); // Inclui o estado do Botão 4
  Serial.println();  // Garante a quebra de linha

  delay(20);  // Reduz o delay para melhorar a taxa de atualização
}

