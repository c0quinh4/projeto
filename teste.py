import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Configuração da porta serial com taxa de baud aumentada
ser = serial.Serial('COM5', 115200, timeout=1)

# Variáveis para plotagem
fig, ax = plt.subplots()
ys = []

def animate(i):
    # Ler todas as linhas disponíveis no buffer serial
    while ser.in_waiting:
        line = ser.readline()

        # Tente decodificar a linha; se falhar, ignore
        try:
            line = line.decode('utf-8').rstrip()
        except UnicodeDecodeError:
            print("Dados inválidos recebidos, ignorando esta linha.")
            continue

        # Dividir a linha por vírgulas
        parts = line.split(',')

        # Dicionário para armazenar os valores
        data = {}

        # Iterar sobre cada parte e extrair chave e valor
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                data[key] = value

        # Se 'ay' estiver nos dados, processar
        if 'ay' in data:
            try:
                ay_value = int(data['ay'])
                ys.append(ay_value)
            except ValueError:
                print("Não foi possível converter o valor para inteiro:", data['ay'])
                continue
        else:
            print("Linha recebida não contém 'ay':", line)

    # Limite a lista para os últimos 100 valores
    ys_recent = ys[-100:]

    # Limpe o gráfico e plote os novos dados
    ax.clear()
    ax.plot(ys_recent)
    ax.set_ylim([-32768, 32767])  # Limites para valores int16
    ax.set_title('Aceleração no Eixo Y')
    ax.set_xlabel('Amostras')
    ax.set_ylabel('Valor de ay')
    ax.grid(True)  # Adiciona o grid ao gráfico

# Reduzido o intervalo para 50ms para atualização mais rápida
ani = animation.FuncAnimation(fig, animate, interval=50)
plt.show()
