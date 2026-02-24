import math
import random
import matplotlib.pyplot as plt

class UniformGenerator:

    def __init__(self, seed=None):
        if seed is None:
            seed = random.randint(1, 1000000)

        self.a = 16807
        self.c = 0
        self.m = 2147483647
        self.x = seed
    def next(self):

        self.x = (self.a * self.x + self.c) % self.m
        return self.x / self.m

def poisson_generator(lmbda, gen):
    x = -1
    s = 1
    q = math.exp(-lmbda)

    while s > q:
        u = gen.next()
        s = s * u
        x += 1
    return x

def normal_generator(mu, sigma, gen):
    while True:
        u1 = 2 * gen.next() - 1
        u2 = 2 * gen.next() - 1
        s = u1 * u1 + u2 * u2
        if 0 < s < 1:
            factor = math.sqrt(-2 * math.log(s) / s)
            z1 = u1 * factor
            z2 = u2 * factor
            x1 = mu + sigma * z1
            x2 = mu + sigma * z2
            return x1, x2

def generate_poisson(lmbda, n, seed=None):
    gen = UniformGenerator(seed)
    data = []
    for i in range(n):
        x = poisson_generator(lmbda, gen)
        data.append(x)
    return data

def generate_normal(mu, sigma, n, seed=None):
    gen = UniformGenerator(seed)
    data = []
    i = 0
    while i < n:
        x1, x2 = normal_generator(mu, sigma, gen)
        data.append(x1)
        if len(data) < n:
            data.append(x2)
        i += 2
    return data

def plot_histogram(data, title):
    plt.hist(data, bins=30, density=True)
    plt.title(title)
    plt.xlabel("Wartość")
    plt.ylabel("Częstość")
    plt.grid(True)
    plt.show()

def main():
    print("==============================")
    print(" Generator rozkładów losowych ")
    print("==============================")
    print("1 - Poisson")
    print("2 - Normalny (Gauss)")
    print("==============================")

    choice = int(input("Wybierz rozkład: "))
    n = int(input("Podaj liczbę próbek N: "))
    seed_input = input("Podaj ziarno (ENTER = losowe): ")
    if seed_input == "":
        seed = None
    else:
        seed = int(seed_input)

    if choice == 1:
        lmbda = float(input("Podaj λ: "))
        data = generate_poisson(lmbda, n, seed)
        title = "Rozkład Poissona (λ = " + str(lmbda) + ")"
        plot_histogram(data, title)
    
    elif choice == 2:
        mu = float(input("Podaj μ: "))
        sigma = float(input("Podaj σ: "))
        data = generate_normal(mu, sigma, n, seed)
        title = "Rozkład normalny (μ = " + str(mu) + ", σ = " + str(sigma) + ")"
        plot_histogram(data, title)

    else:
        print("Błędny wybór!")

if __name__ == "__main__":
    main()