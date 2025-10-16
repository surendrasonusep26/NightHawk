import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import requests
import ollama
import threading

class PhishingDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Phishing URL Detector")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # macOS-inspired color scheme
        self.bg_color = "#f5f5f7"
        self.card_bg = "#ffffff"
        self.accent_color = "#007aff"
        self.text_color = "#1d1d1f"
        self.secondary_text = "#86868b"
        self.success_color = "#34c759"
        self.danger_color = "#ff3b30"
        
        self.root.configure(bg=self.bg_color)
        
        # Available models
        self.available_models = [
            "phishing-detector",
            "gpt-4",
            "gpt-3.5",
            "Maoyue/mistral-nemo-instruct-2407:latest"
        ]
        
        self.is_analyzing = False
        self.setup_ui()
        
    def setup_ui(self):
        # Main container with padding
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Header
        header_frame = tk.Frame(main_container, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            header_frame,
            text="🛡️ Phishing URL Detector",
            font=("SF Pro Display", 28, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        title_label.pack(anchor="w")
        
        subtitle_label = tk.Label(
            header_frame,
            text="Analyze URLs for potential phishing threats using AI",
            font=("SF Pro Text", 12),
            bg=self.bg_color,
            fg=self.secondary_text
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))
        
        # Input card
        input_card = tk.Frame(main_container, bg=self.card_bg, relief=tk.FLAT)
        input_card.pack(fill=tk.X, pady=(0, 20))
        self.add_shadow_effect(input_card)
        
        input_inner = tk.Frame(input_card, bg=self.card_bg)
        input_inner.pack(fill=tk.BOTH, padx=25, pady=25)
        
        # URL input section
        url_label = tk.Label(
            input_inner,
            text="URL to Analyze",
            font=("SF Pro Text", 13, "bold"),
            bg=self.card_bg,
            fg=self.text_color
        )
        url_label.pack(anchor="w", pady=(0, 8))
        
        # URL entry with modern styling
        url_frame = tk.Frame(input_inner, bg="#e8e8ed", relief=tk.FLAT)
        url_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.url_entry = tk.Entry(
            url_frame,
            font=("SF Pro Text", 12),
            bg="#e8e8ed",
            fg=self.text_color,
            relief=tk.FLAT,
            insertbackground=self.accent_color
        )
        self.url_entry.pack(fill=tk.X, padx=12, pady=10)
        self.url_entry.insert(0, "https://")
        
        # Model selection section
        model_label = tk.Label(
            input_inner,
            text="AI Model",
            font=("SF Pro Text", 13, "bold"),
            bg=self.card_bg,
            fg=self.text_color
        )
        model_label.pack(anchor="w", pady=(0, 8))
        
        # Custom styled combobox
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Custom.TCombobox",
            fieldbackground="#e8e8ed",
            background=self.card_bg,
            borderwidth=0
        )
        
        self.model_var = tk.StringVar()
        self.model_dropdown = ttk.Combobox(
            input_inner,
            textvariable=self.model_var,
            values=self.available_models,
            state="readonly",
            font=("SF Pro Text", 12),
            style="Custom.TCombobox"
        )
        self.model_dropdown.pack(fill=tk.X, pady=(0, 20))
        if self.available_models:
            self.model_dropdown.current(0)
        
        # Analyze button
        self.analyze_button = tk.Button(
            input_inner,
            text="Analyze URL",
            font=("SF Pro Text", 13, "bold"),
            bg=self.accent_color,
            fg="white",
            activebackground="#0051d5",
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.analyze_url,
            padx=30,
            pady=12
        )
        self.analyze_button.pack(fill=tk.X)
        self.add_button_hover(self.analyze_button)
        
        # Progress indicator
        self.progress_frame = tk.Frame(input_inner, bg=self.card_bg)
        self.progress_label = tk.Label(
            self.progress_frame,
            text="Analyzing...",
            font=("SF Pro Text", 11),
            bg=self.card_bg,
            fg=self.secondary_text
        )
        self.progress_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            length=200
        )
        self.progress_bar.pack(side=tk.LEFT)
        
        # Results card
        results_card = tk.Frame(main_container, bg=self.card_bg, relief=tk.FLAT)
        results_card.pack(fill=tk.BOTH, expand=True)
        self.add_shadow_effect(results_card)
        
        results_inner = tk.Frame(results_card, bg=self.card_bg)
        results_inner.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
        
        results_header = tk.Frame(results_inner, bg=self.card_bg)
        results_header.pack(fill=tk.X, pady=(0, 12))
        
        results_label = tk.Label(
            results_header,
            text="Analysis Results",
            font=("SF Pro Text", 13, "bold"),
            bg=self.card_bg,
            fg=self.text_color
        )
        results_label.pack(side=tk.LEFT)
        
        # Clear button
        self.clear_button = tk.Button(
            results_header,
            text="Clear",
            font=("SF Pro Text", 11),
            bg=self.bg_color,
            fg=self.text_color,
            activebackground="#d1d1d6",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.clear_output,
            padx=15,
            pady=6
        )
        self.clear_button.pack(side=tk.RIGHT)
        self.add_button_hover(self.clear_button, hover_color="#d1d1d6")
        
        # Output text area with custom styling
        text_frame = tk.Frame(results_inner, bg="#e8e8ed", relief=tk.FLAT)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(
            text_frame,
            font=("SF Mono", 11),
            bg="#f9f9f9",
            fg=self.text_color,
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=15,
            pady=15,
            insertbackground=self.accent_color
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Initial placeholder text
        placeholder = "Analysis results will appear here...\n\n"
        placeholder += "Enter a URL and click 'Analyze URL' to begin."
        self.output_text.insert(tk.END, placeholder)
        self.output_text.config(state=tk.DISABLED)
        
    def add_shadow_effect(self, widget):
        """Simulate shadow effect with border"""
        widget.config(
            highlightbackground="#d1d1d6",
            highlightcolor="#d1d1d6",
            highlightthickness=1,
            borderwidth=0
        )
        
    def add_button_hover(self, button, hover_color=None):
        """Add hover effect to buttons"""
        original_color = button.cget("background")
        if hover_color is None:
            hover_color = "#0051d5" if original_color == self.accent_color else "#d1d1d6"
        
        def on_enter(e):
            button.config(background=hover_color)
        
        def on_leave(e):
            button.config(background=original_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def clear_output(self):
        """Clear the output text area"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        placeholder = "Analysis results cleared.\n\n"
        placeholder += "Enter a URL and click 'Analyze URL' to begin."
        self.output_text.insert(tk.END, placeholder)
        self.output_text.config(state=tk.DISABLED)
    
    def validate_url(self, url):
        """Validate URL format"""
        if not url or url == "https://" or url == "http://":
            return False, "Please enter a valid URL"
        
        if not (url.startswith("http://") or url.startswith("https://")):
            return False, "URL must start with http:// or https://"
        
        if len(url) < 10:
            return False, "URL appears to be too short"
        
        return True, ""
    
    def analyze_url(self):
        """Analyze the URL for phishing"""
        if self.is_analyzing:
            return
        
        url = self.url_entry.get().strip()
        model_name = self.model_var.get()
        
        # Validate inputs
        is_valid, error_msg = self.validate_url(url)
        if not is_valid:
            messagebox.showerror("Invalid URL", error_msg)
            return
        
        if not model_name:
            messagebox.showerror("No Model Selected", "Please select an AI model from the dropdown")
            return
        
        # Start analysis in separate thread
        self.is_analyzing = True
        self.analyze_button.config(state=tk.DISABLED, text="Analyzing...")
        self.progress_frame.pack(fill=tk.X, pady=(15, 0))
        self.progress_bar.start(10)
        
        thread = threading.Thread(target=self.perform_analysis, args=(url, model_name))
        thread.daemon = True
        thread.start()
    
    def perform_analysis(self, url, model_name):
        """Perform the actual analysis in background"""
        try:
            # Fetch HTML
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            html_code = response.text
            
            # Prepare prompt
            prompt = f"""Analyze this website for phishing indicators. Provide a detailed assessment.

URL: {url}

HTML Content (first 2000 characters):
{html_code[:2000]}

Please analyze:
1. Suspicious patterns or elements
2. Security concerns
3. Overall safety assessment
4. Recommendation (Safe/Suspicious/Dangerous)
"""
            
            # Call Ollama API
            ai_response = ollama.generate(model=model_name, prompt=prompt)
            result_text = ai_response.get('response', ai_response.get('text', 'No response received'))
            
            # Update UI in main thread
            self.root.after(0, self.display_result, result_text, True, url)
            
        except requests.exceptions.Timeout:
            self.root.after(0, self.display_result, "Error: Request timed out. The server took too long to respond.", False, url)
        except requests.exceptions.ConnectionError:
            self.root.after(0, self.display_result, "Error: Could not connect to the URL. Check your internet connection or the URL.", False, url)
        except requests.exceptions.HTTPError as e:
            self.root.after(0, self.display_result, f"Error: HTTP {e.response.status_code} - {e.response.reason}", False, url)
        except ollama.ResponseError as e:
            self.root.after(0, self.display_result, f"Error: Ollama API error - {str(e)}", False, url)
        except Exception as e:
            self.root.after(0, self.display_result, f"Error: {str(e)}", False, url)
    
    def display_result(self, result, success, url):
        """Display the analysis result"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        
        # Header
        self.output_text.insert(tk.END, f"Analysis for: {url}\n", "url")
        self.output_text.insert(tk.END, "=" * 80 + "\n\n")
        
        if success:
            self.output_text.insert(tk.END, "✓ Analysis Complete\n\n", "success")
            self.output_text.insert(tk.END, result)
        else:
            self.output_text.insert(tk.END, "✗ Analysis Failed\n\n", "error")
            self.output_text.insert(tk.END, result)
        
        # Configure tags for styling
        self.output_text.tag_config("url", font=("SF Mono", 11, "bold"), foreground=self.accent_color)
        self.output_text.tag_config("success", foreground=self.success_color, font=("SF Pro Text", 12, "bold"))
        self.output_text.tag_config("error", foreground=self.danger_color, font=("SF Pro Text", 12, "bold"))
        
        self.output_text.config(state=tk.DISABLED)
        
        # Reset UI
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        self.analyze_button.config(state=tk.NORMAL, text="Analyze URL")
        self.is_analyzing = False


# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = PhishingDetectorApp(root)
    root.mainloop()