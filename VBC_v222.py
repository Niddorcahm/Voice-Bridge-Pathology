#!/usr/bin/env python3
"""
Voice Bridge v2.2.1 - Sistema Completo de Dictado Médico con Configuración Azure
===============================================================================
Versión mejorada con configuración automática de Azure Speech
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font, simpledialog
import azure.cognitiveservices.speech as speechsdk
import pyautogui
import pynput.keyboard as keyboard
import threading
import queue
import time
import os
import json
import logging
import configparser
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import platform
import gc
import re
from collections import deque, Counter
from difflib import SequenceMatcher

# Manejo mejorado de pkg_resources
try:
    import pkg_resources

    HAS_PKG_RESOURCES = True
except ImportError:
    HAS_PKG_RESOURCES = False

# Configurar pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


class AzureConfigDialog:
    """Diálogo para configurar Azure Speech"""

    def __init__(self, parent=None):
        self.result = None
        self.setup_dialog(parent)

    def setup_dialog(self, parent):
        """Configurar diálogo"""
        self.dialog = tk.Toplevel(parent) if parent else tk.Tk()
        self.dialog.title("Configuración Azure Speech")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)

        if parent:
            self.dialog.transient(parent)
            self.dialog.grab_set()

        # Centrar ventana
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")

        self.create_interface()

    def create_interface(self):
        """Crear interfaz del diálogo"""
        # Frame principal
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        title_label = tk.Label(main_frame,
                               text="🎤 Configuración Azure Speech",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))

        # Información
        info_text = """Para usar Voice Bridge necesitas configurar Azure Speech Services:

