import sys
import requests
import json
import threading
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QTextEdit, 
                             QPushButton, QComboBox, QProgressBar, QFrame,
                             QSplitter, QMessageBox, QScrollArea, QGroupBox)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QFont, QFontDatabase, QPalette, QColor, QIcon
import ollama

class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._default_color = QColor(45, 45, 45)
        self._hover_color = QColor(65, 65, 65)
        self._current_color = self._default_color
        
        self._animation = QPropertyAnimation(self, b"color")
        self._animation.setDuration(200)
        
        self.update_style()

    def enterEvent(self, event):
        self._animation.setStartValue(self._current_color)
        self._animation.setEndValue(self._hover_color)
        self._animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animation.setStartValue(self._current_color)
        self._animation.setEndValue(self._default_color)
        self._animation.start()
        super().leaveEvent(event)

    def get_color(self):
        return self._current_color

    def set_color(self, color):
        self._current_color = color
        self.update_style()

    def update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._current_color.name()};
                color: white;
                border: 1px solid #555;
                padding: 8px 16px;
                font-family: 'Courier New';
                font-weight: bold;
                min-height: 20px;
            }}
            QPushButton:disabled {{
                background-color: #333;
                color: #888;
                border: 1px solid #444;
            }}
        """)

    color = pyqtProperty(QColor, get_color, set_color)

class PhishingDetectorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_dark_mode = True
        self.is_analyzing = False
        self.available_models = []
        self.setup_ui()
        self.load_models()
        self.apply_dark_theme()

    def setup_ui(self):
        self.setWindowTitle("PHISHING URL DETECTOR")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        
        self.title_label = QLabel("PHISHING URL DETECTOR")
        self.title_label.setFont(QFont("Courier New", 18, QFont.Bold))
        
        self.theme_toggle = AnimatedButton("LIGHT MODE")
        self.theme_toggle.setFixedWidth(120)
        self.theme_toggle.clicked.connect(self.toggle_theme)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.theme_toggle)

        # Input section
        input_group = QGroupBox("ANALYSIS CONFIGURATION")
        input_group.setFont(QFont("Courier New", 10, QFont.Bold))
        input_layout = QVBoxLayout(input_group)

        # URL input
        url_layout = QVBoxLayout()
        url_label = QLabel("TARGET URL:")
        url_label.setFont(QFont("Courier New", 9, QFont.Bold))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        self.url_input.setFont(QFont("Courier New", 10))
        self.url_input.setText("https://")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)

        # Model selection
        model_layout = QVBoxLayout()
        model_label = QLabel("AI MODEL:")
        model_label.setFont(QFont("Courier New", 9, QFont.Bold))
        self.model_combo = QComboBox()
        self.model_combo.setFont(QFont("Courier New", 10))
        self.model_combo.setMinimumHeight(30)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)

        # Refresh models button
        refresh_layout = QHBoxLayout()
        self.refresh_btn = AnimatedButton("REFRESH MODELS")
        self.refresh_btn.setFixedHeight(35)
        self.refresh_btn.clicked.connect(self.load_models)
        refresh_layout.addWidget(self.refresh_btn)

        # Control buttons
        button_layout = QHBoxLayout()
        self.analyze_btn = AnimatedButton("INITIATE ANALYSIS")
        self.analyze_btn.setFixedHeight(40)
        self.analyze_btn.clicked.connect(self.analyze_url)

        self.clear_btn = AnimatedButton("CLEAR RESULTS")
        self.clear_btn.setFixedHeight(40)
        self.clear_btn.clicked.connect(self.clear_results)

        button_layout.addWidget(self.analyze_btn)
        button_layout.addWidget(self.clear_btn)

        input_layout.addLayout(url_layout)
        input_layout.addLayout(model_layout)
        input_layout.addLayout(refresh_layout)
        input_layout.addLayout(button_layout)

        # Progress section
        self.progress_group = QGroupBox("ANALYSIS STATUS")
        self.progress_group.setFont(QFont("Courier New", 10, QFont.Bold))
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(8)
        
        self.status_label = QLabel("READY")
        self.status_label.setFont(QFont("Courier New", 9))
        self.status_label.setAlignment(Qt.AlignCenter)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)

        # Results section
        results_group = QGroupBox("ANALYSIS RESULTS")
        results_group.setFont(QFont("Courier New", 10, QFont.Bold))
        results_layout = QVBoxLayout(results_group)

        self.results_text = QTextEdit()
        self.results_text.setFont(QFont("Courier New", 10))
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Analysis results will appear here...")
        results_layout.addWidget(self.results_text)

        # Assemble main layout
        main_layout.addWidget(header_frame)
        main_layout.addWidget(input_group)
        main_layout.addWidget(self.progress_group)
        main_layout.addWidget(results_group)

        # Set stretch factors
        main_layout.setStretchFactor(input_group, 0)
        main_layout.setStretchFactor(self.progress_group, 0)
        main_layout.setStretchFactor(results_group, 1)

    def load_models(self):
        """Load available Ollama models"""
        try:
            self.refresh_btn.setEnabled(False)
            self.status_label.setText("LOADING MODELS...")
            
            models_response = ollama.list()
            self.available_models = [model['name'] for model in models_response.get('models', [])]
            
            self.model_combo.clear()
            for model in self.available_models:
                self.model_combo.addItem(model)
                
            if self.available_models:
                self.status_label.setText(f"MODELS LOADED: {len(self.available_models)} AVAILABLE")
                QTimer.singleShot(2000, lambda: self.status_label.setText("READY"))
            else:
                self.status_label.setText("NO MODELS AVAILABLE")
                
        except Exception as e:
            self.status_label.setText(f"MODEL LOAD ERROR")
            QMessageBox.warning(self, "Model Load Error", 
                              f"Could not load Ollama models. Please ensure Ollama is running.\n\nError: {str(e)}")
        finally:
            self.refresh_btn.setEnabled(True)

    def toggle_theme(self):
        """Toggle between dark and light mode"""
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.apply_dark_theme()
            self.theme_toggle.setText("LIGHT MODE")
        else:
            self.apply_light_theme()
            self.theme_toggle.setText("DARK MODE")

    def apply_dark_theme(self):
        """Apply dark theme styling"""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(15, 15, 15))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(0, 122, 204))
        dark_palette.setColor(QPalette.Highlight, QColor(0, 122, 204))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        
        self.setPalette(dark_palette)
        self.apply_common_styles("#1a1a1a", "#333", "white", "#0a0a0a")

    def apply_light_theme(self):
        """Apply light theme styling"""
        light_palette = QPalette()
        light_palette.setColor(QPalette.Window, QColor(240, 240, 240))
        light_palette.setColor(QPalette.WindowText, Qt.black)
        light_palette.setColor(QPalette.Base, Qt.white)
        light_palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
        light_palette.setColor(QPalette.ToolTipBase, Qt.white)
        light_palette.setColor(QPalette.ToolTipText, Qt.black)
        light_palette.setColor(QPalette.Text, Qt.black)
        light_palette.setColor(QPalette.Button, QColor(220, 220, 220))
        light_palette.setColor(QPalette.ButtonText, Qt.black)
        light_palette.setColor(QPalette.BrightText, Qt.red)
        light_palette.setColor(QPalette.Link, QColor(0, 122, 204))
        light_palette.setColor(QPalette.Highlight, QColor(0, 122, 204))
        light_palette.setColor(QPalette.HighlightedText, Qt.white)
        
        self.setPalette(light_palette)
        self.apply_common_styles("#ffffff", "#ccc", "black", "#f0f0f0")

    def apply_common_styles(self, bg_color, border_color, text_color, group_bg):
        """Apply common styles for both themes"""
        common_style = f"""
            QMainWindow {{
                background-color: {self.palette().color(QPalette.Window).name()};
            }}
            QGroupBox {{
                background-color: {group_bg};
                border: 2px solid {border_color};
                border-radius: 4px;
                margin-top: 1ex;
                padding-top: 10px;
                color: {text_color};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {text_color};
            }}
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                padding: 5px;
                color: {text_color};
                font-family: 'Courier New';
                selection-background-color: #007acc;
            }}
            QProgressBar {{
                border: 1px solid {border_color};
                border-radius: 2px;
                text-align: center;
                background-color: {bg_color};
                color: {text_color};
            }}
            QProgressBar::chunk {{
                background-color: #007acc;
            }}
            QLabel {{
                color: {text_color};
                font-family: 'Courier New';
            }}
        """
        self.setStyleSheet(common_style)

    def validate_url(self, url):
        """Validate URL format"""
        if not url or url in ["https://", "http://"]:
            return False, "Please enter a valid URL"
        
        if not (url.startswith("http://") or url.startswith("https://")):
            return False, "URL must start with http:// or https://"
        
        if len(url) < 10:
            return False, "URL appears to be too short"
        
        return True, ""

    def analyze_url(self):
        """Start URL analysis"""
        if self.is_analyzing:
            return

        url = self.url_input.text().strip()
        model_name = self.model_combo.currentText()

        # Validate inputs
        is_valid, error_msg = self.validate_url(url)
        if not is_valid:
            QMessageBox.warning(self, "Invalid URL", error_msg)
            return

        if not model_name:
            QMessageBox.warning(self, "No Model", "Please select an AI model")
            return

        # Start analysis
        self.is_analyzing = True
        self.analyze_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("ANALYZING URL...")

        # Start analysis in thread
        thread = threading.Thread(target=self.perform_analysis, args=(url, model_name))
        thread.daemon = True
        thread.start()

    def perform_analysis(self, url, model_name):
        """Perform analysis in background thread"""
        try:
            # Update status
            self.update_status("FETCHING WEBSITE CONTENT...")
            
            # Fetch HTML content
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, timeout=15, headers=headers)
            response.raise_for_status()
            html_content = response.text[:3000]  # First 3000 characters

            self.update_status("ANALYZING WITH AI MODEL...")
            
            # Prepare analysis prompt
            prompt = f"""Analyze this URL for potential phishing threats:

