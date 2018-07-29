from pyfiglet import Figlet

class CLI(object):
    """docstring for CLI"""
    def __init__(self):
        super(CLI, self).__init__()
        

    def start(self):
        print(self.welcome())
        self.verify()

    def welcome(self):
        f = Figlet(font='starwars')
        print("Welcome to ...")
        print(f.renderText('\tKW 2.0'))

    def verify(self):
        pass


if __name__ == "__main__":
    cli = CLI()

    cli.welcome()