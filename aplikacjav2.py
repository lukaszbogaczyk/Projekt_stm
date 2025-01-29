import serial
import time
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import csv

# Konfiguracja UART
PORT = "COM5"
BAUDRATE = 9600
TIMEOUT = 1

ser = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT)

times = []
var1_data = []
var2_data = []

temp = 0

# Maksymalna liczba punktów na wykresie
MAX_POINTS = 20

start_time = time.time()

# Zmienna do przechowywania flagi, która pozwala naprzemiennie przetwarzać wiadomości
message_flag = 0


# Funkcja do odczytu danych z UART
def read_data_from_uart():
    global message_flag
    try:
        # Odczytujemy dane z UART
        line = ser.readline().decode("utf-8", errors="ignore").strip()  # ignore errors in decoding
        if line:

            if "|" in line:
                values = list(map(float, line.split("|")))

                if message_flag == 0:
                    # Pierwsza wiadomość: float1|float2
                    var1, var2 = values
                    message_flag = 0
                    print(var1,var2)
                    return var1, var2, None, None  # Zwróć float1, float2, brak danych dla float3, float4
                # elif message_flag == 1:
                    # Druga wiadomość: float3|float4
                    # line = line.lstrip('|')

                    # float3 = float(va)
                    # float4 = temp

                    # message_flag = 0
                    # return None, None, float3, float4  # Zwróć float3, float4, brak danych dla float1, float2
            else:
                float3 = float(line)
                float4 = temp
                print(line)
                return None, None, float3, float4

                # print(f"Nieprawidłowy format danych: {line}")
        else:
            print("Pusta linia odczytana z UART.")
    except ValueError as e:
        print(f"Nie można przekonwertować danych na float: {e}")
    except Exception as e:
        print(f"Błąd: {e}")
    return None, None, None, None


# Funkcja do wysyłania danych
def send_data(value):
    try:
        value_float = float(value)
        ser.write(f"{value_float}\n".encode("utf-8"))
        print(f"Wysłano: {value_float}")
        entry_value.delete(0, tk.END)
    except ValueError:
        print("Wprowadź poprawną liczbę zmiennoprzecinkową!")
    except Exception as e:
        print(f"Błąd: {e}")


# Funkcja do zapisywania danych float3, float4 do pliku CSV

def save_data_to_csv(var1, var2,float3):
    try:
        with open("output.csv", mode="a", newline="") as file:
            writer = csv.writer(file, delimiter=" ")
            writer.writerow([var1, var2,float3])
    except Exception as e:
        print(f"Błąd: {e}")


# Funkcja do aktualizacji wykresu
def update_plot(frame):
    global times, var1_data, var2_data

    current_time = time.time() - start_time

    while ser.in_waiting > 0:
        var1, var2, float3, float4 = read_data_from_uart()

        if var1 is not None and var2 is not None:
            times.append(current_time)
            var1_data.append(var1)
            var2_data.append(var2)
            save_data_to_csv(var1, var2,float3)
            if len(times) > MAX_POINTS:
                times = times[-MAX_POINTS:]
                var1_data = var1_data[-MAX_POINTS:]
                var2_data = var2_data[-MAX_POINTS:]
        if float3 is not None and float4 is not None:
            save_data_to_csv(var1, var2,float3)


    # Aktualizacja danych na wykresie
    ax1.clear()
    ax1.plot(times, var1_data, label="Wartości zadana", color="blue")
    ax1.plot(times, var2_data, label="Wartość aktualna", color="orange")
    ax1.legend()
    ax1.set_title("Dane z stma")
    ax1.set_xlabel("Czas [s]")
    ax1.set_ylabel("Temperatura[°C]")
    ax1.grid()


# Tworzenie GUI
root = tk.Tk()
root.title("Aplikacja do kontroli temperatury")

frame = ttk.Frame(root, padding=10)
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

entry_label = ttk.Label(frame, text="Wprowadź zadaną temperaturę:")
entry_label.grid(row=0, column=0, padx=5, pady=5)

entry_value = ttk.Entry(frame, width=20)
entry_value.grid(row=0, column=1, padx=5, pady=5)

# Przycisk do wysyłania danych
send_button = ttk.Button(frame, text="Wyślij", command=lambda: send_data(entry_value.get()))
send_button.grid(row=0, column=2, padx=5, pady=5)


# Funkcja do Enter
def on_enter_pressed(event):
    send_data(entry_value.get())


# Funkcja do Enter C.D.
entry_value.bind('<Return>', on_enter_pressed)

# Tworzenie wykresu
fig, ax1 = plt.subplots(figsize=(6, 4))
canvas = FigureCanvasTkAgg(fig, master=frame)
canvas.get_tk_widget().grid(row=1, column=0, columnspan=3, padx=10, pady=10)

# Animacja wykresu
ani = FuncAnimation(fig, update_plot, interval=100)

# Uruchomienie GUI
try:
    root.mainloop()
except KeyboardInterrupt:
    print("Zamykanie")
finally:
    ser.close()
