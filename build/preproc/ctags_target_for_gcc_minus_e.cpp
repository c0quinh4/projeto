# 1 "C:\\Python\\Projeto\\projeto\\projeto.ino"
# 2 "C:\\Python\\Projeto\\projeto\\projeto.ino" 2
# 3 "C:\\Python\\Projeto\\projeto\\projeto.ino" 2
MPU6050 mpu;

// Definição dos pinos dos botões
const int buttonPin1 = 4; // Pino Botão 1
const int buttonPin2 = 5; // Pino Botão 2
const int buttonPin3 = 2; // Pino Botão 3
const int buttonPin4 = 3; // Pino Botão 4
// Variáveis para média móvel
const int numReadings = 10; // Número de leituras para a média
int readings[numReadings]; // Armazena as leituras
int readIndex = 0; // Índice da leitura atual
long total = 0; // Soma das leituras
int average = 0; // Média das leituras

void setup() {
  Serial.begin(115200);
  Wire.begin();
  mpu.initialize();
  // Configura o DLPF para reduzir o ruído
  mpu.setDLPFMode(0x06); // Frequência de corte de 5Hz
  // Configura a faixa de sensibilidade do acelerômetro para ±2g
  mpu.setFullScaleAccelRange(0x00);
  // Configura os botões como pull up
  pinMode(buttonPin1, 0x2);
  pinMode(buttonPin2, 0x2);
  pinMode(buttonPin3, 0x2);
  pinMode(buttonPin4, 0x2);
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
  int buttonState3 = digitalRead(buttonPin3);
  int buttonState4 = digitalRead(buttonPin4);
  // Inverte os estados dos botões
  buttonState1 = !buttonState1;
  buttonState2 = !buttonState2;
  buttonState3 = !buttonState3;
  buttonState4 = !buttonState4;
  // Implementa a média móvel para 'ay'
  total = total - readings[readIndex]; // Subtrai a leitura mais antiga
  readings[readIndex] = ay; // Lê o novo valor
  total = total + readings[readIndex]; // Adiciona a nova leitura
  readIndex = readIndex + 1; // Avança para o próximo índice
  // Se chega no final do array, volta ao início
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
  Serial.print(buttonState3);
  Serial.print(",button4:");
  Serial.print(buttonState4);
  Serial.println();
  delay(20);
}
