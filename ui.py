import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import requests
import io
import os
import json
from datetime import datetime
from PIL import Image, ImageTk
from analyzer import analyze_outfit

# ── Theme ──────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

HISTORY_FILE = "history.json"

class FashionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Fashion AI - Outfit Suggester")
        self.state("zoomed")  # full screen on Windows
        self.image_path = None
        self.current_image_prompt = None
        self.current_outfit_image = None
        self.is_dark = False
        self.history = self.load_history()
        self.build_ui()

    # ── History helpers ────────────────────────────────────────
    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        return []

    def save_history(self, style, suggestion):
        entry = {
            "date": datetime.now().strftime("%d %b %Y, %I:%M %p"),
            "style": style,
            "suggestion": suggestion[:200] + "..."
        }
        self.history.insert(0, entry)
        self.history = self.history[:20]  # keep last 20
        with open(HISTORY_FILE, "w") as f:
            json.dump(self.history, f)

    # ── Build UI ───────────────────────────────────────────────
    def build_ui(self):
        # ── Top bar ──────────────────────────────────────────
        self.top_bar = ctk.CTkFrame(self, height=65, corner_radius=0, fg_color="#1d4ed8")
        self.top_bar.pack(fill="x")
        self.top_bar.pack_propagate(False)

        ctk.CTkLabel(self.top_bar, text="👗  Fashion AI",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="white").pack(side="left", padx=25)

        # Dark mode toggle
        self.theme_btn = ctk.CTkButton(self.top_bar,
            text="🌙 Dark Mode", width=130, height=35,
            fg_color="#2563eb", hover_color="#1e40af",
            command=self.toggle_theme)
        self.theme_btn.pack(side="right", padx=15, pady=15)

        ctk.CTkLabel(self.top_bar,
            text="Your Personal AI Stylist",
            font=ctk.CTkFont(size=13),
            text_color="#bfdbfe").pack(side="left")

        # ── Tab view ─────────────────────────────────────────
        self.tabs = ctk.CTkTabview(self, corner_radius=10)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=15)

        self.tab_main = self.tabs.add("✨  Outfit Suggester")
        self.tab_history = self.tabs.add("🕓  History")

        self.build_main_tab()
        self.build_history_tab()

    # ── Main Tab ───────────────────────────────────────────────
    def build_main_tab(self):
        self.tab_main.columnconfigure(0, weight=0)
        self.tab_main.columnconfigure(1, weight=1)
        self.tab_main.rowconfigure(0, weight=1)

        # ── Left panel ───────────────────────────────────────
        left = ctk.CTkFrame(self.tab_main, width=300, corner_radius=15)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 15), pady=5)
        left.pack_propagate(False)

        ctk.CTkLabel(left, text="Upload Photo",
            font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 8))

        self.photo_box = ctk.CTkLabel(left,
            text="📷\n\nNo photo uploaded",
            width=260, height=300,
            fg_color="#eff6ff", corner_radius=12,
            text_color="#3b82f6",
            font=ctk.CTkFont(size=13))
        self.photo_box.pack(padx=20)

        ctk.CTkButton(left, text="📂  Upload Photo",
            command=self.upload_photo, height=40,
            font=ctk.CTkFont(size=14, weight="bold")).pack(padx=20, pady=12, fill="x")

        ctk.CTkLabel(left, text="Style Preference:",
            font=ctk.CTkFont(size=13)).pack(pady=(5, 4))

        self.style_var = ctk.StringVar(value="Casual")
        ctk.CTkOptionMenu(left,
            values=["Casual", "Formal", "College Wear", "Party Wear", "Traditional"],
            variable=self.style_var, height=38,
            font=ctk.CTkFont(size=13)).pack(padx=20, fill="x")

        self.analyze_btn = ctk.CTkButton(left,
            text="✨  Get Outfit Suggestions",
            command=self.run_analysis, height=45,
            font=ctk.CTkFont(size=14, weight="bold"))
        self.analyze_btn.pack(padx=20, pady=15, fill="x")

        # ── Right panel ──────────────────────────────────────
        right = ctk.CTkFrame(self.tab_main, corner_radius=15)
        right.grid(row=0, column=1, sticky="nsew", pady=5)

        # Suggestions header + action buttons
        header = ctk.CTkFrame(right, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))

        ctk.CTkLabel(header, text="Outfit Suggestions",
            font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")

        # Action buttons row
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(btn_frame, text="📋 Copy",
            width=90, height=32,
            command=self.copy_to_clipboard).pack(side="left", padx=4)

        ctk.CTkButton(btn_frame, text="💾 Save PDF",
            width=100, height=32,
            command=self.save_pdf).pack(side="left", padx=4)

        # Suggestions text box
        self.result_box = ctk.CTkTextbox(right,
            font=ctk.CTkFont(size=13), wrap="word",
            state="disabled", height=220)
        self.result_box.pack(fill="x", padx=20, pady=(0, 10))

        # Outfit image header
        img_header = ctk.CTkFrame(right, fg_color="transparent")
        img_header.pack(fill="x", padx=20, pady=(5, 8))

        ctk.CTkLabel(img_header, text="Generated Outfit Preview",
            font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        btn_frame2 = ctk.CTkFrame(img_header, fg_color="transparent")
        btn_frame2.pack(side="right")

        ctk.CTkButton(btn_frame2, text="🔄 Regenerate",
            width=110, height=32,
            command=self.regenerate_image).pack(side="left", padx=4)

        ctk.CTkButton(btn_frame2, text="💾 Save Image",
            width=110, height=32,
            command=self.save_image).pack(side="left", padx=4)

        # Outfit image display
        self.outfit_image_box = ctk.CTkLabel(right,
            text="👗 Outfit image will appear here",
            width=450, height=450,
            fg_color="#eff6ff", corner_radius=12,
            text_color="#3b82f6",
            font=ctk.CTkFont(size=13))
        self.outfit_image_box.pack(pady=(0, 20))

    # ── History Tab ────────────────────────────────────────────
    def build_history_tab(self):
        ctk.CTkLabel(self.tab_history, text="Past Analyses",
            font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 10))

        self.history_scroll = ctk.CTkScrollableFrame(self.tab_history)
        self.history_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.refresh_history_tab()

    def refresh_history_tab(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        if not self.history:
            ctk.CTkLabel(self.history_scroll,
                text="No history yet. Start by getting outfit suggestions!",
                text_color="gray").pack(pady=40)
            return

        for entry in self.history:
            card = ctk.CTkFrame(self.history_scroll, corner_radius=10)
            card.pack(fill="x", pady=6, padx=5)

            ctk.CTkLabel(card,
                text=f"🕓 {entry['date']}   |   👗 {entry['style']}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#1d4ed8").pack(anchor="w", padx=15, pady=(10, 4))

            ctk.CTkLabel(card,
                text=entry["suggestion"],
                font=ctk.CTkFont(size=12),
                text_color="gray", wraplength=800,
                justify="left").pack(anchor="w", padx=15, pady=(0, 10))

    # ── Actions ────────────────────────────────────────────────
    def upload_photo(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp")])
        if path:
            self.image_path = path
            img = Image.open(path)
            img.thumbnail((260, 300))
            photo = ImageTk.PhotoImage(img)
            self.photo_box.configure(image=photo, text="")
            self.photo_box.image = photo

    def run_analysis(self):
        if not self.image_path:
            messagebox.showwarning("No Photo", "Please upload a photo first!")
            return
        self.set_result("🔍 Analyzing your photo... please wait.")
        self.outfit_image_box.configure(image=None,
            text="⏳ Generating outfit image... this takes ~15 seconds")
        self.analyze_btn.configure(state="disabled", text="Analyzing...")
        threading.Thread(target=self.do_analysis, daemon=True).start()

    def do_analysis(self):
        try:
            style = self.style_var.get()
            suggestion_text, image_prompt = analyze_outfit(self.image_path, style)
            self.current_image_prompt = image_prompt
            self.set_result(suggestion_text)
            self.save_history(style, suggestion_text)
            self.after(0, self.refresh_history_tab)
            self.generate_outfit_image(image_prompt)
        except Exception as e:
            self.set_result(f"❌ Error: {str(e)}")
        finally:
            self.analyze_btn.configure(state="normal",
                text="✨  Get Outfit Suggestions")

    def generate_outfit_image(self, prompt):
        try:
            encoded = prompt.replace(" ", "%20")
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=450&height=450&nologo=true"
            response = requests.get(url, timeout=60)
            img = Image.open(io.BytesIO(response.content))
            img = img.resize((450, 450))
            self.current_outfit_image = img
            photo = ImageTk.PhotoImage(img)
            self.outfit_image_box.configure(image=photo, text="")
            self.outfit_image_box.image = photo
        except Exception as e:
            self.outfit_image_box.configure(
                text=f"❌ Image generation failed: {str(e)}")

    def regenerate_image(self):
        if not self.current_image_prompt:
            messagebox.showwarning("No Prompt", "Please get outfit suggestions first!")
            return
        self.outfit_image_box.configure(image=None,
            text="🔄 Regenerating outfit image...")
        threading.Thread(target=lambda: self.generate_outfit_image(
            self.current_image_prompt), daemon=True).start()

    def copy_to_clipboard(self):
        content = self.result_box.get("1.0", "end").strip()
        if not content or content == "🔍 Analyzing your photo... please wait.":
            messagebox.showwarning("Nothing to Copy", "No suggestions yet!")
            return
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copied!", "Suggestions copied to clipboard ✅")

    def save_image(self):
        if not self.current_outfit_image:
            messagebox.showwarning("No Image", "No outfit image to save yet!")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg")])
        if path:
            self.current_outfit_image.save(path)
            messagebox.showinfo("Saved!", f"Outfit image saved ✅")

    def save_pdf(self):
        content = self.result_box.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("Nothing to Save", "No suggestions yet!")
            return
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
        except ImportError:
            if messagebox.askyesno("Install Required",
                "reportlab is needed for PDF. Install it now?"):
                os.system("pip install reportlab")
                messagebox.showinfo("Done", "Installed! Please click Save PDF again.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF File", "*.pdf")])
        if not path:
            return

        doc = SimpleDocTemplate(path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle("title",
            fontSize=22, textColor=colors.HexColor("#1d4ed8"),
            spaceAfter=10, fontName="Helvetica-Bold")
        body_style = ParagraphStyle("body",
            fontSize=12, spaceAfter=6, leading=18)

        story.append(Paragraph("👗 Fashion AI - Outfit Suggestions", title_style))
        story.append(Paragraph(
            f"Generated on: {datetime.now().strftime('%d %b %Y, %I:%M %p')} | Style: {self.style_var.get()}",
            styles["Normal"]))
        story.append(Spacer(1, 20))

        for line in content.split("\n"):
            if line.strip():
                story.append(Paragraph(line, body_style))

        # Add outfit image if available
        if self.current_outfit_image:
            img_path = "temp_outfit.png"
            self.current_outfit_image.save(img_path)
            story.append(Spacer(1, 20))
            story.append(Paragraph("Generated Outfit Preview:", title_style))
            story.append(RLImage(img_path, width=300, height=300))

        doc.build(story)
        messagebox.showinfo("Saved!", f"PDF saved successfully ✅")

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        if self.is_dark:
            ctk.set_appearance_mode("dark")
            self.theme_btn.configure(text="☀️ Light Mode")
        else:
            ctk.set_appearance_mode("light")
            self.theme_btn.configure(text="🌙 Dark Mode")

    def set_result(self, text):
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", text)
        self.result_box.configure(state="disabled")

if __name__ == "__main__":
    app = FashionApp()
    app.mainloop()