URL: {url}

Website Content Preview:
{html_content}

Provide a comprehensive security analysis focusing on:
1. Domain reputation and SSL certificate
2. Suspicious patterns in content
3. Potential social engineering tactics
4. Technical security indicators
5. Overall risk assessment (Low/Medium/High/Critical)

Format the response with clear sections and specific findings."""

            # Get AI analysis
            response = ollama.generate(model=model_name, prompt=prompt)
            result = response.get('response', 'No analysis generated.')

            # Update UI with results
            self.show_results(url, result, True)

        except requests.exceptions.RequestException as e:
            error_msg = f"NETWORK ERROR: {str(e)}"
            self.show_results(url, error_msg, False)
        except ollama.ResponseError as e:
            error_msg = f"AI MODEL ERROR: {str(e)}"
            self.show_results(url, error_msg, False)
        except Exception as e:
            error_msg = f"UNEXPECTED ERROR: {str(e)}"
            self.show_results(url, error_msg, False)

    def update_status(self, message):
        """Update status label from thread"""
        QTimer.singleShot(0, lambda: self.status_label.setText(message))

    def show_results(self, url, result, success):
        """Display analysis results in main thread"""
        QTimer.singleShot(0, lambda: self._display_results(url, result, success))

    def _display_results(self, url, result, success):
        """Internal method to display results"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create formatted HTML result
        results_html = f"""
        <div style='font-family: "Courier New", monospace; font-size: 10pt;'>
            <div style='color: #007acc; font-weight: bold; border-bottom: 1px solid #555; padding-bottom: 5px;'>
                ANALYSIS REPORT - {timestamp}
            </div>
            <div style='margin: 10px 0; color: #888;'>
                TARGET: {url}
            </div>
            <div style='margin: 15px 0; padding: 10px; background-color: {'#1a3a1a' if success else '#3a1a1a'}; border-left: 3px solid {'#00cc00' if success else '#cc0000'};'>
                <strong>{'ANALYSIS COMPLETE' if success else 'ANALYSIS FAILED'}</strong>
            </div>
            <div style='margin-top: 15px; line-height: 1.4; white-space: pre-wrap;'>
                {self.format_result(result)}
            </div>
        </div>
        """
        
        self.results_text.setHtml(results_html)
        self.finish_analysis()

    def format_result(self, result):
        """Format the result text with proper HTML escaping"""
        import html
        formatted = html.escape(result)
        formatted = formatted.replace('\n', '<br>')
        
        # Add color coding for risk levels
        risk_patterns = {
            'LOW RISK': '<span style="color: #00cc00; font-weight: bold;">LOW RISK</span>',
            'MEDIUM RISK': '<span style="color: #cccc00; font-weight: bold;">MEDIUM RISK</span>',
            'HIGH RISK': '<span style="color: #cc6600; font-weight: bold;">HIGH RISK</span>',
            'CRITICAL RISK': '<span style="color: #cc0000; font-weight: bold;">CRITICAL RISK</span>',
            'SAFE': '<span style="color: #00cc00; font-weight: bold;">SAFE</span>',
            'SUSPICIOUS': '<span style="color: #cc6600; font-weight: bold;">SUSPICIOUS</span>',
            'DANGEROUS': '<span style="color: #cc0000; font-weight: bold;">DANGEROUS</span>',
            'PHISHING': '<span style="color: #cc0000; font-weight: bold;">PHISHING</span>',
            'LEGITIMATE': '<span style="color: #00cc00; font-weight: bold;">LEGITIMATE</span>'
        }
        
        for pattern, replacement in risk_patterns.items():
            formatted = formatted.replace(pattern, replacement)
            
        return formatted

    def finish_analysis(self):
        """Clean up after analysis completion"""
        self.is_analyzing = False
        self.analyze_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("ANALYSIS COMPLETE")
        QTimer.singleShot(3000, lambda: self.status_label.setText("READY"))

    def clear_results(self):
        """Clear the results display"""
        self.results_text.clear()
        self.status_label.setText("READY")

def main():
    app = QApplication(sys.argv)
    
    # Set application-wide font
    app.setFont(QFont("Courier New", 9))
    
    window = PhishingDetectorApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()