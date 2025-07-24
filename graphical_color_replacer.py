#!/usr/bin/env python3
import tkinter as tk
from tkinter import colorchooser, font, messagebox
import re
import argparse
from pathlib import Path

try:
    import webcolors
except ImportError:
    messagebox.showerror(
        "Missing Library",
        "Error: The 'webcolors' library is required.\n\nPlease install it using: pip install webcolors"
    )
    exit(1)

def color_to_hex(color_string: str) -> str:
    """Converts any valid color string (name or hex) to a 6-digit hex code."""
    if color_string.startswith("#"):
        if len(color_string) == 4:
            return f"#{color_string[1]*2}{color_string[2]*2}{color_string[3]*2}"
        return color_string
    try:
        return webcolors.name_to_hex(color_string)
    except ValueError:
        return "#FFFFFF"

class ColorEditorApp:
    def __init__(self, master, file_path: Path):
        self.master = master
        self.file_path = file_path
        self.original_content = self.file_path.read_text()
        self.replacements = {}

        hex_regex = r"#(?:[a-fA-F0-9]{3}){1,2}"
        found_hex = set(re.findall(hex_regex, self.original_content, re.IGNORECASE))

        all_names = webcolors.CSS3_NAMES_TO_HEX.keys()
        names_regex = r'\b(' + '|'.join(all_names) + r')\b'
        found_names = set(re.findall(names_regex, self.original_content, re.IGNORECASE))

        self.found_colors = sorted(list(found_hex | found_names), key=str.lower)

        self.master.title(f"Color Editor - {self.file_path.name}")
        self.master.geometry("400x600")

        self._create_widgets()

    def _create_widgets(self):
        """Create and layout the GUI elements with a robust scrollbar."""
        # --- WIDGET CREATION ---

        # 1. Create the bottom button first, but don't pack it yet.
        save_button = tk.Button(self.master, text="Save Changes and Exit", command=self._save_and_exit, height=2)

        # 2. Create the main frame that will hold the scrollable area.
        main_frame = tk.Frame(self.master)

        canvas = tk.Canvas(main_frame)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas) # The frame that will hold the color list

        # 3. Configure the canvas and scrollbar to work together.
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # --- LAYOUT (PACKING) ---

        # 4. Pack the Save button to the BOTTOM of the window first.
        save_button.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # 5. Pack the main_frame to fill all REMAINING space.
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 6. Pack the canvas and scrollbar inside the main_frame.
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- POPULATE CONTENT ---
        self._populate_colors()

    def _populate_colors(self):
        """Adds the color rows to the scrollable frame."""
        if not self.found_colors:
             tk.Label(self.scrollable_frame, text="No valid HTML colors found.", pady=20).pack()
        else:
            header_font = font.Font(family="Helvetica", size=12, weight="bold")
            tk.Label(self.scrollable_frame, text="Click a color to change it:", font=header_font, pady=10).pack()

            for original_color in self.found_colors:
                self._create_color_row(self.scrollable_frame, original_color)

    def _create_color_row(self, parent, original_color):
        """Creates a single row for a color swatch and its label."""
        row_frame = tk.Frame(parent)
        row_frame.pack(fill=tk.X, pady=2)

        initial_hex = color_to_hex(original_color)

        swatch = tk.Label(row_frame, text="    ", bg=initial_hex, relief="ridge", borderwidth=2)
        swatch.pack(side=tk.LEFT, padx=5)

        text_label = tk.Label(row_frame, text=original_color, anchor="w")
        text_label.pack(side=tk.LEFT, expand=True, fill=tk.X)

        click_handler = lambda e, oc=original_color, s=swatch, t=text_label: self._on_swatch_click(oc, s, t)
        row_frame.bind("<Button-1>", click_handler)
        swatch.bind("<Button-1>", click_handler)
        text_label.bind("<Button-1>", click_handler)

    def _on_swatch_click(self, original_color, swatch_widget, text_widget):
        """Handles the color picking event."""
        current_color = swatch_widget.cget("bg")
        new_color_tuple = colorchooser.askcolor(initialcolor=current_color, title="Pick a new color")

        if new_color_tuple and new_color_tuple[1]:
            new_hex = new_color_tuple[1]
            self.replacements[original_color] = new_hex
            swatch_widget.config(bg=new_hex)
            text_widget.config(text=f"{original_color}  ->  {new_hex}")

    def _save_and_exit(self):
        """Applies the replacements and saves the new file."""
        if not self.replacements:
            self.master.destroy()
            return

        modified_content = self.original_content
        for old, new in self.replacements.items():
            pattern = r'\b' + re.escape(old) + r'\b' if old.isalpha() else re.escape(old)
            modified_content = re.sub(pattern, new, modified_content, flags=re.IGNORECASE)

        new_file_path = self.file_path.with_name(f"{self.file_path.stem}-modified{self.file_path.suffix}")
        new_file_path.write_text(modified_content)

        messagebox.showinfo("Success", f"Modified file saved as:\n{new_file_path}")
        self.master.destroy()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A GUI tool to find and replace HTML colors in a text file.")
    parser.add_argument("filename", help="The path to the file to process.")
    args = parser.parse_args()

    file = Path(args.filename)
    if not file.is_file():
        messagebox.showerror("Error", f"File not found:\n{file}")
        exit(1)

    root = tk.Tk()
    app = ColorEditorApp(root, file)
    root.mainloop()