1. Crea una cuenta en Azure Portal (azure.microsoft.com)
2. Busca "Speech Services" y crea un recurso
3. Copia la clave (Key) y región (Region)
4. Ingresa los datos a continuación:"""

        info_label = tk.Label(main_frame, text=info_text, justify=tk.LEFT, wraplength=450)
        info_label.pack(pady=(0, 20))

        # Campos de entrada
        fields_frame = tk.Frame(main_frame)
        fields_frame.pack(fill=tk.X, pady=(0, 20))

        # Azure Key
        tk.Label(fields_frame, text="Azure Speech Key:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.key_entry = tk.Entry(fields_frame, width=50, show="*")
        self.key_entry.pack(fill=tk.X, pady=(5, 15))

        # Azure Region
        tk.Label(fields_frame, text="Azure Region:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.region_var = tk.StringVar(value="eastus")
        region_combo = ttk.Combobox(fields_frame, textvariable=self.region_var, width=47)
        region_combo['values'] = ('eastus', 'westus', 'eastus2', 'westus2', 'westeurope',
                                  'northeurope', 'eastasia', 'southeastasia', 'japaneast',
                                  'australiaeast', 'centralus', 'southcentralus')
        region_combo.pack(fill=tk.X, pady=(5, 15))

        # Idioma
        tk.Label(fields_frame, text="Idioma de reconocimiento:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.lang_var = tk.StringVar(value="es-CO")
        lang_combo = ttk.Combobox(fields_frame, textvariable=self.lang_var, width=47)
        lang_combo['values'] = ('es-CO', 'es-ES', 'es-MX', 'es-AR', 'en-US', 'en-GB')
        lang_combo.pack(fill=tk.X, pady=(5, 15))

        # Botones
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)

        test_btn = tk.Button(buttons_frame, text="🧪 Probar Conexión",
                             command=self.test_connection, bg="#3498db", fg="white",
                             font=('Arial', 10), padx=15, pady=5)
        test_btn.pack(side=tk.LEFT, padx=(0, 10))

        save_btn = tk.Button(buttons_frame, text="💾 Guardar",
                             command=self.save_config, bg="#27ae60", fg="white",
                             font=('Arial', 10), padx=20, pady=5)
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))

        cancel_btn = tk.Button(buttons_frame, text="❌ Cancelar",
                               command=self.cancel, bg="#95a5a6", fg="white",
                               font=('Arial', 10), padx=15, pady=5)
        cancel_btn.pack(side=tk.RIGHT)

        # Status
        self.status_label = tk.Label(main_frame, text="", fg="blue")
        self.status_label.pack(pady=(10, 0))

    def test_connection(self):
        """Probar conexión con Azure"""
        key = self.key_entry.get().strip()
        region = self.region_var.get().strip()

        if not key or not region:
            self.status_label.config(text="❌ Por favor ingresa Key y Region", fg="red")
            return

        self.status_label.config(text="🔄 Probando conexión...", fg="blue")
        self.dialog.update()

        def test_worker():
            try:
                # Crear configuración de prueba
                speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
                speech_config.speech_recognition_language = self.lang_var.get()

                # Crear reconocedor de prueba
                recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

                # Test rápido
                result = recognizer.recognize_once_async().get()

                self.dialog.after(0, lambda: self.status_label.config(
                    text="✅ Conexión exitosa! Configuración válida", fg="green"))

            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "Forbidden" in error_msg:
                    msg = "❌ Key inválida o sin permisos"
                elif "InvalidServiceRegion" in error_msg:
                    msg = "❌ Región inválida"
                else:
                    msg = f"❌ Error: {error_msg[:50]}..."

                self.dialog.after(0, lambda: self.status_label.config(text=msg, fg="red"))

        threading.Thread(target=test_worker, daemon=True).start()

    def save_config(self):
        """Guardar configuración"""
        key = self.key_entry.get().strip()
        region = self.region_var.get().strip()
        language = self.lang_var.get()

        if not key or not region:
            self.status_label.config(text="❌ Por favor completa todos los campos", fg="red")
            return

        self.result = {
            'azure_speech_key': key,
            'azure_region': region,
            'speech_language': language
        }

        self.dialog.destroy()

    def cancel(self):
        """Cancelar configuración"""
        self.result = None
        self.dialog.destroy()

    def show(self):
        """Mostrar diálogo y retornar resultado"""
        self.dialog.wait_window()
        return self.result


class ThemeSystem:
    """Sistema de temas mejorado para UI médica"""

    def __init__(self):
        self.current_theme = 'light'
        self.current_language = 'en'
        self.detect_fonts()

    def detect_fonts(self):
        """Detectar mejores fuentes disponibles"""
        try:
            root_temp = tk.Tk()
            root_temp.withdraw()
            available = set(font.families())
            root_temp.destroy()

            # Jerarquía de fuentes preferidas
            font_preferences = ['Segoe UI', 'San Francisco', 'Ubuntu', 'DejaVu Sans', 'Arial']
            mono_preferences = ['Consolas', 'Monaco', 'Ubuntu Mono', 'DejaVu Sans Mono', 'Courier New']

            self.primary_font = next((f for f in font_preferences if f in available), 'Arial')
            self.mono_font = next((f for f in mono_preferences if f in available), 'Courier New')

        except (tk.TclError, AttributeError, Exception):
            self.primary_font = 'Arial'
            self.mono_font = 'Courier New'

    def get_theme(self):
        """Obtener colores del tema actual"""
        themes = {
            'light': {
                'bg_main': '#f5f5f5',
                'bg_surface': '#ffffff',
                'bg_surface_hover': '#f8f8f8',
                'text_primary': '#2c3e50',
                'text_secondary': '#7f8c8d',
                'text_muted': '#95a5a6',
                'primary': '#3498db',
                'primary_hover': '#2980b9',
                'success': '#27ae60',
                'warning': '#f39c12',
                'danger': '#e74c3c',
                'border': '#e0e0e0',
                'shadow': '#00000010'
            },
            'dark': {
                'bg_main': '#1a1a1a',
                'bg_surface': '#2d2d2d',
                'bg_surface_hover': '#3a3a3a',
                'text_primary': '#f0f0f0',
                'text_secondary': '#b0b0b0',
                'text_muted': '#808080',
                'primary': '#4a9eff',
                'primary_hover': '#357abd',
                'success': '#4caf50',
                'warning': '#ff9800',
                'danger': '#f44336',
                'border': '#404040',
                'shadow': '#00000040'
            }
        }
        return themes[self.current_theme]

    def get_fonts(self):
        """Obtener configuración de fuentes"""
        return {
            'title': (self.primary_font, 16, 'bold'),
            'heading': (self.primary_font, 12, 'bold'),
            'body': (self.primary_font, 10),
            'body_bold': (self.primary_font, 10, 'bold'),
            'mono': (self.mono_font, 10),
            'button': (self.primary_font, 10),
            'caption': (self.primary_font, 9)
        }

    def get_texts(self):
        """Obtener textos según idioma"""
        texts = {
            'en': {
                'title': 'Voice Bridge v2.2.1',
                'start': 'Start',
                'stop': 'Stop',
                'status': 'Status',
                'recognizing': 'Recognizing...',
                'ready': 'Ready',
                'not_configured': 'Azure not configured',
                'config': 'Settings',
                'save_session': 'Save',
                'clear': 'Clear',
                'medical_corrections': 'Medical Corrections',
                'repetitions': 'Repetitions Detected',
                'stats': 'Session Statistics'
            },
            'es': {
                'title': 'Voice Bridge v2.2.1',
                'start': 'Iniciar',
                'stop': 'Detener',
                'status': 'Estado',
                'recognizing': 'Reconociendo...',
                'ready': 'Listo',
                'not_configured': 'Azure no configurado',
                'config': 'Configuración',
                'save_session': 'Guardar',
                'clear': 'Limpiar',
                'medical_corrections': 'Correcciones Médicas',
                'repetitions': 'Repeticiones Detectadas',
                'stats': 'Estadísticas de Sesión'
            }
        }
        return texts[self.current_language]


# ... (resto de las clases MedicalCorrector, RepetitionDetector, StatsCollector igual que antes)

class MedicalCorrector:
    """Sistema de corrección médica contextual"""

    def __init__(self):
        self.corrections_applied = 0
        self.medical_terms = {}
        self.context_window = deque(maxlen=5)

    def load_terms(self, terms_dict):
        """Cargar diccionario de términos médicos"""
        self.medical_terms = terms_dict

    def correct_text(self, text):
        """Aplicar correcciones médicas contextuales"""
        original = text
        corrected = text

        # Aplicar correcciones del diccionario
        for incorrect, correct in self.medical_terms.items():
            pattern = re.compile(r'\b' + re.escape(incorrect) + r'\b', re.IGNORECASE)
            if pattern.search(corrected):
                corrected = pattern.sub(correct, corrected)

        # Actualizar contexto
        self.context_window.append(corrected)

        if corrected != original:
            self.corrections_applied += 1

        return corrected, (corrected != original)


class RepetitionDetector:
    """Detector avanzado de repeticiones"""

    def __init__(self):
        self.recent_phrases = deque(maxlen=10)
        self.repetitions_found = 0
        self.similarity_threshold = 0.85

    def is_repetition(self, text):
        """Detectar si el texto es una repetición"""
        if not text or len(text) < 5:
            return False, None

        # Verificar similitud con frases recientes
        for recent in self.recent_phrases:
            similarity = SequenceMatcher(None, text.lower(), recent.lower()).ratio()
            if similarity > self.similarity_threshold:
                self.repetitions_found += 1
                return True, recent

        self.recent_phrases.append(text)
        return False, None


class StatsCollector:
    """Recolector de estadísticas de sesión"""

    def __init__(self):
        self.session_start = datetime.now()
        self.stats = {
            'total_phrases': 0,
            'total_words': 0,
            'total_characters': 0,
            'corrections_applied': 0,
            'repetitions_detected': 0,
            'commands_executed': 0
        }

    def update(self, text, corrected=False, repetition=False, command=False):
        """Actualizar estadísticas"""
        if command:
            self.stats['commands_executed'] += 1
            return

        self.stats['total_phrases'] += 1
        self.stats['total_words'] += len(text.split())
        self.stats['total_characters'] += len(text)

        if corrected:
            self.stats['corrections_applied'] += 1
        if repetition:
            self.stats['repetitions_detected'] += 1


class VoiceBridge220:
    def __init__(self):
        """Inicializar Voice Bridge v2.2.1"""
        self.setup_logging()
        self.logger.info("=== Voice Bridge v2.2.1 Iniciando ===")

        # Sistemas principales
        self.theme_system = ThemeSystem()
        self.medical_corrector = MedicalCorrector()
        self.repetition_detector = RepetitionDetector()
        self.stats_collector = StatsCollector()

        # Configuración
        self.config = self.load_config()
        self.load_ui_preferences()

        # Verificar configuración Azure al inicio
        if not self.check_azure_config():
            if not self.configure_azure():
                print("❌ ERROR: AZURE_SPEECH_KEY no está configurado")
                print("Por favor configura la variable de entorno AZURE_SPEECH_KEY")
                return

        # Estado del sistema
        self.is_listening = False
        self.is_speaking = False
        self.recognition_paused = False
        self.recognition_paused_for_tts = False
        self.azure_ready = False
        self.medical_buffer = []
        self.last_activity_time = None
        self.buffer_timer = None

        # Timeouts configurables
        try:
            self.medical_pause_seconds = float(self.config.get('medical_pause_seconds', '6'))
            if self.medical_pause_seconds <= 0:
                self.medical_pause_seconds = 6.0
        except (ValueError, TypeError):
            self.logger.warning("Valor inválido para medical_pause_seconds, usando default")
            self.medical_pause_seconds = 6.0

        # Azure objects
        self.speech_config = None
        self.speech_recognizer = None
        self.speech_synthesizer = None
        self.audio_config = None

        # Colas
        self.transcription_queue = queue.Queue()

        # Setup componentes
        self.setup_gui()

        # Configurar Azure en thread separado
        self.log_to_gui("⏳ Configurando Azure Speech...")
        threading.Thread(target=self.delayed_azure_setup, daemon=True).start()

        self.load_medical_terms()
        self.setup_hotkeys()

        # Información de sesión
        self.session_start = datetime.now()
        self.transcription_count = 0

        self.logger.info("✅ Voice Bridge v2.2.1 iniciado correctamente")

        # Iniciar loops
        self.start_update_loops()

    def check_azure_config(self):
        """Verificar si Azure está configurado"""
        azure_key = self.config.get('azure_speech_key', '').strip()
        azure_region = self.config.get('azure_region', '').strip()

        # Verificar variables de entorno también
        env_key = os.environ.get('AZURE_SPEECH_KEY', '').strip()
        env_region = os.environ.get('AZURE_SPEECH_REGION', '').strip()

        return bool(azure_key or env_key) and bool(azure_region or env_region)

    def configure_azure(self):
        """Configurar Azure mediante diálogo"""
        try:
            dialog = AzureConfigDialog()
            config_data = dialog.show()

            if config_data:
                # Actualizar configuración
                self.config.update(config_data)

                # Guardar configuración
                config_file = Path.home() / "voice-bridge-claude" / "config" / "voice_bridge_config.ini"
                config_file.parent.mkdir(parents=True, exist_ok=True)

                config = configparser.ConfigParser()
                config['DEFAULT'] = dict(self.config)

                with open(config_file, 'w') as f:
                    config.write(f)

                return True

            return False

        except Exception as e:
            print(f"Error configurando Azure: {e}")
            return False

    # ... (resto de métodos igual que en la versión anterior, con las mejoras aplicadas)

    def setup_logging(self):
        """Configurar sistema de logging"""
        log_dir = Path.home() / "voice-bridge-claude" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"voice_bridge_v221_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self):
        """Cargar configuración"""
        config = configparser.ConfigParser()
        default_config = {
            # Azure
            'azure_speech_key': os.environ.get('AZURE_SPEECH_KEY', ''),
            'azure_region': os.environ.get('AZURE_SPEECH_REGION', 'eastus'),
            'speech_language': 'es-CO',
            'tts_voice': 'es-CO-SalomeNeural',
            # Funcionalidad
            'auto_send_to_claude': 'false',
            'tts_enabled': 'true',
            'auto_correct_medical': 'true',
            'medical_pause_seconds': '6',
            'microphone_type': 'ambient',
            # Timeouts Azure
            'azure_initial_silence_ms': '10000',
            'azure_end_silence_ms': '10000',
            'azure_segmentation_ms': '6000',
            # UI
            'ui_theme': 'light',
            'ui_language': 'en',
            # Avanzado
            'similarity_threshold': '0.85',
            'show_correction_details': 'true',
            'show_performance_stats': 'true',
            'claude_activation_delay': '0.5'
        }

        config_file = Path.home() / "voice-bridge-claude" / "config" / "voice_bridge_config.ini"

        if config_file.exists():
            config.read(config_file)
            # Actualizar con nuevos valores si no existen
            for key, value in default_config.items():
                if key not in config['DEFAULT']:
                    config['DEFAULT'][key] = value
        else:
            config['DEFAULT'] = default_config
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                config.write(f)

        return config['DEFAULT']

    def load_ui_preferences(self):
        """Cargar preferencias de UI"""
        self.theme_system.current_theme = self.config.get('ui_theme', 'light')
        self.theme_system.current_language = self.config.get('ui_language', 'en')

    def setup_gui(self):
        """Configurar interfaz gráfica mejorada"""
        self.root = tk.Tk()
        texts = self.theme_system.get_texts()
        self.root.title(texts['title'])

        # Configurar ventana
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Aplicar tema
        self.apply_theme()

        # Crear interfaz
        self.create_main_interface()

        # Configurar cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def apply_theme(self):
        """Aplicar tema a la ventana"""
        colors = self.theme_system.get_theme()
        self.root.configure(bg=colors['bg_main'])

        # Estilo ttk
        style = ttk.Style()
        style.theme_use('clam')

    def create_main_interface(self):
        """Crear interfaz principal completa"""
        colors = self.theme_system.get_theme()
        fonts = self.theme_system.get_fonts()
        texts = self.theme_system.get_texts()

        # Frame principal
        main_frame = tk.Frame(self.root, bg=colors['bg_main'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título
        title_label = tk.Label(main_frame,
                               text=texts['title'],
                               font=fonts['title'],
                               bg=colors['bg_main'],
                               fg=colors['text_primary'])
        title_label.pack(pady=(0, 20))

        # Panel de control
        control_frame = tk.Frame(main_frame, bg=colors['bg_surface'], relief=tk.FLAT, bd=1)
        control_frame.pack(fill=tk.X, pady=(0, 15))

        # Botones de control
        buttons_frame = tk.Frame(control_frame, bg=colors['bg_surface'])
        buttons_frame.pack(pady=10)

        self.start_button = tk.Button(buttons_frame,
                                      text=texts['start'],
                                      font=fonts['button'],
                                      bg=colors['primary'],
                                      fg='white',
                                      relief=tk.FLAT,
                                      padx=20,
                                      pady=8,
                                      command=self.toggle_recognition)
        self.start_button.pack(side=tk.LEFT, padx=5)

        config_button = tk.Button(buttons_frame,
                                  text=texts['config'],
                                  font=fonts['button'],
                                  bg=colors['text_secondary'],
                                  fg='white',
                                  relief=tk.FLAT,
                                  padx=20,
                                  pady=8,
                                  command=self.open_config)
        config_button.pack(side=tk.LEFT, padx=5)

        save_button = tk.Button(buttons_frame,
                                text=texts['save_session'],
                                font=fonts['button'],
                                bg=colors['success'],
                                fg='white',
                                relief=tk.FLAT,
                                padx=20,
                                pady=8,
                                command=self.save_session)
        save_button.pack(side=tk.LEFT, padx=5)

        clear_button = tk.Button(buttons_frame,
                                 text=texts['clear'],
                                 font=fonts['button'],
                                 bg=colors['warning'],
                                 fg='white',
                                 relief=tk.FLAT,
                                 padx=20,
                                 pady=8,
                                 command=self.clear_transcription)
        clear_button.pack(side=tk.LEFT, padx=5)

        # Estado
        status_frame = tk.Frame(control_frame, bg=colors['bg_surface'])
        status_frame.pack(pady=(0, 10))

        status_title = tk.Label(status_frame,
                                text=texts['status'] + ":",
                                font=fonts['body_bold'],
                                bg=colors['bg_surface'],
                                fg=colors['text_primary'])
        status_title.pack(side=tk.LEFT, padx=(10, 5))

        self.status_label = tk.Label(status_frame,
                                     text=texts['not_configured'] if not self.check_azure_config() else texts['ready'],
                                     font=fonts['body'],
                                     bg=colors['bg_surface'],
                                     fg=colors['danger'] if not self.check_azure_config() else colors['text_secondary'])
        self.status_label.pack(side=tk.LEFT)

        # Área de transcripción
        transcription_frame = tk.LabelFrame(main_frame,
                                            text="Transcripción",
                                            font=fonts['heading'],
                                            bg=colors['bg_main'],
                                            fg=colors['text_primary'])
        transcription_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.transcriptions_text = scrolledtext.ScrolledText(transcription_frame,
                                                             font=fonts['mono'],
                                                             bg=colors['bg_surface'],
                                                             fg=colors['text_primary'],
                                                             insertbackground=colors['text_primary'],
                                                             height=15,
                                                             wrap=tk.WORD)
        self.transcriptions_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Panel de estadísticas
        self.create_stats_panel(main_frame)

        # Área de log
        log_frame = tk.LabelFrame(main_frame,
                                  text="Sistema",
                                  font=fonts['caption'],
                                  bg=colors['bg_main'],
                                  fg=colors['text_primary'])
        log_frame.pack(fill=tk.X, pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                  height=6,
                                                  font=fonts['mono'],
                                                  bg=colors['bg_surface'],
                                                  fg=colors['text_secondary'],
                                                  insertbackground=colors['text_secondary'])
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_stats_panel(self, parent):
        """Crear panel de estadísticas"""
        colors = self.theme_system.get_theme()
        fonts = self.theme_system.get_fonts()
        texts = self.theme_system.get_texts()

        stats_frame = tk.LabelFrame(parent,
                                    text=texts['stats'],
                                    font=fonts['caption'],
                                    bg=colors['bg_main'],
                                    fg=colors['text_primary'])
        stats_frame.pack(fill=tk.X, pady=(0, 15))

        # Frame interno para estadísticas
        inner_frame = tk.Frame(stats_frame, bg=colors['bg_surface'])
        inner_frame.pack(fill=tk.X, padx=10, pady=5)

        # Estadísticas
        self.phrases_label = self.create_stat_widget(inner_frame, "Frases: 0", colors, fonts)
        self.phrases_label.pack(side=tk.LEFT, padx=5)

        self.corrections_label = self.create_stat_widget(inner_frame, texts['medical_corrections'] + ": 0", colors,
                                                         fonts)
        self.corrections_label.pack(side=tk.LEFT, padx=5)

        self.repetitions_label = self.create_stat_widget(inner_frame, texts['repetitions'] + ": 0", colors, fonts)
        self.repetitions_label.pack(side=tk.LEFT, padx=5)

    def create_stat_widget(self, parent, text, colors, fonts):
        """Crear widget de estadística"""
        frame = tk.Frame(parent,
                         bg=colors['bg_surface'],
                         relief=tk.FLAT,
                         bd=1)

        label = tk.Label(frame,
                         text=text,
                         font=fonts['caption'],
                         bg=colors['bg_surface'],
                         fg=colors['text_secondary'],
                         padx=8,
                         pady=4)
        label.pack()

        return label

    def delayed_azure_setup(self):
        """Configurar Azure con delay"""
        try:
            time.sleep(0.5)
            self.setup_azure()
        except Exception as e:
            self.logger.error(f"Error en configuración diferida de Azure: {e}")
            self.log_to_gui(f"❌ Error configurando Azure: {e}")

    def setup_azure(self):
        """Configurar Azure Speech Services mejorado"""
        try:
            # Obtener credenciales (primero config, luego variables de entorno)
            azure_key = self.config.get('azure_speech_key', '').strip()
            azure_region = self.config.get('azure_region', '').strip()

            if not azure_key:
                azure_key = os.environ.get('AZURE_SPEECH_KEY', '').strip()
            if not azure_region:
                azure_region = os.environ.get('AZURE_SPEECH_REGION', 'eastus').strip()

            if not azure_key:
                raise ValueError("Azure Speech Key no configurada")

            # Configuración de Azure Speech
            self.speech_config = speechsdk.SpeechConfig(
                subscription=azure_key,
                region=azure_region
            )

            # Configurar idioma
            speech_language = self.config.get('speech_language', 'es-CO')
            self.speech_config.speech_recognition_language = speech_language

            # Configurar para TTS
            tts_voice = self.config.get('tts_voice', 'es-CO-SalomeNeural')
            self.speech_config.speech_synthesis_voice_name = tts_voice

            # Configurar audio
            self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

            # Crear reconocedor
            self.speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=self.audio_config
            )

            # Crear sintetizador
            self.speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config
            )

            # Configurar callbacks
            self.setup_speech_callbacks()

            self.azure_ready = True
            self.log_to_gui("✅ Azure Speech configurado correctamente")
            self.logger.info("Azure Speech Services configurado correctamente")

            # Actualizar UI
            texts = self.theme_system.get_texts()
            colors = self.theme_system.get_theme()
            self.status_label.configure(text=texts['ready'], fg=colors['text_secondary'])

        except Exception as e:
            self.azure_ready = False
            error_msg = f"❌ Error configurando Azure: {str(e)}"
            self.log_to_gui(error_msg)
            self.logger.error(f"Error configurando Azure Speech: {e}")

            # Actualizar UI
            texts = self.theme_system.get_texts()
            colors = self.theme_system.get_theme()
            self.status_label.configure(text=texts['not_configured'], fg=colors['danger'])

    def setup_speech_callbacks(self):
        """Configurar callbacks de Azure Speech"""
        if not self.speech_recognizer:
            return

        try:
            # Resultado final
            self.speech_recognizer.recognized.connect(
                lambda evt: self.transcription_queue.put(('final', evt.result.text))
            )

            # Resultado parcial
            self.speech_recognizer.recognizing.connect(
                lambda evt: self.transcription_queue.put(('partial', evt.result.text))
            )

            # Eventos de sesión
            self.speech_recognizer.session_started.connect(
                lambda evt: self.log_to_gui("🎤 Sesión iniciada")
            )

            self.speech_recognizer.session_stopped.connect(
                lambda evt: self.log_to_gui("⏹️ Sesión detenida")
            )

            # Eventos de error
            self.speech_recognizer.canceled.connect(
                lambda evt: self.handle_recognition_error(evt)
            )

        except Exception as e:
            self.logger.error(f"Error configurando callbacks: {e}")

    def handle_recognition_error(self, evt):
        """Manejar errores de reconocimiento"""
        if evt.reason == speechsdk.CancellationReason.Error:
            error_msg = f"❌ Error de reconocimiento: {evt.error_details}"
            self.log_to_gui(error_msg)
            self.logger.error(error_msg)

    # ... (resto de métodos permanecen igual que en la versión anterior)

    def toggle_recognition(self):
        """Alternar reconocimiento de voz"""
        if not self.azure_ready:
            # Mostrar diálogo de configuración si Azure no está listo
            if not self.check_azure_config():
                config_data = AzureConfigDialog(self.root).show()
                if config_data:
                    self.config.update(config_data)
                    threading.Thread(target=self.delayed_azure_setup, daemon=True).start()
                    return
            else:
                self.log_to_gui("❌ Azure Speech no está listo, reiniciando...")
                threading.Thread(target=self.delayed_azure_setup, daemon=True).start()
                return

        if self.is_listening:
            self.stop_recognition()
        else:
            self.start_recognition()

    def start_recognition(self):
        """Iniciar reconocimiento de voz"""
        if not self.azure_ready:
            self.log_to_gui("❌ Azure Speech no está configurado")
            return

        try:
            if self.speech_recognizer:
                self.speech_recognizer.start_continuous_recognition_async()
                self.is_listening = True
                self.update_ui_state()
                self.log_to_gui("🎤 Reconocimiento iniciado")
                self.logger.info("Reconocimiento de voz iniciado")

        except Exception as e:
            error_msg = f"❌ Error iniciando reconocimiento: {str(e)}"
            self.log_to_gui(error_msg)
            self.logger.error(f"Error iniciando reconocimiento: {e}")

    def stop_recognition(self):
        """Detener reconocimiento de voz"""
        try:
            if self.speech_recognizer and self.is_listening:
                self.speech_recognizer.stop_continuous_recognition_async()

            self.is_listening = False
            self.update_ui_state()

            self.log_to_gui("⏹️ Reconocimiento detenido")
            self.logger.info("Reconocimiento de voz detenido")

        except Exception as e:
            error_msg = f"❌ Error deteniendo reconocimiento: {str(e)}"
            self.log_to_gui(error_msg)
            self.logger.error(f"Error deteniendo reconocimiento: {e}")

    def update_ui_state(self):
        """Actualizar estado de la interfaz"""
        try:
            colors = self.theme_system.get_theme()
            texts = self.theme_system.get_texts()

            if self.is_listening:
                self.start_button.configure(
                    text=texts['stop'],
                    bg=colors['danger']
                )
                self.status_label.configure(
                    text=texts['recognizing'],
                    fg=colors['success']
                )
            else:
                self.start_button.configure(
                    text=texts['start'],
                    bg=colors['primary']
                )
                status_text = texts['ready'] if self.azure_ready else texts['not_configured']
                status_color = colors['text_secondary'] if self.azure_ready else colors['danger']
                self.status_label.configure(text=status_text, fg=status_color)

            # Actualizar estadísticas
            stats = self.stats_collector.stats
            self.phrases_label.configure(text=f"Frases: {stats['total_phrases']}")
            self.corrections_label.configure(
                text=f"{self.theme_system.get_texts()['medical_corrections']}: {stats['corrections_applied']}"
            )
            self.repetitions_label.configure(
                text=f"{self.theme_system.get_texts()['repetitions']}: {stats['repetitions_detected']}"
            )

        except Exception as e:
            self.logger.error(f"Error actualizando UI: {e}")

    # ... (resto de métodos como process_medical_buffer, add_to_transcription, etc. permanecen igual)

    def log_to_gui(self, message):
        """Agregar mensaje al log de la interfaz"""
        try:
            if hasattr(self, 'log_text'):
                self.log_text.configure(state=tk.NORMAL)
                timestamp = datetime.now().strftime("%H:%M:%S")
                log_line = f"[{timestamp}] {message}\n"
                self.log_text.insert(tk.END, log_line)
                self.log_text.see(tk.END)
                self.log_text.configure(state=tk.DISABLED)
        except Exception as e:
            self.logger.error(f"Error en log GUI: {e}")

    def open_config(self):
        """Abrir configuración Azure si no está configurado"""
        if not self.check_azure_config():
            config_data = AzureConfigDialog(self.root).show()
            if config_data:
                self.config.update(config_data)
                # Guardar y reconfigurar
                config_file = Path.home() / "voice-bridge-claude" / "config" / "voice_bridge_config.ini"
                config = configparser.ConfigParser()
                config['DEFAULT'] = dict(self.config)
                with open(config_file, 'w') as f:
                    config.write(f)
                # Reconfigurar Azure
                threading.Thread(target=self.delayed_azure_setup, daemon=True).start()
        else:
            self.log_to_gui("⚙️ Azure ya está configurado")

    def process_medical_buffer(self):
        """Procesar buffer médico acumulado"""
        if not self.medical_buffer:
            return

        try:
            # Unir todo el buffer
            full_text = ' '.join(self.medical_buffer)
            self.medical_buffer.clear()

            # Aplicar correcciones médicas
            if self.config.get('auto_correct_medical', 'true').lower() == 'true':
                corrected_text, was_corrected = self.medical_corrector.correct_text(full_text)
                if was_corrected:
                    self.log_to_gui(f"🔧 Corrección aplicada: {full_text} → {corrected_text}")
                full_text = corrected_text
            else:
                was_corrected = False

            # Detectar repeticiones
            is_repetition, similar_phrase = self.repetition_detector.is_repetition(full_text)
            if is_repetition:
                self.log_to_gui(f"🔄 Repetición detectada")

            # Actualizar estadísticas
            self.stats_collector.update(full_text, was_corrected, is_repetition)

            # Agregar a transcripción
            self.add_to_transcription(full_text)

        except Exception as e:
            self.logger.error(f"Error procesando buffer médico: {e}")

    def add_to_transcription(self, text):
        """Agregar texto a la transcripción"""
        if not text or not text.strip():
            return

        try:
            self.transcriptions_text.configure(state=tk.NORMAL)

            # Agregar texto final
            timestamp = datetime.now().strftime("%H:%M:%S")
            final_line = f"[{timestamp}] {text.strip()}\n"
            self.transcriptions_text.insert(tk.END, final_line)
            self.transcriptions_text.see(tk.END)
            self.transcriptions_text.configure(state=tk.DISABLED)

            self.transcription_count += 1
            self.logger.info(f"Transcripción #{self.transcription_count}: {text}")

        except Exception as e:
            self.logger.error(f"Error agregando transcripción: {e}")

    def clear_transcription(self):
        """Limpiar área de transcripción"""
        try:
            self.transcriptions_text.configure(state=tk.NORMAL)
            self.transcriptions_text.delete("1.0", tk.END)
            self.transcriptions_text.configure(state=tk.DISABLED)
            self.log_to_gui("🗑️ Transcripción limpiada")
        except Exception as e:
            self.logger.error(f"Error limpiando transcripción: {e}")

    def save_session(self):
        """Guardar sesión actual"""
        try:
            # Crear directorio de sesiones
            sessions_dir = Path.home() / "voice-bridge-claude" / "sessions"
            sessions_dir.mkdir(parents=True, exist_ok=True)

            # Obtener contenido de transcripción
            content = self.transcriptions_text.get("1.0", tk.END)

            if not content.strip():
                self.log_to_gui("⚠️ No hay contenido para guardar")
                return

            # Crear archivo de sesión
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_file = sessions_dir / f"session_{timestamp}.txt"

            # Crear metadatos de sesión
            stats = self.stats_collector.stats
            session_info = f"""
