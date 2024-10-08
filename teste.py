import serial
import time

def test_serial(port='COM4', baudrate=9600):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        ser.flush()
        print(f"Conectado ao Arduino na porta {port}.")
    except serial.SerialException:
        print(f"Falha ao conectar com o Arduino na porta {port}. Verifique a conexão.")
        return

    try:
        while True:
            if ser.in_waiting > 0:
                linha = ser.readline().decode('utf-8').rstrip()
                try:
                    steering_value = float(linha)
                    print(f"Valor de Direção: {steering_value}")
                except ValueError:
                    print("Valor inválido recebido.")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Encerrando o teste serial.")
    finally:
        ser.close()

if __name__ == "__main__":
    test_serial()