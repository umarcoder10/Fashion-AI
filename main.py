import customtkinter as ctk
from splash import SplashScreen
from ui import FashionApp

def launch_main():
    app = FashionApp()
    app.mainloop()

if __name__ == "__main__":
    splash = SplashScreen(on_finish=launch_main)
    splash.mainloop()