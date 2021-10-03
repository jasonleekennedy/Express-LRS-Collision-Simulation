
RNG_MAX = 32767


class Rng(object):
    def __init__(self, seed, master):
        self.seed = seed
        self.master = master

    def next(self):
        m = 2147483648
        a = 214013
        c = 2531011
        self.seed = (a * self.seed + c) % m
        self.seed = self.seed % 4294967296  # reflect the overflow of a unsigned long

        # print(self.seed, self.seed >> 16)
        return self.seed >> 16

    def rngN110(self, max):
        x = self.next()
        result = int(int(x * max) / RNG_MAX)
        result %= 4294967296  # reflect the overflow of a unsigned int

        return result

    def rngNMaster(self, max):
        return self.next() % max

    def rngN(self, max):
        if self.master:
            return self.rngNMaster(max)
        else:
            return self.rngN110(max)


if __name__ == '__main__':
    rng = Rng(24, True)

    for x in range(80000):
        y = rng.rngN(80)
        if y >= 80:
            print(y)
