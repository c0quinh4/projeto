import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.ticker as ticker
from collections import deque

# Abrir porta serial
try:
    ser = serial.Serial('COM5', 115200, timeout=1)
    print("Porta serial COM5 aberta com sucesso.")
except serial.SerialException:
    print("Erro: Não foi possível abrir a porta serial COM5")
    ser = None
if ser is None:
    raise SystemExit("Programa encerrado devido à falha na abertura da porta serial.")

# Configuração do gráfico
fig, ax = plt.subplots()
ys = deque(maxlen=100)
Y_MIN = -20000
Y_MAX = 20000
Y_TICKS = [-20000, -15600, -15000, -10000, 0, 10000, 15000, 15600, 20000]
ax.set_ylim([Y_MIN, Y_MAX])
ax.set_yticks(Y_TICKS)
# Definindo os minor ticks com múltiplos de 5000
ax.yaxis.set_minor_locator(ticker.MultipleLocator(5000))
# Configuração da grade
ax.grid(which='major', linestyle='-', linewidth='0.75', color='black')
ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
# Títulos e rótulos dos eixos
ax.set_title('Aceleração no Eixo Y', fontsize=14)
ax.set_xlabel('Amostras', fontsize=12)
ax.set_ylabel('Valor de ay', fontsize=12)
# Configuração do eixo X
ax.set_xlim(0, 99)
ax.set_xticks(range(0, 100, 10))
# Estilização dos ticks para melhor visibilidade
ax.tick_params(axis='both', which='major', labelsize=10)
# Linha do gráfico
line, = ax.plot([], [], color='blue')
def init():
    """Inicializa a linha do gráfico."""
    line.set_data([], [])
    return line,
def animate(frame):
    """ Função de animação que atualiza os dados do gráfico. """
    if ser.in_waiting:
        try:
            while ser.in_waiting:
                line_data = ser.readline()
                try:
                    line_data = line_data.decode('utf-8').rstrip()
                except UnicodeDecodeError:
                    continue
                parts = line_data.split(',')
                data = {}
                for part in parts:
                    if ':' in part:
                        key, value = part.split(':', 1)
                        data[key] = value
                if 'ay' in data:
                    try:
                        ay_value = int(data['ay'])
                        ys.append(ay_value)
                    except ValueError:
                        continue
        except Exception as e:
            print(f"Erro ao ler dados seriais: {e}")
    ys_list = list(ys)
    if len(ys_list) < 100:
        ys_padded = [0]*(100 - len(ys_list)) + ys_list
    else:
        ys_padded = ys_list
    line.set_data(range(len(ys_padded)), ys_padded)
    return line,
# Criação da animação
ani = animation.FuncAnimation(
    fig, animate, init_func=init,
    interval=50, blit=True
)
plt.show()
# Fecha a porta serial após o fechamento do gráfico
ser.close()