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
try:
    import pkg_resources
except ImportError:
    pkg_resources = None

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
            
        except:
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
        self.azure_ready = False  # Flag para indicar si Azure está listo
        self.medical_buffer = []
        self.last_activity_time = None
        self.buffer_timer = None
        
        # Timeouts configurables
        self.medical_pause_seconds = float(self.config.get('medical_pause_seconds', '6'))
        
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
            time.sleep(0.5)  # Pequeño delay para que la UI esté lista
            self.setup_azure()
            
            # Después de configurar Azure, conectar eventos de sesión
            if hasattr(self, 'speech_recognizer') and self.speech_recognizer:
                try:
                    # Conectar eventos de sesión para v1.45
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
        
        # Log versión del SDK
        try:
            import azure.cognitiveservices.speech as sdk
            if hasattr(sdk, '__version__'):
                self.logger.info(f"Azure Speech SDK versión: {sdk.__version__}")
            else:
                # Para v1.45, intentar obtener versión de otra forma
                if pkg_resources:
                    version = pkg_resources.get_distribution("azure-cognitiveservices-speech").version
                    self.logger.info(f"Azure Speech SDK versión: {version}")
                else:
                    self.logger.info("Azure Speech SDK versión: 1.45 (confirmada)")
        except:
            self.logger.info("Azure Speech SDK versión: 1.45+ (no se pudo determinar exacta)")
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
        """Crear interfaz principal"""
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
        
        # Interior del panel
        control_inner = tk.Frame(control_frame, bg=colors['bg_surface'])
        control_inner.pack(fill=tk.X, padx=15, pady=15)
        
        # Botones principales
        button_frame = tk.Frame(control_inner, bg=colors['bg_surface'])
        button_frame.pack(side=tk.LEFT)
        
        # Botón Start/Stop
        self.start_button = tk.Button(button_frame,
                                     text=texts['start'],
                                     command=self.toggle_recognition,
                                     font=fonts['button'],
                                     bg=colors['primary'],
                                     fg='white',
                                     activebackground=colors['primary_hover'],
                                     activeforeground='white',
                                     relief=tk.FLAT,
                                     padx=30, pady=8,
                                     cursor='hand2')
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón Configuración
        config_button = tk.Button(button_frame,
                                 text=texts['config'],
                                 command=self.open_config,
                                 font=fonts['button'],
                                 bg=colors['bg_surface_hover'],
                                 fg=colors['text_primary'],
                                 relief=tk.FLAT,
                                 padx=20, pady=8,
                                 cursor='hand2')
        config_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón Guardar
        save_button = tk.Button(button_frame,
                               text=texts['save_session'],
                               command=self.save_session,
                               font=fonts['button'],
                               bg=colors['bg_surface_hover'],
                               fg=colors['text_primary'],
                               relief=tk.FLAT,
                               padx=20, pady=8,
                               cursor='hand2')
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón Limpiar
        clear_button = tk.Button(button_frame,
                                text=texts['clear'],
                                command=self.clear_transcription,
                                font=fonts['button'],
                                bg=colors['bg_surface_hover'],
                                fg=colors['text_primary'],
                                relief=tk.FLAT,
                                padx=20, pady=8,
                                cursor='hand2')
        clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón Reiniciar Azure (útil para errores)
        azure_button = tk.Button(button_frame,
                                text="🔄 Azure",
                                command=lambda: threading.Thread(target=self.reinitialize_recognizer, daemon=True).start(),
                                font=fonts['button'],
                                bg=colors['bg_surface_hover'],
                                fg=colors['text_primary'],
                                relief=tk.FLAT,
                                padx=15, pady=8,
                                cursor='hand2')
        azure_button.pack(side=tk.LEFT)
        
        # Estado
        status_frame = tk.Frame(control_inner, bg=colors['bg_surface'])
        status_frame.pack(side=tk.RIGHT)
        
        tk.Label(status_frame,
                text=texts['status'] + ":",
                font=fonts['body'],
                bg=colors['bg_surface'],
                fg=colors['text_secondary']).pack(side=tk.LEFT, padx=(0, 5))
        
        self.status_label = tk.Label(status_frame,
                                    text=texts['ready'],
                                    font=fonts['body_bold'],
                                    bg=colors['bg_surface'],
                                    fg=colors['success'])
        self.status_label.pack(side=tk.LEFT)
        
        # Área de transcripción
        transcript_frame = tk.Frame(main_frame, bg=colors['bg_surface'], relief=tk.FLAT, bd=1)
        transcript_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Texto de transcripción
        self.transcriptions_text = scrolledtext.ScrolledText(
            transcript_frame,
            wrap=tk.WORD,
            font=fonts['mono'],
            bg=colors['bg_surface'],
            fg=colors['text_primary'],
            insertbackground=colors['primary'],
            selectbackground=colors['primary'],
            selectforeground='white',
            relief=tk.FLAT,
            padx=15,
            pady=15
        )
        self.transcriptions_text.pack(fill=tk.BOTH, expand=True)
        
        # Panel de información
        info_frame = tk.Frame(main_frame, bg=colors['bg_surface'], relief=tk.FLAT, bd=1)
        info_frame.pack(fill=tk.X)
        
        info_inner = tk.Frame(info_frame, bg=colors['bg_surface'])
        info_inner.pack(fill=tk.X, padx=15, pady=10)
        
        # Estadísticas
        self.create_stats_panel(info_inner)
        
        # Log
        self.log_text = tk.Text(info_inner,
                               height=3,
                               font=fonts['caption'],
                               bg=colors['bg_surface'],
                               fg=colors['text_muted'],
                               relief=tk.FLAT,
                               wrap=tk.WORD)
        self.log_text.pack(fill=tk.X, pady=(10, 0))
    
    def create_stats_panel(self, parent):
        """Crear panel de estadísticas"""
        colors = self.theme_system.get_theme()
        fonts = self.theme_system.get_fonts()
        texts = self.theme_system.get_texts()
        
        stats_frame = tk.Frame(parent, bg=colors['bg_surface'])
        stats_frame.pack(fill=tk.X)
        
        # Columnas de estadísticas
        col1 = tk.Frame(stats_frame, bg=colors['bg_surface'])
        col1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        col2 = tk.Frame(stats_frame, bg=colors['bg_surface'])
        col2.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        col3 = tk.Frame(stats_frame, bg=colors['bg_surface'])
        col3.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Estadísticas
        self.phrases_label = self.create_stat_widget(col1, "📝 Frases:", "0")
        self.corrections_label = self.create_stat_widget(col2, "🏥 " + texts['medical_corrections'] + ":", "0")
        self.repetitions_label = self.create_stat_widget(col3, "🔁 " + texts['repetitions'] + ":", "0")
    
    def create_stat_widget(self, parent, label, value):
        """Crear widget de estadística"""
        colors = self.theme_system.get_theme()
        fonts = self.theme_system.get_fonts()
        
        frame = tk.Frame(parent, bg=colors['bg_surface'])
        frame.pack(anchor=tk.W, pady=2)
        
        tk.Label(frame,
                text=label,
                font=fonts['caption'],
                bg=colors['bg_surface'],
                fg=colors['text_secondary']).pack(side=tk.LEFT)
        
        value_label = tk.Label(frame,
                              text=value,
                              font=fonts['body_bold'],
                              bg=colors['bg_surface'],
                              fg=colors['text_primary'])
        value_label.pack(side=tk.LEFT, padx=(5, 0))
        
        return value_label

    def setup_azure(self):
        """Configurar Azure Speech Services"""
        self.azure_ready = False  # Marcar como no listo al inicio

        try:
            # Asegurar que no está escuchando
            self.is_listening = False

            # Limpiar instancias previas
            if hasattr(self, 'speech_recognizer') and self.speech_recognizer:
                try:
                    self.logger.info("Limpiando recognizer anterior...")
                    # No usar .wait() ya que puede causar problemas
                    self.speech_recognizer.stop_continuous_recognition_async()
                    time.sleep(0.5)  # Dar tiempo para limpiar
                    del self.speech_recognizer
                    self.speech_recognizer = None
                except Exception as e:
                    self.logger.warning(f"Error limpiando recognizer: {e}")

            if hasattr(self, 'speech_synthesizer') and self.speech_synthesizer:
                try:
                    del self.speech_synthesizer
                    self.speech_synthesizer = None
                except:
                    pass

            if hasattr(self, 'audio_config') and self.audio_config:
                try:
                    del self.audio_config
                    self.audio_config = None
                except:
                    pass

            if hasattr(self, 'speech_config') and self.speech_config:
                try:
                    del self.speech_config
                    self.speech_config = None
                except:
                    pass

            # Forzar recolección de basura
            gc.collect()
            time.sleep(0.5)

            speech_key = self.config['azure_speech_key']
            region = self.config['azure_region']

            if not speech_key:
                raise ValueError("AZURE_SPEECH_KEY no configurado")

            self.logger.info(f"Configurando Azure - Región: {region}")

            # Configuración básica
            self.speech_config = speechsdk.SpeechConfig(
                subscription=speech_key,
                region=region
            )

            # Configurar idioma y voz
            self.speech_config.speech_recognition_language = self.config['speech_language']
            self.speech_config.speech_synthesis_voice_name = self.config['tts_voice']

            # IMPORTANTE: Usar modo DICTATION para reconocimiento continuo
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_RecoMode,
                "DICTATION"
            )

            # Timeouts optimizados - usar solo propiedades disponibles
            try:
                self.speech_config.set_property(
                    speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
                    self.config.get('azure_initial_silence_ms', '10000')
                )
            except AttributeError:
                self.logger.warning("InitialSilenceTimeoutMs no disponible")

            try:
                # Esta propiedad podría llamarse diferente en versiones antiguas
                if hasattr(speechsdk.PropertyId, 'Speech_SegmentationSilenceTimeoutMs'):
                    self.speech_config.set_property(
                        speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs,
                        self.config.get('azure_segmentation_ms', '6000')
                    )
                elif hasattr(speechsdk.PropertyId, 'SpeechServiceConnection_EndSilenceTimeoutMs'):
                    # Usar EndSilenceTimeout como alternativa
                    self.speech_config.set_property(
                        speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs,
                        self.config.get('azure_segmentation_ms', '6000')
                    )
            except AttributeError:
                self.logger.warning("SegmentationSilenceTimeoutMs no disponible")

            try:
                self.speech_config.set_property(
                    speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs,
                    self.config.get('azure_end_silence_ms', '10000')
                )
            except AttributeError:
                self.logger.warning("EndSilenceTimeoutMs no disponible")

            # Configuraciones opcionales (solo si están disponibles)
            try:
                # Intentar habilitar puntuación automática
                if hasattr(speechsdk.PropertyId, 'SpeechServiceResponse_RequestPunctuationMode'):
                    self.speech_config.set_property(
                        speechsdk.PropertyId.SpeechServiceResponse_RequestPunctuationMode,
                        "Automatic"
                    )
                else:
                    self.logger.info("Puntuación automática no disponible en esta versión del SDK")
            except AttributeError:
                pass

            try:
                # Intentar mejorar reconocimiento continuo
                if hasattr(speechsdk.PropertyId, 'SpeechServiceConnection_LanguageIdMode'):
                    self.speech_config.set_property(
                        speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode,
                        "Continuous"
                    )
            except AttributeError:
                pass

            # Crear audio config y recognizer
            self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
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

            # Marcar Azure como listo
            self.azure_ready = True

            self.logger.info("✅ Azure configurado correctamente")
            self.log_to_gui("✅ Azure Speech configurado - Modo DICTATION")

        except Exception as e:  # ← AHORA SÍ ESTÁ EN EL LUGAR CORRECTO
            self.azure_ready = False
            self.logger.error(f"Error configurando Azure: {e}")
            self.log_to_gui(f"❌ Error configurando Azure: {e}")
            raise
    
    def setup_speech_callbacks(self):
        """Configurar callbacks de reconocimiento"""
        
        def on_recognized(evt):
            """Texto reconocido final"""
            try:
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    text = evt.result.text.strip()
                    if text and not self.recognition_paused and not self.recognition_paused_for_tts:
                        self.logger.info(f"Texto reconocido: '{text}'")
                        
                        # Actualizar tiempo de actividad
                        self.last_activity_time = datetime.now()
                        
                        # Agregar al buffer médico
                        self.medical_buffer.append(text)
                        
                        # Reiniciar timer para procesar buffer
                        if self.buffer_timer:
                            self.buffer_timer.cancel()
                        self.buffer_timer = threading.Timer(
                            self.medical_pause_seconds,
                            self.process_medical_buffer
                        )
                        self.buffer_timer.start()
                        
                        # Actualizar UI
                        self.update_partial_text(" ".join(self.medical_buffer))
            except Exception as e:
                self.logger.error(f"Error en on_recognized: {e}")
        
        def on_recognizing(evt):
            """Texto parcial durante reconocimiento"""
            if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
                text = evt.result.text.strip()
                if text and not self.recognition_paused and not self.recognition_paused_for_tts:
                    partial = " ".join(self.medical_buffer) + " " + text
                    self.update_partial_text(partial.strip())
        
        def on_error(evt):
            """Error en reconocimiento"""
            if evt.result.reason == speechsdk.ResultReason.Canceled:
                cancellation = evt.result.cancellation_details
                self.logger.error(f"Error de reconocimiento: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    self.log_to_gui(f"❌ Error: {cancellation.error_details}")
        
        # Conectar eventos
        self.speech_recognizer.recognized.connect(on_recognized)
        self.speech_recognizer.recognizing.connect(on_recognizing)
        self.speech_recognizer.canceled.connect(on_error)
    
    def process_medical_buffer(self):
        """Procesar buffer médico completo"""
        if not self.medical_buffer:
            return
        
        # Unir todo el buffer
        complete_text = " ".join(self.medical_buffer)
        self.medical_buffer.clear()
        
        # Aplicar correcciones si está habilitado
        if self.config.getboolean('auto_correct_medical'):
            corrected_text, was_corrected = self.medical_corrector.correct_text(complete_text)
        else:
            corrected_text = complete_text
            was_corrected = False
        
        # Detectar repeticiones
        is_repetition, similar_to = self.repetition_detector.is_repetition(corrected_text)
        
        if is_repetition:
            self.log_to_gui(f"🔁 Repetición detectada: similar a '{similar_to[:30]}...'")
        
        # Actualizar estadísticas
        self.stats_collector.update(corrected_text, was_corrected, is_repetition)
        
        # Agregar a transcripción
        if not is_repetition:
            self.add_to_transcription(corrected_text)
            if was_corrected:
                self.log_to_gui(f"🏥 Corrección aplicada: {complete_text[:30]}... → {corrected_text[:30]}...")
        
        # Limpiar texto parcial
        self.update_partial_text("")
        
        # Enviar a Claude si está configurado
        if self.config.getboolean('auto_send_to_claude') and not is_repetition:
            threading.Thread(target=self.send_to_claude, args=(corrected_text,), daemon=True).start()
    
    def toggle_recognition(self):
        """Alternar reconocimiento de voz"""
        # Verificar que Azure esté listo
        if not self.azure_ready:
            self.log_to_gui("⚠️ Azure aún no está listo, espere...")
            return
        
        if self.is_listening:
            self.stop_recognition()
        else:
            self.start_recognition()
    
    def start_recognition(self):
        """Iniciar reconocimiento"""
        try:
            # Verificar que el recognizer existe y está listo
            if not hasattr(self, 'speech_recognizer') or not self.speech_recognizer:
                self.logger.error("Speech recognizer no está inicializado")
                self.log_to_gui("❌ Error: Recognizer no inicializado")
                return
            
            # Si ya está escuchando, no hacer nada
            if self.is_listening:
                self.logger.warning("Ya está escuchando")
                return
            
            # Limpiar estado
            self.recognition_paused = False
            self.recognition_paused_for_tts = False
            self.medical_buffer.clear()
            
            # Iniciar reconocimiento
            self.logger.info("Iniciando reconocimiento continuo...")
            result = self.speech_recognizer.start_continuous_recognition_async()
            result.get(timeout=5)  # Timeout de 5 segundos
            
            self.is_listening = True
            self.update_ui_state()
            self.log_to_gui("🎤 Reconocimiento iniciado")
            self.logger.info("✅ Reconocimiento iniciado correctamente")
            
        except Exception as e:
            self.is_listening = False
            error_msg = str(e)
            
            if "0x13" in error_msg or "INVALID_STATE" in error_msg:
                # Error de estado - intentar reinicializar
                self.logger.error("Error de estado del recognizer - reinicializando")
                self.log_to_gui("⚠️ Reinicializando recognizer...")
                
                # Reinicializar en el thread principal
                self.root.after(100, lambda: threading.Thread(target=self.reinitialize_recognizer, daemon=True).start())
            elif "timeout" in error_msg.lower():
                self.logger.error("Timeout al iniciar reconocimiento")
                self.log_to_gui("❌ Timeout - intente de nuevo")
            else:
                self.logger.error(f"Error iniciando reconocimiento: {e}")
                self.log_to_gui(f"❌ Error: {e}")
    
    def stop_recognition(self):
        """Detener reconocimiento"""
        try:
            # Si no está escuchando, no hacer nada
            if not self.is_listening:
                return
            
            # Marcar como no escuchando inmediatamente
            self.is_listening = False
            
            # Procesar buffer pendiente
            if self.buffer_timer:
                self.buffer_timer.cancel()
                self.buffer_timer = None
            
            # Procesar cualquier texto pendiente
            if self.medical_buffer:
                self.process_medical_buffer()
            
            # Detener reconocimiento si el recognizer existe
            if hasattr(self, 'speech_recognizer') and self.speech_recognizer:
                self.logger.info("Deteniendo reconocimiento...")
                try:
                    result = self.speech_recognizer.stop_continuous_recognition_async()
                    result.get(timeout=5)  # Timeout de 5 segundos
                    self.logger.info("✅ Reconocimiento detenido correctamente")
                except Exception as e:
                    self.logger.warning(f"Advertencia al detener: {e}")
            
            self.update_ui_state()
            self.log_to_gui("🛑 Reconocimiento detenido")
            
        except Exception as e:
            self.is_listening = False
            self.logger.error(f"Error deteniendo reconocimiento: {e}")
            self.log_to_gui(f"❌ Error al detener: {e}")
            # Actualizar UI de todos modos
            try:
                self.update_ui_state()
            except:
                pass
    
    def reinitialize_recognizer(self):
        """Reinicializar el recognizer en caso de error"""
        try:
            self.logger.info("Reinicializando Azure Speech...")
            self.log_to_gui("🔄 Reinicializando Azure...")
            
            # Marcar como no listo
            self.azure_ready = False
            self.is_listening = False
            
            # Esperar un momento
            time.sleep(1)
            
            # Reinicializar
            self.setup_azure()
            
            self.log_to_gui("✅ Azure reinicializado")
            
        except Exception as e:
            self.logger.error(f"Error reinicializando: {e}")
            self.log_to_gui(f"❌ Error reinicializando: {e}")
            self.azure_ready = False
    
    def pause_recognition(self):
        """Pausar reconocimiento temporalmente"""
        self.recognition_paused_for_tts = True
        self.logger.info("⏸️ Reconocimiento pausado para TTS")
    
    def resume_recognition(self):
        """Reanudar reconocimiento"""
        self.recognition_paused_for_tts = False
        self.logger.info("▶️ Reconocimiento reanudado")
    
    def speak_text(self, text):
        """TTS con anti-acoplamiento"""
        if not self.config.getboolean('tts_enabled'):
            return
        
        # Determinar si necesita anti-acoplamiento
        mic_type = self.config.get('microphone_type', 'ambient')
        needs_mute = mic_type in ['ambient', 'builtin', 'directional']
        
        self.logger.info(f"TTS: Micrófono '{mic_type}', anti-acoplamiento: {needs_mute}")
        
        def tts_thread():
            try:
                self.is_speaking = True
                was_listening = self.is_listening
                
                # Anti-acoplamiento si es necesario
                if needs_mute and was_listening:
                    # Pausar reconocimiento
                    self.pause_recognition()
                    
                    # Detener reconocimiento completamente
                    try:
                        self.speech_recognizer.stop_continuous_recognition_async().get()
                        self.is_listening = False
                        time.sleep(0.2)
                    except Exception as e:
                        self.logger.error(f"Error deteniendo para TTS: {e}")
                
                # Hablar
                result = self.speech_synthesizer.speak_text_async(text).get()
                
                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    self.logger.info("✅ TTS completado")
                    time.sleep(0.5)  # Esperar que termine el audio
                else:
                    self.logger.error(f"Error TTS: {result.reason}")
                
            except Exception as e:
                self.logger.error(f"Error en TTS: {e}")
            finally:
                self.is_speaking = False
                
                # Restaurar reconocimiento si estaba activo
                if needs_mute and was_listening:
                    try:
                        time.sleep(0.2)
                        self.speech_recognizer.start_continuous_recognition_async().get()
                        self.is_listening = True
                        self.resume_recognition()
                    except Exception as e:
                        self.logger.error(f"Error restaurando reconocimiento: {e}")
        
        # Ejecutar en thread separado
        threading.Thread(target=tts_thread, daemon=True).start()
    
    def update_ui_state(self):
        """Actualizar estado de la UI"""
        colors = self.theme_system.get_theme()
        texts = self.theme_system.get_texts()
        
        if self.is_listening:
            self.start_button.config(
                text=texts['stop'],
                bg=colors['danger'],
                activebackground=colors['danger']
            )
            self.status_label.config(
                text=texts['recognizing'],
                fg=colors['primary']
            )
        else:
            self.start_button.config(
                text=texts['start'],
                bg=colors['primary'],
                activebackground=colors['primary_hover']
            )
            self.status_label.config(
                text=texts['ready'],
                fg=colors['success']
            )
    
    def update_partial_text(self, text):
        """Actualizar texto parcial en UI"""
        def update():
            try:
                # Buscar marcador de texto parcial
                self.transcriptions_text.tag_delete("partial")
                
                if text:
                    # Agregar texto parcial en gris
                    end_pos = self.transcriptions_text.index(tk.END)
                    self.transcriptions_text.insert(tk.END, f"\n[{text}]", "partial")
                    self.transcriptions_text.tag_config("partial", 
                                                      foreground=self.theme_system.get_theme()['text_muted'])
                    self.transcriptions_text.see(tk.END)
            except:
                pass
        
        self.root.after_idle(update)
    
    def add_to_transcription(self, text):
        """Agregar texto a la transcripción"""
        def add():
            try:
                # Eliminar texto parcial si existe
                self.transcriptions_text.tag_delete("partial")
                
                # Agregar nueva transcripción
                timestamp = datetime.now().strftime("%H:%M:%S")
                colors = self.theme_system.get_theme()
                
                # Agregar timestamp
                self.transcriptions_text.insert(tk.END, f"\n[{timestamp}] ", "timestamp")
                self.transcriptions_text.tag_config("timestamp", 
                                                   foreground=colors['text_secondary'])
                
                # Agregar texto
                self.transcriptions_text.insert(tk.END, text)
                self.transcriptions_text.see(tk.END)
                
                self.transcription_count += 1
            except Exception as e:
                self.logger.error(f"Error agregando transcripción: {e}")
        
        self.root.after_idle(add)
    
    def send_to_claude(self, text):
        """Enviar texto a Claude"""
        try:
            # Buscar ventana de Claude
            claude_windows = pyautogui.getWindowsWithTitle('Claude')
            if not claude_windows:
                self.log_to_gui("⚠️ Ventana de Claude no encontrada")
                return
            
            # Activar ventana
            claude_window = claude_windows[0]
            claude_window.activate()
            time.sleep(float(self.config.get('claude_activation_delay', '0.5')))
            
            # Escribir texto
            pyautogui.write(text)
            time.sleep(0.1)
            
            # Enviar
            pyautogui.press('enter')
            
            # Volver a Voice Bridge
            voice_windows = pyautogui.getWindowsWithTitle('Voice Bridge')
            if voice_windows:
                voice_windows[0].activate()
            
            self.log_to_gui("✅ Enviado a Claude")
            
        except Exception as e:
            self.logger.error(f"Error enviando a Claude: {e}")
            self.log_to_gui(f"❌ Error enviando a Claude: {e}")
    
    def log_to_gui(self, message):
        """Agregar mensaje al log de la GUI"""
        def log():
            try:
                self.log_text.config(state=tk.NORMAL)
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(1.0, f"{datetime.now().strftime('%H:%M:%S')} - {message}")
                self.log_text.config(state=tk.DISABLED)
            except:
                pass
        
        self.root.after_idle(log)
    
    def clear_transcription(self):
        """Limpiar área de transcripción"""
        self.transcriptions_text.delete(1.0, tk.END)
        self.log_to_gui("📄 Transcripción limpiada")
    
    def save_session(self):
        """Guardar sesión de transcripción"""
        try:
            content = self.transcriptions_text.get(1.0, tk.END).strip()
            if not content:
                messagebox.showwarning("Aviso", "No hay contenido para guardar")
                return
            
            # Crear directorio
            save_dir = Path.home() / "voice-bridge-claude" / "sesiones"
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = save_dir / f"sesion_{timestamp}.txt"
            
            # Guardar con estadísticas
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"=== Voice Bridge v2.2.0 - Sesión ===\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Duración: {datetime.now() - self.session_start}\n")
                f.write(f"\n=== Estadísticas ===\n")
                f.write(f"Frases: {self.stats_collector.stats['total_phrases']}\n")
                f.write(f"Palabras: {self.stats_collector.stats['total_words']}\n")
                f.write(f"Correcciones: {self.stats_collector.stats['corrections_applied']}\n")
                f.write(f"Repeticiones: {self.stats_collector.stats['repetitions_detected']}\n")
                f.write(f"\n=== Transcripción ===\n")
                f.write(content)
            
            self.log_to_gui(f"💾 Sesión guardada: {filename.name}")
            messagebox.showinfo("Éxito", f"Sesión guardada en:\n{filename}")
            
        except Exception as e:
            self.logger.error(f"Error guardando sesión: {e}")
            messagebox.showerror("Error", f"Error al guardar: {e}")
    
    def load_medical_terms(self):
        """Cargar términos médicos"""
        terms_file = Path.home() / "voice-bridge-claude" / "config" / "medical_terms.json"
        
        if terms_file.exists():
            try:
                with open(terms_file, 'r', encoding='utf-8') as f:
                    terms = json.load(f)
                    self.medical_corrector.load_terms(terms)
                    self.logger.info(f"✅ {len(terms)} términos médicos cargados")
                    self.log_to_gui(f"🏥 {len(terms)} términos médicos cargados")
            except Exception as e:
                self.logger.error(f"Error cargando términos: {e}")
        else:
            # Crear archivo de ejemplo
            example_terms = {
                "hemoglobina": "hemoglobina",
                "emoglobina": "hemoglobina",
                "proteina": "proteína",
                "celula": "célula",
                "leucocito": "leucocito",
                "leukocito": "leucocito"
            }
            
            terms_file.parent.mkdir(parents=True, exist_ok=True)
            with open(terms_file, 'w', encoding='utf-8') as f:
                json.dump(example_terms, f, indent=2, ensure_ascii=False)
            
            self.medical_corrector.load_terms(example_terms)
            self.log_to_gui("🏥 Términos médicos de ejemplo creados")
    
    def open_config(self):
        """Abrir ventana de configuración"""
        ConfigWindow(self)
    
    def setup_hotkeys(self):
        """Configurar atajos de teclado"""
        def on_press(key):
            try:
                # Ctrl+Shift+V - Toggle reconocimiento
                if hasattr(key, 'char') and key.char == 'v':
                    if keyboard.Controller().pressed(keyboard.Key.ctrl) and \
                       keyboard.Controller().pressed(keyboard.Key.shift):
                        self.root.after_idle(self.toggle_recognition)
            except:
                pass
        
        # Iniciar listener en thread separado
        self.hotkey_listener = keyboard.Listener(on_press=on_press)
        self.hotkey_listener.start()
    
    def start_update_loops(self):
        """Iniciar loops de actualización"""
        def update_stats():
            """Actualizar estadísticas en UI"""
            try:
                stats = self.stats_collector.stats
                self.phrases_label.config(text=str(stats['total_phrases']))
                self.corrections_label.config(text=str(stats['corrections_applied']))
                self.repetitions_label.config(text=str(stats['repetitions_detected']))
            except:
                pass
            
            # Programar siguiente actualización
            self.root.after(1000, update_stats)
        
        # Iniciar loop
        self.root.after(1000, update_stats)
    
    def on_closing(self):
        """Manejar cierre de aplicación"""
        try:
            # Detener reconocimiento si está activo
            if self.is_listening:
                self.stop_recognition()
            
            # Detener hotkeys
            if hasattr(self, 'hotkey_listener'):
                self.hotkey_listener.stop()
            
            # Preguntar si guardar
            content = self.transcriptions_text.get(1.0, tk.END).strip()
            if content and len(content) > 50:
                result = messagebox.askyesnocancel(
                    "Guardar sesión",
                    "¿Desea guardar la sesión antes de salir?"
                )
                if result is True:
                    self.save_session()
                elif result is None:
                    return  # Cancelar cierre
            
            self.logger.info("=== Voice Bridge v2.2.0 cerrado ===")
            self.root.destroy()
            
        except:
            self.root.destroy()
    
    def run(self):
        """Ejecutar aplicación"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()


class ConfigWindow:
    """Ventana de configuración avanzada"""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("Configuración - Voice Bridge v2.2.0")
        self.window.geometry("700x600")
        self.window.resizable(False, False)
        
        # Aplicar tema
        colors = parent.theme_system.get_theme()
        self.window.configure(bg=colors['bg_main'])
        
        # Crear interfaz
        self.create_interface()
        
        # Centrar ventana
        self.window.transient(parent.root)
        self.window.grab_set()
    
    def create_interface(self):
        """Crear interfaz de configuración"""
        colors = self.parent.theme_system.get_theme()
        fonts = self.parent.theme_system.get_fonts()
        
        # Notebook para pestañas
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Pestaña General
        general_frame = tk.Frame(notebook, bg=colors['bg_surface'])
        notebook.add(general_frame, text="General")
        self.create_general_tab(general_frame)
        
        # Pestaña Azure
        azure_frame = tk.Frame(notebook, bg=colors['bg_surface'])
        notebook.add(azure_frame, text="Azure Speech")
        self.create_azure_tab(azure_frame)
        
        # Pestaña UI
        ui_frame = tk.Frame(notebook, bg=colors['bg_surface'])
        notebook.add(ui_frame, text="Interfaz")
        self.create_ui_tab(ui_frame)
        
        # Botones
        button_frame = tk.Frame(self.window, bg=colors['bg_main'])
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Button(button_frame,
                 text="Guardar",
                 command=self.save_config,
                 font=fonts['button'],
                 bg=colors['primary'],
                 fg='white',
                 activebackground=colors['primary_hover'],
                 relief=tk.FLAT,
                 padx=30, pady=8,
                 cursor='hand2').pack(side=tk.RIGHT, padx=(10, 0))
        
        tk.Button(button_frame,
                 text="Cancelar",
                 command=self.window.destroy,
                 font=fonts['button'],
                 bg=colors['bg_surface_hover'],
                 fg=colors['text_primary'],
                 relief=tk.FLAT,
                 padx=30, pady=8,
                 cursor='hand2').pack(side=tk.RIGHT)
    
    def create_general_tab(self, parent):
        """Crear pestaña general"""
        colors = self.parent.theme_system.get_theme()
        fonts = self.parent.theme_system.get_fonts()
        
        # Scrollable frame
        canvas = tk.Canvas(parent, bg=colors['bg_surface'])
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=colors['bg_surface'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Contenido
        frame = tk.Frame(scrollable_frame, bg=colors['bg_surface'])
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Auto enviar a Claude
        self.auto_send_var = tk.BooleanVar(value=self.parent.config.getboolean('auto_send_to_claude'))
        tk.Checkbutton(frame,
                      text="Auto-enviar a Claude",
                      variable=self.auto_send_var,
                      font=fonts['body'],
                      bg=colors['bg_surface'],
                      fg=colors['text_primary'],
                      activebackground=colors['bg_surface'],
                      selectcolor=colors['bg_surface']).pack(anchor=tk.W, pady=5)
        
        # TTS habilitado
        self.tts_enabled_var = tk.BooleanVar(value=self.parent.config.getboolean('tts_enabled'))
        tk.Checkbutton(frame,
                      text="Habilitar Text-to-Speech",
                      variable=self.tts_enabled_var,
                      font=fonts['body'],
                      bg=colors['bg_surface'],
                      fg=colors['text_primary'],
                      activebackground=colors['bg_surface'],
                      selectcolor=colors['bg_surface']).pack(anchor=tk.W, pady=5)
        
        # Corrección médica
        self.auto_correct_var = tk.BooleanVar(value=self.parent.config.getboolean('auto_correct_medical'))
        tk.Checkbutton(frame,
                      text="Corrección médica automática",
                      variable=self.auto_correct_var,
                      font=fonts['body'],
                      bg=colors['bg_surface'],
                      fg=colors['text_primary'],
                      activebackground=colors['bg_surface'],
                      selectcolor=colors['bg_surface']).pack(anchor=tk.W, pady=5)
        
        # Tipo de micrófono
        tk.Label(frame,
                text="Tipo de micrófono:",
                font=fonts['body_bold'],
                bg=colors['bg_surface'],
                fg=colors['text_primary']).pack(anchor=tk.W, pady=(20, 5))
        
        self.mic_type_var = tk.StringVar(value=self.parent.config.get('microphone_type'))
        mic_types = [
            ('Ambiental/Solapa', 'ambient'),
            ('Auriculares', 'headset'),
            ('Direccional/Boom', 'directional'),
            ('Integrado laptop', 'builtin')
        ]
        
        for text, value in mic_types:
            tk.Radiobutton(frame,
                          text=text,
                          variable=self.mic_type_var,
                          value=value,
                          font=fonts['body'],
                          bg=colors['bg_surface'],
                          fg=colors['text_primary'],
                          activebackground=colors['bg_surface'],
                          selectcolor=colors['bg_surface']).pack(anchor=tk.W, padx=(20, 0))
        
        # Pausa médica
        tk.Label(frame,
                text="Pausa para finalizar frase médica (segundos):",
                font=fonts['body_bold'],
                bg=colors['bg_surface'],
                fg=colors['text_primary']).pack(anchor=tk.W, pady=(20, 5))
        
        pause_frame = tk.Frame(frame, bg=colors['bg_surface'])
        pause_frame.pack(fill=tk.X, pady=5)
        
        self.pause_var = tk.DoubleVar(value=float(self.parent.config.get('medical_pause_seconds')))
        self.pause_scale = tk.Scale(pause_frame,
                                   from_=2, to=10,
                                   resolution=0.5,
                                   orient=tk.HORIZONTAL,
                                   variable=self.pause_var,
                                   bg=colors['bg_surface'],
                                   fg=colors['text_primary'],
                                   highlightthickness=0)
        self.pause_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.pause_label = tk.Label(pause_frame,
                                   text=f"{self.pause_var.get()}s",
                                   font=fonts['body_bold'],
                                   bg=colors['bg_surface'],
                                   fg=colors['primary'])
        self.pause_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.pause_scale.config(command=lambda v: self.pause_label.config(text=f"{float(v)}s"))
    
    def create_azure_tab(self, parent):
        """Crear pestaña Azure"""
        colors = self.parent.theme_system.get_theme()
        fonts = self.parent.theme_system.get_fonts()
        
        frame = tk.Frame(parent, bg=colors['bg_surface'])
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Región
        tk.Label(frame,
                text="Región de Azure:",
                font=fonts['body_bold'],
                bg=colors['bg_surface'],
                fg=colors['text_primary']).pack(anchor=tk.W, pady=(0, 5))
        
        self.region_var = tk.StringVar(value=self.parent.config.get('azure_region'))
        regions = ['eastus', 'westus', 'westus2', 'southcentralus', 'eastus2', 
                  'westeurope', 'northeurope', 'brazilsouth', 'australiaeast']
        
        region_combo = ttk.Combobox(frame,
                                   textvariable=self.region_var,
                                   values=regions,
                                   state='readonly',
                                   font=fonts['body'])
        region_combo.pack(fill=tk.X, pady=(0, 15))
        
        # Timeouts
        tk.Label(frame,
                text="Timeouts de reconocimiento:",
                font=fonts['body_bold'],
                bg=colors['bg_surface'],
                fg=colors['text_primary']).pack(anchor=tk.W, pady=(10, 10))
        
        # Silencio inicial
        self.create_timeout_control(frame, 
                                   "Silencio inicial (ms):",
                                   'azure_initial_silence_ms',
                                   5000, 30000, 1000)
        
        # Segmentación
        self.create_timeout_control(frame,
                                   "Segmentación (ms):",
                                   'azure_segmentation_ms',
                                   2000, 10000, 500)
        
        # Silencio final
        self.create_timeout_control(frame,
                                   "Silencio final (ms):",
                                   'azure_end_silence_ms',
                                   5000, 20000, 1000)
    
    def create_timeout_control(self, parent, label, config_key, min_val, max_val, resolution):
        """Crear control de timeout"""
        colors = self.parent.theme_system.get_theme()
        fonts = self.parent.theme_system.get_fonts()
        
        tk.Label(parent,
                text=label,
                font=fonts['body'],
                bg=colors['bg_surface'],
                fg=colors['text_secondary']).pack(anchor=tk.W, pady=(5, 0))
        
        control_frame = tk.Frame(parent, bg=colors['bg_surface'])
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        var = tk.IntVar(value=int(self.parent.config.get(config_key)))
        scale = tk.Scale(control_frame,
                        from_=min_val, to=max_val,
                        resolution=resolution,
                        orient=tk.HORIZONTAL,
                        variable=var,
                        bg=colors['bg_surface'],
                        fg=colors['text_primary'],
                        highlightthickness=0)
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        label = tk.Label(control_frame,
                        text=f"{var.get()}ms",
                        font=fonts['body_bold'],
                        bg=colors['bg_surface'],
                        fg=colors['primary'])
        label.pack(side=tk.RIGHT, padx=(10, 0))
        
        scale.config(command=lambda v: label.config(text=f"{int(float(v))}ms"))
        
        # Guardar referencia
        setattr(self, f"{config_key}_var", var)
    
    def create_ui_tab(self, parent):
        """Crear pestaña UI"""
        colors = self.parent.theme_system.get_theme()
        fonts = self.parent.theme_system.get_fonts()
        
        frame = tk.Frame(parent, bg=colors['bg_surface'])
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Tema
        tk.Label(frame,
                text="Tema de la interfaz:",
                font=fonts['body_bold'],
                bg=colors['bg_surface'],
                fg=colors['text_primary']).pack(anchor=tk.W, pady=(0, 10))
        
        self.theme_var = tk.StringVar(value=self.parent.theme_system.current_theme)
        
        theme_frame = tk.Frame(frame, bg=colors['bg_surface'])
        theme_frame.pack(anchor=tk.W, padx=(20, 0))
        
        tk.Radiobutton(theme_frame,
                      text="Modo Claro ☀️",
                      variable=self.theme_var,
                      value='light',
                      font=fonts['body'],
                      bg=colors['bg_surface'],
                      fg=colors['text_primary']).pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Radiobutton(theme_frame,
                      text="Modo Oscuro 🌙",
                      variable=self.theme_var,
                      value='dark',
                      font=fonts['body'],
                      bg=colors['bg_surface'],
                      fg=colors['text_primary']).pack(side=tk.LEFT)
        
        # Idioma
        tk.Label(frame,
                text="Idioma de la interfaz:",
                font=fonts['body_bold'],
                bg=colors['bg_surface'],
                fg=colors['text_primary']).pack(anchor=tk.W, pady=(20, 10))
        
        self.lang_var = tk.StringVar(value=self.parent.theme_system.current_language)
        
        lang_frame = tk.Frame(frame, bg=colors['bg_surface'])
        lang_frame.pack(anchor=tk.W, padx=(20, 0))
        
        tk.Radiobutton(lang_frame,
                      text="English",
                      variable=self.lang_var,
                      value='en',
                      font=fonts['body'],
                      bg=colors['bg_surface'],
                      fg=colors['text_primary']).pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Radiobutton(lang_frame,
                      text="Español",
                      variable=self.lang_var,
                      value='es',
                      font=fonts['body'],
                      bg=colors['bg_surface'],
                      fg=colors['text_primary']).pack(side=tk.LEFT)
        
        # Nota
        note_text = ("⚠️ Los cambios de tema e idioma requieren reiniciar la aplicación "
                    "para aplicarse completamente.")
        tk.Label(frame,
                text=note_text,
                font=fonts['caption'],
                bg=colors['bg_surface'],
                fg=colors['text_muted'],
                wraplength=400,
                justify=tk.LEFT).pack(anchor=tk.W, pady=(30, 0))
    
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
            
            # Timeouts Azure
            if hasattr(self, 'azure_initial_silence_ms_var'):
                self.parent.config['azure_initial_silence_ms'] = str(self.azure_initial_silence_ms_var.get())
            if hasattr(self, 'azure_segmentation_ms_var'):
                self.parent.config['azure_segmentation_ms'] = str(self.azure_segmentation_ms_var.get())
            if hasattr(self, 'azure_end_silence_ms_var'):
                self.parent.config['azure_end_silence_ms'] = str(self.azure_end_silence_ms_var.get())
            
            # UI
            self.parent.config['ui_theme'] = self.theme_var.get()
            self.parent.config['ui_language'] = self.lang_var.get()
            
            # Actualizar sistemas
            self.parent.theme_system.current_theme = self.theme_var.get()
            self.parent.theme_system.current_language = self.lang_var.get()
            self.parent.medical_pause_seconds = float(self.pause_var.get())
            
            # Guardar a archivo
            config_file = Path.home() / "voice-bridge-claude" / "config" / "voice_bridge_config.ini"
            config_parser = configparser.ConfigParser()
            config_parser['DEFAULT'] = dict(self.parent.config)
            
            with open(config_file, 'w') as f:
                config_parser.write(f)
            
            self.parent.log_to_gui("💾 Configuración guardada")
            
            # Reconfigurar Azure si cambió
            if hasattr(self, 'azure_initial_silence_ms_var'):
                was_listening = self.parent.is_listening
                if was_listening:
                    self.parent.stop_recognition()
                
                self.parent.setup_azure()
                
                if was_listening:
                    self.parent.start_recognition()
            
            messagebox.showinfo("Éxito", "Configuración guardada correctamente")
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {e}")


def main():
    """Función principal"""
    try:
        if not os.environ.get('AZURE_SPEECH_KEY'):
            print("❌ ERROR: AZURE_SPEECH_KEY no está configurado")
            print("Por favor configura la variable de entorno AZURE_SPEECH_KEY")
            return
        
        app = VoiceBridge220()
        app.run()
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
