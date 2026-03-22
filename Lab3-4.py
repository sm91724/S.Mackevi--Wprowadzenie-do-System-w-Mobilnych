import tkinter as tk
from tkinter import ttk
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import threading

# logika systemu
class Simulator:
    def __init__(self, channels, queue_size, lam, mean, std, t_min, t_max):
        # liczba kanałów (S)
        self.channels = channels

        # maksymalna długość kolejki
        self.queue_size = queue_size

        # parametr rozkładu Poissona (λ)
        self.lam = lam

        # parametry rozkładu Gaussa (czas rozmowy)
        self.mean = mean
        self.std = std
        self.t_min = t_min
        self.t_max = t_max

        # stan kanałów (0 = wolny, >0 = ile sekund pozostało)
        self.channel_state = [0] * channels

        # kolejka (FIFO)
        self.queue = []

        # statystyki
        self.served = 0      # liczba obsłużonych
        self.rejected = 0    # liczba odrzuconych

        # listy do wykresów
        self.wait_times = []
        self.queue_lengths = []
        self.rho_values = []

        self.time = 0  # aktualny czas symulacji


# Poisson
    def generate_arrivals(self):
        return np.random.poisson(self.lam)

    # Gauss
    def generate_service_time(self):
        # losowanie czasu rozmowy
        t = random.gauss(self.mean, self.std)

        # ograniczenie do zakresu min-max
        return max(self.t_min, min(self.t_max, int(t)))


    def step(self):
        self.time += 1

        # 1. generujemy nowe zgłoszenia
        arrivals = self.generate_arrivals()

        for _ in range(arrivals):
            service_time = self.generate_service_time()

            # 2. jeśli jest wolny kanał → obsługuj od razu
            if 0 in self.channel_state:
                idx = self.channel_state.index(0)
                self.channel_state[idx] = service_time
                self.served += 1

                # brak oczekiwania
                self.wait_times.append(0)

            else:
                # 3. jeśli brak kanałów → kolejka lub odrzucenie
                if len(self.queue) < self.queue_size:
                    # zapisujemy (czas rozmowy, moment przyjścia)
                    self.queue.append((service_time, self.time))
                else:
                    # brak miejsca → odrzucenie (blokada)
                    self.rejected += 1

        # 4. obsługa kanałów (zmniejszamy czas rozmowy)
        for i in range(len(self.channel_state)):
            if self.channel_state[i] > 0:
                self.channel_state[i] -= 1

                # jeśli rozmowa się zakończyła
                if self.channel_state[i] == 0 and self.queue:
                    # pobierz z kolejki
                    service_time, arrival_time = self.queue.pop(0)

                    # oblicz czas oczekiwania
                    wait = self.time - arrival_time
                    self.wait_times.append(wait)

                    # przypisz do kanału
                    self.channel_state[i] = service_time
                    self.served += 1

        # 5. obliczamy statystyki
        busy = sum(1 for x in self.channel_state if x > 0)

        # intensywność ruchu ρ
        rho = busy / self.channels

        self.rho_values.append(rho)
        self.queue_lengths.append(len(self.queue))

    # Wyniki
    def get_stats(self):
        Q = np.mean(self.queue_lengths) if self.queue_lengths else 0
        W = np.mean(self.wait_times) if self.wait_times else 0
        rho = np.mean(self.rho_values) if self.rho_values else 0
        return rho, Q, W

# GUI
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Symulator M/M/S/S")

        self.create_inputs()
        self.create_canvas()

        self.running = False

    # Input
    def create_inputs(self):
        frame = ttk.Frame(self.root)
        frame.pack(side=tk.LEFT, padx=10)

        self.entries = {}

        # parametry wejściowe
        params = [
            ("Kanały", 10),
            ("Kolejka", 10),
            ("Lambda", 1.0),
            ("Śr. czas", 20),
            ("Odchylenie", 5),
            ("Min", 5),
            ("Max", 30),
        ]

        # tworzenie pól
        for i, (label, val) in enumerate(params):
            ttk.Label(frame, text=label).grid(row=i, column=0)

            e = ttk.Entry(frame)
            e.insert(0, str(val))
            e.grid(row=i, column=1)

            self.entries[label] = e

        # przycisk start
        self.start_btn = ttk.Button(frame, text="START", command=self.start)
        self.start_btn.grid(row=len(params), column=0, columnspan=2)


    # Bar chart
    def create_canvas(self):
        self.fig, self.ax = plt.subplots(3, 1, figsize=(8, 10))
        self.fig.tight_layout(pad=3.0)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT)

    # Start symulacji
    def start(self):
        self.running = True

        # pobranie parametrów z GUI
        channels = int(self.entries["Kanały"].get())
        queue = int(self.entries["Kolejka"].get())
        lam = float(self.entries["Lambda"].get())
        mean = float(self.entries["Śr. czas"].get())
        std = float(self.entries["Odchylenie"].get())
        tmin = int(self.entries["Min"].get())
        tmax = int(self.entries["Max"].get())

        self.sim = Simulator(channels, queue, lam, mean, std, tmin, tmax)

        threading.Thread(target=self.run).start()



    def run(self):
        for _ in range(200):
            if not self.running:
                break

            self.sim.step()
            self.update_plot()

            time.sleep(0.1)

    # Update wykresow
    def update_plot(self):
        rho, Q, W = self.sim.get_stats()

        for axis in self.ax:
            axis.clear()

        # Q – długość kolejki
        self.ax[0].plot(self.sim.queue_lengths)
        self.ax[0].set_title(f"Średnia długość kolejki Q = {Q:.2f}", fontsize=12)
        self.ax[0].set_xlabel("Czas")
        self.ax[0].set_ylabel("Q")
        self.ax[0].grid(True)

        # W – czas oczekiwania
        self.ax[1].plot(self.sim.wait_times)
        self.ax[1].set_title(f"Średni czas oczekiwania W = {W:.2f}", fontsize=12)
        self.ax[1].set_xlabel("Czas")
        self.ax[1].set_ylabel("W")
        self.ax[1].grid(True)

        # ρ – obciążenie
        self.ax[2].plot(self.sim.rho_values)
        self.ax[2].set_title(f"Intensywność ruchu ρ = {rho:.2f}", fontsize=12)
        self.ax[2].set_xlabel("Czas")
        self.ax[2].set_ylabel("ρ")
        self.ax[2].grid(True)

        self.fig.tight_layout(pad=3.0)
        self.canvas.draw()

# Main
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()