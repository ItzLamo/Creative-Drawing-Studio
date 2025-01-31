import tkinter as tk
from tkinter import ttk, colorchooser, filedialog
from PIL import Image, ImageDraw, ImageTk
import numpy as np
from datetime import datetime
import json
import os

class DrawingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Creative Drawing Studio")
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("Custom.TButton", padding=5, font=('Arial', 10))
        self.style.configure("Custom.TLabel", padding=5, font=('Arial', 10))
        
        # Initialize variables
        self.current_color = "#000000"
        self.brush_size = 2
        self.current_tool = "pen"
        self.layers = []
        self.active_layer = 0
        self.undo_stack = []
        self.redo_stack = []
        self.symmetry_enabled = False
        self.color_history = []
        self.grid_visible = False
        
        self.setup_ui()
        self.create_new_layer()
        
    def setup_ui(self):
        # Main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Toolbar
        self.create_toolbar()
        
        # Canvas area
        self.canvas_frame = ttk.Frame(self.main_container)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=800,
            height=600,
            bg="white",
            cursor="crosshair"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind events
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)
        
        # Layer panel
        self.create_layer_panel()
        
        # Quick actions panel
        self.create_quick_actions()
        
    def create_toolbar(self):
        toolbar = ttk.Frame(self.main_container)
        toolbar.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Tools
        tools = [
            ("Pen", "pen"),
            ("Brush", "brush"),
            ("Eraser", "eraser"),
            ("Spray", "spray"),
            ("Shape", "shape")
        ]
        
        for tool_name, tool_id in tools:
            btn = ttk.Button(
                toolbar,
                text=tool_name,
                style="Custom.TButton",
                command=lambda t=tool_id: self.set_tool(t)
            )
            btn.pack(pady=2)
        
        ttk.Separator(toolbar).pack(fill=tk.X, pady=5)
        
        # Color selector
        ttk.Label(toolbar, text="Color:", style="Custom.TLabel").pack()
        self.color_btn = ttk.Button(
            toolbar,
            text="Choose Color",
            command=self.choose_color
        )
        self.color_btn.pack(pady=2)
        
        # Color history
        self.create_color_history(toolbar)
        
        # Brush size
        ttk.Label(toolbar, text="Brush Size:", style="Custom.TLabel").pack()
        self.size_scale = ttk.Scale(
            toolbar,
            from_=1,
            to=50,
            orient=tk.HORIZONTAL,
            command=self.update_brush_size
        )
        self.size_scale.set(2)
        self.size_scale.pack(pady=2)
        
        # Symmetry toggle
        self.symmetry_btn = ttk.Checkbutton(
            toolbar,
            text="Mirror Mode",
            command=self.toggle_symmetry
        )
        self.symmetry_btn.pack(pady=5)
        
        # Grid toggle
        self.grid_btn = ttk.Checkbutton(
            toolbar,
            text="Show Grid",
            command=self.toggle_grid
        )
        self.grid_btn.pack(pady=5)
        
    def create_layer_panel(self):
        layer_panel = ttk.Frame(self.main_container)
        layer_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        
        ttk.Label(layer_panel, text="Layers", style="Custom.TLabel").pack()
        
        # Layer controls
        controls = ttk.Frame(layer_panel)
        controls.pack(fill=tk.X)
        
        ttk.Button(
            controls,
            text="Add Layer",
            command=self.create_new_layer
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            controls,
            text="Delete Layer",
            command=self.delete_active_layer
        ).pack(side=tk.LEFT, padx=2)
        
        # Layer list
        self.layer_listbox = tk.Listbox(layer_panel, height=10)
        self.layer_listbox.pack(fill=tk.BOTH, expand=True)
        self.layer_listbox.bind('<<ListboxSelect>>', self.on_layer_select)
        
    def create_quick_actions(self):
        quick_panel = tk.Frame(self.canvas_frame, bg='#f0f0f0')
        quick_panel.place(relx=1, rely=0, anchor='ne')
        
        actions = [
            ("Undo", self.undo),
            ("Redo", self.redo),
            ("Clear", self.clear_canvas),
            ("Save", self.save_drawing)
        ]
        
        for action_name, command in actions:
            ttk.Button(
                quick_panel,
                text=action_name,
                command=command,
                style="Custom.TButton"
            ).pack(pady=1)
            
    def create_color_history(self, parent):
        self.color_history_frame = ttk.Frame(parent)
        self.color_history_frame.pack(pady=5)
        self.update_color_history()
        
    def update_color_history(self):
        for widget in self.color_history_frame.winfo_children():
            widget.destroy()
            
        for color in self.color_history[-5:]:  # Show last 5 colors
            btn = tk.Button(
                self.color_history_frame,
                bg=color,
                width=2,
                height=1,
                command=lambda c=color: self.set_color(c)
            )
            btn.pack(side=tk.LEFT, padx=1)
            
    def create_new_layer(self):
        layer = Image.new('RGBA', (800, 600), (255, 255, 255, 0))
        self.layers.append({
            'image': layer,
            'draw': ImageDraw.Draw(layer),
            'visible': True
        })
        self.active_layer = len(self.layers) - 1
        self.update_layer_list()
        
    def update_layer_list(self):
        self.layer_listbox.delete(0, tk.END)
        for i in range(len(self.layers)):
            self.layer_listbox.insert(0, f"Layer {i+1}")
            
    def on_layer_select(self, event):
        selection = self.layer_listbox.curselection()
        if selection:
            self.active_layer = selection[0]
            
    def delete_active_layer(self):
        if len(self.layers) > 1:
            del self.layers[self.active_layer]
            self.active_layer = max(0, self.active_layer - 1)
            self.update_layer_list()
            
    def set_tool(self, tool):
        self.current_tool = tool
        
    def choose_color(self):
        color = colorchooser.askcolor(color=self.current_color)[1]
        if color:
            self.set_color(color)
            
    def set_color(self, color):
        self.current_color = color
        if color not in self.color_history:
            self.color_history.append(color)
            self.update_color_history()
            
    def update_brush_size(self, size):
        self.brush_size = int(float(size))
        
    def toggle_symmetry(self):
        self.symmetry_enabled = not self.symmetry_enabled
        
    def toggle_grid(self):
        self.grid_visible = not self.grid_visible
        self.draw_grid()
        
    def draw_grid(self):
        self.canvas.delete("grid")
        if self.grid_visible:
            for i in range(0, 800, 50):
                self.canvas.create_line(i, 0, i, 600, fill="#cccccc", tags="grid")
            for i in range(0, 600, 50):
                self.canvas.create_line(0, i, 800, i, fill="#cccccc", tags="grid")
                
    def start_draw(self, event):
        self.last_x = event.x
        self.last_y = event.y
        self.drawing = True
        
    def draw(self, event):
        if self.drawing:
            x, y = event.x, event.y
            
            if self.current_tool == "pen":
                self.draw_line(self.last_x, self.last_y, x, y)
            elif self.current_tool == "brush":
                self.draw_brush(x, y)
            elif self.current_tool == "eraser":
                self.erase(x, y)
            elif self.current_tool == "spray":
                self.spray(x, y)
                
            if self.symmetry_enabled:
                mirror_x = 800 - x
                self.draw_line(800 - self.last_x, self.last_y, mirror_x, y)
                
            self.last_x = x
            self.last_y = y
            
    def draw_line(self, x1, y1, x2, y2):
        self.layers[self.active_layer]['draw'].line(
            [x1, y1, x2, y2],
            fill=self.current_color,
            width=self.brush_size
        )
        self.update_canvas()
        
    def draw_brush(self, x, y):
        self.layers[self.active_layer]['draw'].ellipse(
            [x-self.brush_size, y-self.brush_size,
             x+self.brush_size, y+self.brush_size],
            fill=self.current_color
        )
        self.update_canvas()
        
    def spray(self, x, y):
        for _ in range(20):
            offset_x = np.random.normal(0, self.brush_size)
            offset_y = np.random.normal(0, self.brush_size)
            self.layers[self.active_layer]['draw'].point(
                (x + offset_x, y + offset_y),
                fill=self.current_color
            )
        self.update_canvas()
        
    def erase(self, x, y):
        self.layers[self.active_layer]['draw'].ellipse(
            [x-self.brush_size, y-self.brush_size,
             x+self.brush_size, y+self.brush_size],
            fill=(255, 255, 255, 0)
        )
        self.update_canvas()
        
    def stop_draw(self, event):
        self.drawing = False
        self.save_state()
        
    def update_canvas(self):
        # Combine all layers
        combined = Image.new('RGBA', (800, 600), (255, 255, 255, 255))
        for layer in self.layers:
            if layer['visible']:
                combined = Image.alpha_composite(combined, layer['image'])
                
        # Update canvas
        self.photo = ImageTk.PhotoImage(combined)
        self.canvas.create_image(0, 0, image=self.photo, anchor='nw')
        
        # Redraw grid if visible
        if self.grid_visible:
            self.draw_grid()
            
    def save_state(self):
        # Save current state for undo
        state = []
        for layer in self.layers:
            state.append(layer['image'].copy())
        self.undo_stack.append(state)
        self.redo_stack.clear()
        
    def undo(self):
        if self.undo_stack:
            state = self.undo_stack.pop()
            current_state = []
            for layer in self.layers:
                current_state.append(layer['image'].copy())
            self.redo_stack.append(current_state)
            
            for i, layer_image in enumerate(state):
                self.layers[i]['image'] = layer_image
                self.layers[i]['draw'] = ImageDraw.Draw(layer_image)
            self.update_canvas()
            
    def redo(self):
        if self.redo_stack:
            state = self.redo_stack.pop()
            current_state = []
            for layer in self.layers:
                current_state.append(layer['image'].copy())
            self.undo_stack.append(current_state)
            
            for i, layer_image in enumerate(state):
                self.layers[i]['image'] = layer_image
                self.layers[i]['draw'] = ImageDraw.Draw(layer_image)
            self.update_canvas()
            
    def clear_canvas(self):
        for layer in self.layers:
            layer['image'] = Image.new('RGBA', (800, 600), (255, 255, 255, 0))
            layer['draw'] = ImageDraw.Draw(layer['image'])
        self.update_canvas()
        self.save_state()
        
    def save_drawing(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if filename:
            # Combine all layers and save
            combined = Image.new('RGBA', (800, 600), (255, 255, 255, 255))
            for layer in self.layers:
                if layer['visible']:
                    combined = Image.alpha_composite(combined, layer['image'])
            combined.save(filename)

if __name__ == "__main__":
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()