from Generator.generator import Generator
from time import sleep


GEN = Generator()


if __name__ == '__main__':
    while True:
        GEN.runner()
        sleep(5)