=== SESIÓN VOICE BRIDGE v2.2.1 ===
Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Duración: {datetime.now() - self.session_start}
Frases totales: {stats['total_phrases']}
Palabras totales: {stats['total_words']}
Caracteres totales: {stats['total_characters']}
Correcciones aplicadas: {stats['corrections_applied']}
Repeticiones detectadas: {stats['repetitions_detected']}

=== TRANSCRIPCIÓN ===
{content}
"""

            # Guardar archivo
            with open(session_file, 'w', encoding='utf-8') as f:
                f.write(session_info)

            self.log_to_gui(f"💾 Sesión guardada: {session_file.name}")
            self.logger.info(f"Sesión guardada en: {session_file}")

        except Exception as e:
            error_msg = f"❌ Error guardando sesión: {e}"
            self.log_to_gui(error_msg)
            self.logger.error(f"Error guardando sesión: {e}")

    def load_medical_terms(self):
        """Cargar términos médicos desde archivo"""
        try:
            config_dir = Path.home() / "voice-bridge-claude" / "config"
            terms_file = config_dir / "medical_terms.json"

            if terms_file.exists():
                with open(terms_file, 'r', encoding='utf-8') as f:
                    terms = json.load(f)
                self.medical_corrector.load_terms(terms)
                self.log_to_gui(f"📚 {len(terms)} términos médicos cargados")
            else:
                # Crear archivo de términos por defecto
                default_terms = {
                    "dolor de cabesa": "dolor de cabeza",
                    "fiebre alta": "fiebre alta",
                    "presion arterial": "presión arterial",
                    "frecuencia cardiaca": "frecuencia cardíaca"
                }
                config_dir.mkdir(parents=True, exist_ok=True)
                with open(terms_file, 'w', encoding='utf-8') as f:
                    json.dump(default_terms, f, indent=2, ensure_ascii=False)
                self.medical_corrector.load_terms(default_terms)
                self.log_to_gui("📚 Términos médicos por defecto creados")

        except Exception as e:
            self.logger.error(f"Error cargando términos médicos: {e}")

    def setup_hotkeys(self):
        """Configurar atajos de teclado"""
        try:
            def on_hotkey():
                self.toggle_recognition()

            # Hotkey Ctrl+Shift+V para toggle
            self.hotkey_listener = keyboard.GlobalHotKeys({
                '<ctrl>+<shift>+v': on_hotkey
            })
            self.hotkey_listener.start()
            self.log_to_gui("⌨️ Hotkeys configurados (Ctrl+Shift+V)")

        except Exception as e:
            self.logger.error(f"Error configurando hotkeys: {e}")

    def start_update_loops(self):
        """Iniciar loops de actualización"""

        def transcription_loop():
            """Loop para procesar transcripciones"""
            while True:
                try:
                    msg_type, text = self.transcription_queue.get(timeout=0.1)

                    if msg_type == 'final' and text.strip():
                        # Agregar a buffer médico
                        self.medical_buffer.append(text.strip())
                        self.last_activity_time = time.time()

                        # Configurar timer para procesar buffer
                        if self.buffer_timer:
                            self.buffer_timer.cancel()

                        self.buffer_timer = threading.Timer(
                            self.medical_pause_seconds,
                            self.process_medical_buffer
                        )
                        self.buffer_timer.start()

                except queue.Empty:
                    pass
                except Exception as e:
                    self.logger.error(f"Error en transcription_loop: {e}")

        def ui_update_loop():
            """Loop para actualizar UI"""
            while True:
                try:
                    self.root.after(0, self.update_ui_state)
                    time.sleep(1)
                except Exception as e:
                    self.logger.error(f"Error en ui_update_loop: {e}")

        # Iniciar threads
        threading.Thread(target=transcription_loop, daemon=True).start()
        threading.Thread(target=ui_update_loop, daemon=True).start()

    def on_closing(self):
        """Manejar cierre de la aplicación"""
        try:
            self.logger.info("Cerrando Voice Bridge v2.2.1...")

            # Detener reconocimiento
            if self.is_listening:
                self.stop_recognition()

            # Procesar buffer pendiente
            if self.medical_buffer:
                self.process_medical_buffer()

            # Detener hotkeys
            if hasattr(self, 'hotkey_listener'):
                self.hotkey_listener.stop()

            self.logger.info("Voice Bridge v2.2.1 cerrado correctamente")

        except Exception as e:
            self.logger.error(f"Error cerrando aplicación: {e}")
        finally:
            self.root.destroy()

    def run(self):
        """Ejecutar la aplicación"""
        try:
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Error ejecutando aplicación: {e}")


def main():
    """Función principal"""
    try:
        app = VoiceBridge220()
        if hasattr(app, 'root'):  # Solo ejecutar si la GUI se creó correctamente
            app.run()
    except Exception as e:
        print(f"Error crítico: {e}")
        logging.error(f"Error crítico en main: {e}")


if __name__ == "__main__":
    main()