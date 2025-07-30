#!/usr/bin/env python3
"""
Voice Bridge v2.2.0 - Sistema Completo de Dictado Médico
=========================================================
Versión estable con todas las correcciones y mejoras
CARACTERÍSTICAS PRINCIPALES:
- Modo DICTATION para reconocimiento continuo
- Sistema anti-acoplamiento inteligente
- Modo oscuro/claro con UI mejorada
- Selector de tipo de micrófono
- Corrección médica contextual
- Detección de repeticiones
- Estadísticas en tiempo real
- Soporte multiidioma (ES/EN)
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font
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

        except (tk.TclError, AttributeError, Exception) as e:
            # Manejo específico de excepciones
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
                'title': 'Voice Bridge v2.2.0',
                'start': 'Start',
                'stop': 'Stop',
                'status': 'Status',
                'recognizing': 'Recognizing...',
                'ready': 'Ready',
                'config': 'Settings',
                'save_session': 'Save',
                'clear': 'Clear',
                'medical_corrections': 'Medical Corrections',
                'repetitions': 'Repetitions Detected',
                'stats': 'Session Statistics'
            },
            'es': {
                'title': 'Voice Bridge v2.2.0',
                'start': 'Iniciar',
                'stop': 'Detener',
                'status': 'Estado',
                'recognizing': 'Reconociendo...',
                'ready': 'Listo',
                'config': 'Configuración',
                'save_session': 'Guardar',
                'clear': 'Limpiar',
                'medical_corrections': 'Correcciones Médicas',
                'repetitions': 'Repeticiones Detectadas',
                'stats': 'Estadísticas de Sesión'
            }
        }
        return texts[self.current_language]


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
        """Inicializar Voice Bridge v2.2.0"""
        self.setup_logging()
        self.logger.info("=== Voice Bridge v2.2.0 Iniciando ===")

        # Sistemas principales
        self.theme_system = ThemeSystem()
        self.medical_corrector = MedicalCorrector()
        self.repetition_detector = RepetitionDetector()
        self.stats_collector = StatsCollector()

        # Configuración
        self.config = self.load_config()
        self.load_ui_preferences()

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

        # Configurar Azure en thread separado para evitar bloqueos
        self.log_to_gui("⏳ Configurando Azure Speech...")
        threading.Thread(target=self.delayed_azure_setup, daemon=True).start()

        self.load_medical_terms()
        self.setup_hotkeys()

        # Información de sesión
        self.session_start = datetime.now()
        self.transcription_count = 0

        self.logger.info("✅ Voice Bridge v2.2.0 iniciado correctamente")

        # Iniciar loops
        self.start_update_loops()

    def delayed_azure_setup(self):
        """Configurar Azure con delay para evitar conflictos"""
        try:
            time.sleep(0.5)
            self.setup_azure()

            # Después de configurar Azure, conectar eventos de sesión
            if hasattr(self, 'speech_recognizer') and self.speech_recognizer:
                try:
                    self.speech_recognizer.session_started.connect(
                        lambda evt: self.logger.info("Sesión de Azure iniciada")
                    )
                    self.speech_recognizer.session_stopped.connect(
                        lambda evt: self.logger.info("Sesión de Azure detenida")
                    )
                    self.speech_recognizer.speech_start_detected.connect(
                        lambda evt: self.logger.info("Inicio de habla detectado")
                    )
                    self.speech_recognizer.speech_end_detected.connect(
                        lambda evt: self.logger.info("Fin de habla detectado")
                    )
                except Exception as e:
                    self.logger.info(f"No se pudieron conectar todos los eventos de sesión: {e}")

        except Exception as e:
            self.logger.error(f"Error en configuración diferida de Azure: {e}")
            self.log_to_gui(f"❌ Error configurando Azure: {e}")

    def setup_logging(self):
        """Configurar sistema de logging"""
        log_dir = Path.home() / "voice-bridge-claude" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"voice_bridge_v220_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Log versión del SDK mejorado
        try:
            import azure.cognitiveservices.speech as sdk
            if hasattr(sdk, '__version__'):
                self.logger.info(f"Azure Speech SDK versión: {sdk.__version__}")
            elif HAS_PKG_RESOURCES:
                try:
                    version = pkg_resources.get_distribution("azure-cognitiveservices-speech").version
                    self.logger.info(f"Azure Speech SDK versión: {version}")
                except Exception:
                    self.logger.info("Azure Speech SDK versión: No se pudo determinar")
            else:
                self.logger.info("Azure Speech SDK versión: pkg_resources no disponible")
        except Exception:
            self.logger.info("Azure Speech SDK versión: Error al determinar")

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

        # Configurar estilos
        style.configure('Title.TLabel',
                        background=colors['bg_main'],
                        foreground=colors['text_primary'])
        style.configure('Status.TFrame',
                        background=colors['bg_surface'],
                        relief='flat',
                        borderwidth=1)

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
                                     text=texts['ready'],
                                     font=fonts['body'],
                                     bg=colors['bg_surface'],
                                     fg=colors['text_secondary'])
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

    def setup_azure(self):
        """Configurar Azure Speech Services"""
        try:
            azure_key = self.config.get('azure_speech_key', '').strip()
            azure_region = self.config.get('azure_region', 'eastus').strip()

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

            # Configurar tipo de micrófono
            mic_type = self.config.get('microphone_type', 'ambient')
            if mic_type == 'close':
                self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
            else:
                self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

            # Configurar timeouts
            try:
                initial_silence = int(self.config.get('azure_initial_silence_ms', '10000'))
                end_silence = int(self.config.get('azure_end_silence_ms', '10000'))
                segmentation = int(self.config.get('azure_segmentation_ms', '6000'))

                self.speech_config.set_property(
                    speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
                    str(initial_silence)
                )
                self.speech_config.set_property(
                    speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs,
                    str(end_silence)
                )
                self.speech_config.set_property(
                    speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs,
                    str(segmentation)
                )
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Error configurando timeouts Azure: {e}")

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

        except Exception as e:
            self.azure_ready = False
            error_msg = f"❌ Error configurando Azure: {str(e)}"
            self.log_to_gui(error_msg)
            self.logger.error(f"Error configurando Azure Speech: {e}")

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
                lambda evt: self.log_to_gui("🎤 Sesión de reconocimiento iniciada")
            )

            self.speech_recognizer.session_stopped.connect(
                lambda evt: self.log_to_gui("⏹️ Sesión de reconocimiento detenida")
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
                self.log_to_gui(f"🔄 Repetición detectada (similar a: '{similar_phrase}')")

            # Actualizar estadísticas
            self.stats_collector.update(full_text, was_corrected, is_repetition)

            # Agregar a transcripción
            self.add_to_transcription(full_text)

            # Auto-enviar a Claude si está habilitado
            if self.config.get('auto_send_to_claude', 'false').lower() == 'true':
                threading.Thread(target=self.send_to_claude, args=(full_text,), daemon=True).start()

        except Exception as e:
            self.logger.error(f"Error procesando buffer médico: {e}")

    def toggle_recognition(self):
        """Alternar reconocimiento de voz"""
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

            # Procesar buffer pendiente
            if self.buffer_timer:
                self.buffer_timer.cancel()
                self.buffer_timer = None

            if self.medical_buffer:
                self.process_medical_buffer()

            self.log_to_gui("⏹️ Reconocimiento detenido")
            self.logger.info("Reconocimiento de voz detenido")

        except Exception as e:
            error_msg = f"❌ Error deteniendo reconocimiento: {str(e)}"
            self.log_to_gui(error_msg)
            self.logger.error(f"Error deteniendo reconocimiento: {e}")

    def reinitialize_recognizer(self):
        """Reinicializar el reconocedor de Azure"""
        try:
            self.logger.info("Reinicializando reconocedor Azure...")

            # Detener reconocimiento actual
            if self.speech_recognizer and self.is_listening:
                self.speech_recognizer.stop_continuous_recognition_async()
                time.sleep(0.5)

            # Reconfigurar Azure
            self.setup_azure()

            self.log_to_gui("🔄 Reconocedor reinicializado")

        except Exception as e:
            self.logger.error(f"Error reinicializando reconocedor: {e}")
            self.log_to_gui(f"❌ Error reinicializando: {e}")

    def pause_recognition(self):
        """Pausar reconocimiento temporalmente"""
        self.recognition_paused = True
        self.log_to_gui("⏸️ Reconocimiento pausado")

    def resume_recognition(self):
        """Reanudar reconocimiento"""
        self.recognition_paused = False
        self.log_to_gui("▶️ Reconocimiento reanudado")

    def speak_text(self, text):
        """Sintetizar texto a voz usando Azure TTS"""
        if not self.config.get('tts_enabled', 'true').lower() == 'true':
            return

        if not self.speech_synthesizer:
            self.log_to_gui("❌ TTS no disponible")
            return

        def tts_worker():
            try:
                self.is_speaking = True
                self.recognition_paused_for_tts = True

                # Pausar reconocimiento durante TTS
                if self.is_listening:
                    self.pause_recognition()

                # Sintetizar
                result = self.speech_synthesizer.speak_text_async(text).get()

                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    self.log_to_gui(f"🔊 TTS: {text[:50]}...")
                else:
                    self.log_to_gui(f"❌ Error TTS: {result.reason}")

            except Exception as e:
                self.log_to_gui(f"❌ Error en TTS: {e}")
            finally:
                self.is_speaking = False
                self.recognition_paused_for_tts = False

                # Reanudar reconocimiento
                if self.is_listening:
                    self.resume_recognition()

        threading.Thread(target=tts_worker, daemon=True).start()

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
                self.status_label.configure(
                    text=texts['ready'],
                    fg=colors['text_secondary']
                )

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

    def update_partial_text(self, text):
        """Actualizar texto parcial en la interfaz"""
        if self.recognition_paused or self.recognition_paused_for_tts:
            return

        try:
            # Actualizar en la interfaz con formato especial para texto parcial
            self.transcriptions_text.configure(state=tk.NORMAL)

            # Eliminar línea parcial anterior si existe
            current_content = self.transcriptions_text.get("1.0", tk.END)
            lines = current_content.split('\n')

            if lines and lines[-2].startswith("[Parcial] "):
                self.transcriptions_text.delete(f"{len(lines) - 1}.0", tk.END)

            # Agregar nuevo texto parcial
            timestamp = datetime.now().strftime("%H:%M:%S")
            partial_line = f"[Parcial] {timestamp}: {text}\n"
            self.transcriptions_text.insert(tk.END, partial_line)
            self.transcriptions_text.see(tk.END)
            self.transcriptions_text.configure(state=tk.DISABLED)

        except Exception as e:
            self.logger.error(f"Error actualizando texto parcial: {e}")

    def add_to_transcription(self, text):
        """Agregar texto a la transcripción"""
        if not text or not text.strip():
            return

        try:
            self.transcriptions_text.configure(state=tk.NORMAL)

            # Eliminar línea parcial si existe
            current_content = self.transcriptions_text.get("1.0", tk.END)
            lines = current_content.split('\n')

            if lines and len(lines) > 1 and lines[-2].startswith("[Parcial] "):
                self.transcriptions_text.delete(f"{len(lines) - 1}.0", tk.END)

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

    def send_to_claude(self, text):
        """Enviar texto a Claude (simulado)"""
        try:
            delay = float(self.config.get('claude_activation_delay', '0.5'))
            time.sleep(delay)

            # Simular envío a Claude
            pyautogui.typewrite(text)
            pyautogui.press('enter')

            self.log_to_gui(f"📤 Enviado a Claude: {text[:50]}...")
            self.stats_collector.update("", command=True)

        except Exception as e:
            self.log_to_gui(f"❌ Error enviando a Claude: {e}")

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
=== SESIÓN VOICE BRIDGE v2.2.0 ===
Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Duración: {datetime.now() - self.session_start}
Frases totales: {stats['total_phrases']}
Palabras totales: {stats['total_words']}
Caracteres totales: {stats['total_characters']}
Correcciones aplicadas: {stats['corrections_applied']}
Repeticiones detectadas: {stats['repetitions_detected']}
Comandos ejecutados: {stats['commands_executed']}

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

    def open_config(self):
        """Abrir ventana de configuración"""
        ConfigWindow(self)

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

                    if msg_type == 'partial':
                        self.update_partial_text(text)
                    elif msg_type == 'final' and text.strip():
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
            self.logger.info("Cerrando Voice Bridge v2.2.0...")

            # Detener reconocimiento
            if self.is_listening:
                self.stop_recognition()

            # Procesar buffer pendiente
            if self.medical_buffer:
                self.process_medical_buffer()

            # Detener hotkeys
            if hasattr(self, 'hotkey_listener'):
                self.hotkey_listener.stop()

            # Limpiar Azure
            if self.speech_recognizer:
                try:
                    self.speech_recognizer.stop_continuous_recognition_async()
                except:
                    pass

            # Guardar configuración final
            config_file = Path.home() / "voice-bridge-claude" / "config" / "voice_bridge_config.ini"
            config = configparser.ConfigParser()
            config['DEFAULT'] = dict(self.config)

            with open(config_file, 'w') as f:
                config.write(f)

            self.logger.info("Voice Bridge v2.2.0 cerrado correctamente")

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


class ConfigWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("Configuración Voice Bridge")
        self.window.geometry("600x500")
        self.window.transient(parent.root)
        self.window.grab_set()

        self.create_interface()

    def create_interface(self):
        """Crear interfaz de configuración"""
        colors = self.parent.theme_system.get_theme()
        fonts = self.parent.theme_system.get_fonts()

        # Notebook para pestañas
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Pestañas
        self.create_general_tab(notebook)
        self.create_azure_tab(notebook)
        self.create_ui_tab(notebook)

        # Botones
        button_frame = tk.Frame(self.window, bg=colors['bg_main'])
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        save_btn = tk.Button(button_frame,
                             text="Guardar",
                             font=fonts['button'],
                             bg=colors['success'],
                             fg='white',
                             command=self.save_config)
        save_btn.pack(side=tk.RIGHT, padx=5)

        cancel_btn = tk.Button(button_frame,
                               text="Cancelar",
                               font=fonts['button'],
                               bg=colors['text_secondary'],
                               fg='white',
                               command=self.window.destroy)
        cancel_btn.pack(side=tk.RIGHT)

    def create_general_tab(self, notebook):
        """Crear pestaña general"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="General")

        # Variables
        self.auto_send_var = tk.BooleanVar(
            value=self.parent.config.get('auto_send_to_claude', 'false').lower() == 'true')
        self.tts_enabled_var = tk.BooleanVar(value=self.parent.config.get('tts_enabled', 'true').lower() == 'true')
        self.auto_correct_var = tk.BooleanVar(
            value=self.parent.config.get('auto_correct_medical', 'true').lower() == 'true')
        self.mic_type_var = tk.StringVar(value=self.parent.config.get('microphone_type', 'ambient'))
        self.pause_var = tk.StringVar(value=self.parent.config.get('medical_pause_seconds', '6'))

        # Controles
        row = 0

        ttk.Checkbutton(frame, text="Auto-enviar a Claude", variable=self.auto_send_var).grid(row=row, column=0,
                                                                                              sticky='w', padx=10,
                                                                                              pady=5)
        row += 1

        ttk.Checkbutton(frame, text="TTS habilitado", variable=self.tts_enabled_var).grid(row=row, column=0, sticky='w',
                                                                                          padx=10, pady=5)
        row += 1

        ttk.Checkbutton(frame, text="Corrección médica automática", variable=self.auto_correct_var).grid(row=row,
                                                                                                         column=0,
                                                                                                         sticky='w',
                                                                                                         padx=10,
                                                                                                         pady=5)
        row += 1

        ttk.Label(frame, text="Tipo de micrófono:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        mic_combo = ttk.Combobox(frame, textvariable=self.mic_type_var, values=['ambient', 'close'])
        mic_combo.grid(row=row, column=1, sticky='ew', padx=10, pady=5)
        row += 1

        ttk.Label(frame, text="Pausa médica (segundos):").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.pause_scale = tk.Scale(frame, from_=1, to=15, orient=tk.HORIZONTAL, variable=self.pause_var)
        self.pause_scale.grid(row=row, column=1, sticky='ew', padx=10, pady=5)

        self.pause_label = ttk.Label(frame, text=f"Actual: {self.pause_var.get()}s")
        self.pause_label.grid(row=row + 1, column=1, sticky='w', padx=10)

    def create_azure_tab(self, notebook):
        """Crear pestaña Azure"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Azure")

        # Variables Azure
        self.region_var = tk.StringVar(value=self.parent.config.get('azure_region', 'eastus'))

        row = 0

        ttk.Label(frame, text="Región de Azure:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        region_combo = ttk.Combobox(frame, textvariable=self.region_var,
                                    values=['eastus', 'westus', 'westeurope', 'eastasia'])
        region_combo.grid(row=row, column=1, sticky='ew', padx=10, pady=5)

    def create_ui_tab(self, notebook):
        """Crear pestaña UI"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Interfaz")

        # Variables UI
        self.theme_var = tk.StringVar(value=self.parent.theme_system.current_theme)
        self.lang_var = tk.StringVar(value=self.parent.theme_system.current_language)

        row = 0

        ttk.Label(frame, text="Tema:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        theme_combo = ttk.Combobox(frame, textvariable=self.theme_var, values=['light', 'dark'])
        theme_combo.grid(row=row, column=1, sticky='ew', padx=10, pady=5)
        row += 1

        ttk.Label(frame, text="Idioma:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        lang_combo = ttk.Combobox(frame, textvariable=self.lang_var, values=['en', 'es'])
        lang_combo.grid(row=row, column=1, sticky='ew', padx=10, pady=5)

    def save_config(self):
        """Guardar configuración"""
        try:
            # Actualizar configuración
            self.parent.config['auto_send_to_claude'] = str(self.auto_send_var.get()).lower()
            self.parent.config['tts_enabled'] = str(self.tts_enabled_var.get()).lower()
            self.parent.config['auto_correct_medical'] = str(self.auto_correct_var.get()).lower()
            self.parent.config['microphone_type'] = self.mic_type_var.get()
            self.parent.config['medical_pause_seconds'] = str(self.pause_var.get())
            self.parent.config['azure_region'] = self.region_var.get()
            self.parent.config['ui_theme'] = self.theme_var.get()
            self.parent.config['ui_language'] = self.lang_var.get()

            # Actualizar pausa médica
            try:
                self.parent.medical_pause_seconds = float(self.pause_var.get())
            except (ValueError, TypeError):
                self.parent.medical_pause_seconds = 6.0

            # Actualizar tema
            self.parent.theme_system.current_theme = self.theme_var.get()
            self.parent.theme_system.current_language = self.lang_var.get()

            # Guardar a archivo
            config_file = Path.home() / "voice-bridge-claude" / "config" / "voice_bridge_config.ini"
            config = configparser.ConfigParser()
            config['DEFAULT'] = dict(self.parent.config)

            with open(config_file, 'w') as f:
                config.write(f)

            self.parent.log_to_gui("⚙️ Configuración guardada")

            # Aplicar cambios inmediatos
            self.parent.apply_theme()

            # Cerrar ventana
            self.window.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Error guardando configuración: {e}")


def main():
    """Función principal"""
    try:
        app = VoiceBridge220()
        app.run()
    except Exception as e:
        print(f"Error crítico: {e}")
        logging.error(f"Error crítico en main: {e}")


if __name__ == "__main__":
    main()