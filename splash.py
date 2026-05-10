import customtkinter as ctk
import threading
import time

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

QUOTES = [
    "Fashion is the armor to survive everyday life...",
    "Style is a way to say who you are without speaking...",
    "Dress how you want to be addressed...",
    "Your outfit is your first impression...",
    "Great style is effortless, but never accidental..."
]

class SplashScreen(ctk.CTk):
    def __init__(self, on_finish):
        super().__init__()
        self.on_finish = on_finish
        self.overrideredirect(True)  # no title bar

        # Center the splash on screen
        w, h = 600, 400
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.configure(fg_color="#0a0f2c")
        self.resizable(False, False)

        self.build_ui()
        self.after(100, self.start_animation)

    def build_ui(self):
        # Logo emoji
        self.logo_label = ctk.CTkLabel(
            self, text="👗",
            font=ctk.CTkFont(size=0),
            text_color="#3b82f6"
        )
        self.logo_label.place(relx=0.5, rely=0.25, anchor="center")

        # App name
        self.title_label = ctk.CTkLabel(
            self, text="Fashion AI",
            font=ctk.CTkFont(size=42, weight="bold"),
            text_color="#ffffff"
        )
        self.title_label.place(relx=0.5, rely=0.45, anchor="center")

        # Tagline
        self.tagline_label = ctk.CTkLabel(
            self, text="Your Personal AI Stylist",
            font=ctk.CTkFont(size=16),
            text_color="#93c5fd"
        )
        self.tagline_label.place(relx=0.5, rely=0.55, anchor="center")

        # Fashion quote
        self.quote_label = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#64748b",
            wraplength=500
        )
        self.quote_label.place(relx=0.5, rely=0.70, anchor="center")

        # Progress bar
        self.progress = ctk.CTkProgressBar(
            self, width=400, height=6,
            fg_color="#1e293b",
            progress_color="#3b82f6"
        )
        self.progress.place(relx=0.5, rely=0.82, anchor="center")
        self.progress.set(0)

        # Loading text
        self.loading_label = ctk.CTkLabel(
            self, text="Loading...",
            font=ctk.CTkFont(size=12),
            text_color="#64748b"
        )
        self.loading_label.place(relx=0.5, rely=0.89, anchor="center")

    def start_animation(self):
        threading.Thread(target=self.animate, daemon=True).start()

    def animate(self):
        import random

        # Phase 1 — grow logo emoji font size
        for size in range(0, 72, 4):
            self.logo_label.configure(font=ctk.CTkFont(size=size))
            time.sleep(0.03)

        time.sleep(0.2)

        # Phase 2 — show a random quote
        quote = random.choice(QUOTES)
        self.quote_label.configure(text=f'"{quote}"')

        # Phase 3 — fill progress bar with loading messages
        steps = [
            (0.2,  "Initializing AI engine..."),
            (0.4,  "Loading style database..."),
            (0.6,  "Preparing color analysis..."),
            (0.8,  "Setting up outfit generator..."),
            (1.0,  "Ready! Launching Fashion AI..."),
        ]

        for value, message in steps:
            self.progress.set(value)
            self.loading_label.configure(text=message)
            time.sleep(0.6)

        time.sleep(0.4)
        self.after(0, self.finish)

    def finish(self):
        self.destroy()
        self.on_finish()