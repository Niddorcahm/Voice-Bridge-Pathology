#!/usr/bin/env python3
"""
Voice Bridge v224 - Versión Completamente Reescrita SIN DEPENDENCIAS ADICIONALES
Reconocimiento de voz médico con Azure Speech SDK optimizado para PipeWire
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import tkinter.font
import azure.cognitiveservices.speech as speechsdk
import json
import os
import sys
import time
import threading
import logging
import queue
import subprocess
import re
from datetime import datetime
from difflib import SequenceMatcher

# ===== CONFIGURACIONES GLOBALES =====
VERSION = "2.2.4"
CONFIG_FILE = "voice_bridge_config.json"
MEDICAL_TERMS_FILE = "medical_terms.json"


# ===== CONFIGURACIÓN DE LOGGING =====
def setup_logger():
    """Configurar logging del sistema"""
    logger = logging.getLogger('VoiceBridge')
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Handler para archivo
        os.makedirs('logs', exist_ok=True)
        file_handler = logging.FileHandler(f'logs/voice_bridge_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler.setLevel(logging.DEBUG)

        # Formato
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


# ===== SISTEMA DE TEMAS =====
class ThemeSystem:
    """Sistema de gestión de temas y localización"""

    def __init__(self):
        self.current_theme = "dark"
        self.current_language = "es"
        self.detect_fonts()

    def detect_fonts(self):
        """Detectar fuentes disponibles"""
        try:
            # Fuentes predeterminadas para diferentes sistemas
            system_fonts = {
                'primary': ['DejaVu Sans', 'Arial', 'Helvetica', 'Liberation Sans'],
                'mono': ['DejaVu Sans Mono', 'Courier New', 'Liberation Mono']
            }

            # Detectar fuente principal
            for font in system_fonts['primary']:
                try:
                    test_font = tk.font.Font(family=font, size=10)
                    self.primary_font = font
                    break
                except:
                    continue
            else:
                self.primary_font = 'TkDefaultFont'

            # Detectar fuente monoespaciada
            for font in system_fonts['mono']:
                try:
                    test_font = tk.font.Font(family=font, size=10)
                    self.mono_font = font
                    break
                except:
                    continue
            else:
                self.mono_font = 'TkFixedFont'

        except Exception as e:
            self.primary_font = 'TkDefaultFont'
            self.mono_font = 'TkFixedFont'

    def get_theme(self):
        """Obtener configuración del tema actual"""
        themes = {
            "dark": {
                "bg": "#2d2d2d",
                "fg": "#ffffff",
                "select_bg": "#404040",
                "button_bg": "#4a4a4a",
                "button_fg": "#ffffff",
                "entry_bg": "#404040",
                "entry_fg": "#ffffff",
                "text_bg": "#1e1e1e",
                "text_fg": "#ffffff",
                "accent": "#0078d4",
                "success": "#0dbc79",
                "warning": "#ffb900",
                "error": "#d13438"
            },
            "light": {
                "bg": "#f0f0f0",
                "fg": "#000000",
                "select_bg": "#e0e0e0",
                "button_bg": "#e1e1e1",
                "button_fg": "#000000",
                "entry_bg": "#ffffff",
                "entry_fg": "#000000",
                "text_bg": "#ffffff",
                "text_fg": "#000000",
                "accent": "#0078d4",
                "success": "#107c10",
                "warning": "#ff8c00",
                "error": "#d13438"
            }
        }
        return themes.get(self.current_theme, themes["dark"])

    def get_fonts(self):
        """Obtener configuración de fuentes"""
        return {
            "primary": (self.primary_font, 10),
            "heading": (self.primary_font, 12, "bold"),
            "mono": (self.mono_font, 9),
            "small": (self.primary_font, 8)
        }

    def get_texts(self):
        """Obtener textos localizados"""
        texts = {
            "es": {
                "title": "Voice Bridge v2.2.4 - Reconocimiento Médico",
                "start": "Iniciar",
                "stop": "Detener",
                "config": "Configurar",
                "clear": "Limpiar",
                "save": "Guardar",
                "status_ready": "Listo",
                "status_listening": "Escuchando...",
                "status_error": "Error",
                "transcription": "Transcripción:",
                "stats": "Estadísticas",
                "phrases": "Frases:",
                "corrections": "Correcciones:",
                "repetitions": "Repeticiones:",
                "session_time": "Tiempo sesión:",
                "azure_config": "Configuración Azure",
                "azure_key": "Clave API:",
                "azure_region": "Región:",
                "azure_language": "Idioma:",
                "test_connection": "Probar Conexión",
                "save_config": "Guardar Configuración",
                "cancel": "Cancelar"
            }
        }
        return texts.get(self.current_language, texts["es"])


# ===== CORRECTOR MÉDICO =====
class MedicalCorrector:
    """Corrector de términos médicos"""

    def __init__(self):
        self.medical_terms = {}
        self.corrections_applied = 0
        self.context_window = 3
        self.load_terms()

    def load_terms(self):
        """Cargar términos médicos"""
        try:
            if os.path.exists(MEDICAL_TERMS_FILE):
                with open(MEDICAL_TERMS_FILE, 'r', encoding='utf-8') as f:
                    self.medical_terms = json.load(f)
            else:
                # Términos médicos básicos por defecto
                self.medical_terms = {
                    "auscultacion": "auscultación",
                    "palpacion": "palpación",
                    "inspeccion": "inspección",
                    "percusion": "percusión",
                    "hipertension": "hipertensión",
                    "taquicardia": "taquicardia",
                    "bradicardia": "bradicardia",
                    "disnea": "disnea",
                    "cianosis": "cianosis",
                    "edema": "edema",
                    "abdomen": "abdomen",
                    "torax": "tórax",
                    "corazon": "corazón",
                    "pulmon": "pulmón",
                    "respiracion": "respiración"
                }
                # Guardar términos por defecto
                with open(MEDICAL_TERMS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.medical_terms, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error cargando términos médicos: {e}")
            self.medical_terms = {}

    def correct_text(self, text):
        """Aplicar correcciones médicas al texto"""
        if not text or not self.medical_terms:
            return text

        corrected_text = text
        corrections_made = 0

        for incorrect, correct in self.medical_terms.items():
            if incorrect.lower() in corrected_text.lower():
                # Reemplazar manteniendo el caso original
                pattern = re.compile(re.escape(incorrect), re.IGNORECASE)
                corrected_text = pattern.sub(correct, corrected_text)
                corrections_made += 1

        self.corrections_applied += corrections_made
        return corrected_text


# ===== DETECTOR DE REPETICIONES =====
class RepetitionDetector:
    """Detector de frases repetidas"""

    def __init__(self):
        self.recent_phrases = []
        self.repetitions_found = 0
        self.similarity_threshold = 0.8

    def is_repetition(self, new_phrase):
        """Verificar si la frase es una repetición"""
        if not new_phrase or len(new_phrase.strip()) < 5:
            return False

        for existing_phrase in self.recent_phrases:
            similarity = SequenceMatcher(None, new_phrase.lower(), existing_phrase.lower()).ratio()
            if similarity >= self.similarity_threshold:
                self.repetitions_found += 1
                return True

        # Agregar frase a la lista (mantener solo las últimas 10)
        self.recent_phrases.append(new_phrase)
        if len(self.recent_phrases) > 10:
            self.recent_phrases.pop(0)

        return False


# ===== COLECTOR DE ESTADÍSTICAS =====
class StatsCollector:
    """Colector de estadísticas de sesión"""

    def __init__(self):
        self.session_start = time.time()
        self.stats = {
            'phrases_count': 0,
            'words_count': 0,
            'corrections_applied': 0,
            'repetitions_detected': 0,
            'session_duration': 0,
            'chars_transcribed': 0
        }

    def update(self, phrase, corrections=0, is_repetition=False):
        """Actualizar estadísticas"""
        if phrase:
            self.stats['phrases_count'] += 1
            self.stats['words_count'] += len(phrase.split())
            self.stats['chars_transcribed'] += len(phrase)

        self.stats['corrections_applied'] += corrections

        if is_repetition:
            self.stats['repetitions_detected'] += 1

        self.stats['session_duration'] = int(time.time() - self.session_start)


# ===== CLASE PRINCIPAL =====
class VoiceBridge224:
    """Aplicación principal Voice Bridge v2.2.4"""

    def __init__(self):
        # Inicialización del logger
        self.logger = setup_logger()
        self.logger.info(f"Iniciando Voice Bridge v{VERSION}")

        # Sistema de temas y componentes
        self.theme_system = ThemeSystem()
        self.medical_corrector = MedicalCorrector()
        self.repetition_detector = RepetitionDetector()
        self.stats_collector = StatsCollector()

        # Estados de la aplicación
        self.is_listening = False
        self.is_speaking = False
        self.azure_ready = False
        self.recognition_paused = False

        # Configuración
        self.config = {}
        self.load_config()

        # Componentes Azure (se inicializan después)
        self.speech_config = None
        self.audio_config = None
        self.speech_recognizer = None
        self.speech_synthesizer = None

        # Buffer médico
        self.medical_buffer = ""
        self.medical_pause_seconds = 2.0
        self.buffer_timer = None

        # Colas y threading
        self.transcription_queue = queue.Queue()
        self.session_start = time.time()
        self.transcription_count = 0

        # Configurar GUI
        self.setup_gui()

        # Configurar Azure después de la GUI
        self.root.after(500, self.delayed_azure_setup)

    def load_config(self):
        """Cargar configuración desde el archivo"""
        default_config = {
            'azure_key': '',
            'azure_region': 'eastus',
            'azure_language': 'es-ES',
            'theme': 'dark',
            'ui_language': 'es',
            'medical_pause_seconds': 2.0,
            'auto_correct': True,
            'show_stats': True,
            'tts_enabled': False,
            'similarity_threshold': 0.8,
            'initial_silence_timeout': 8000,
            'end_silence_timeout': 2000,
            'segmentation_silence_timeout': 500
        }

        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    default_config.update(saved_config)
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")

        self.config = default_config

        # Actualizar configuraciones de componentes
        self.medical_pause_seconds = self.config.get('medical_pause_seconds', 2.0)
        self.repetition_detector.similarity_threshold = self.config.get('similarity_threshold', 0.8)

    def save_config(self):
        """Guardar configuración actual"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.info("Configuración guardada")
        except Exception as e:
            self.logger.error(f"Error guardando configuración: {e}")

    def setup_gui(self):
        """Configurar interfaz gráfica"""
        self.root = tk.Tk()
        self.root.title(self.theme_system.get_texts()["title"])
        self.root.geometry("800x600")
        self.root.minsize(600, 400)

        # Aplicar tema
        self.apply_theme()

        # Crear interfaz principal
        self.create_main_interface()

        # Configurar cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Iniciar loops de actualización
        self.start_update_loops()

    def apply_theme(self):
        """Aplicar tema actual"""
        theme = self.theme_system.get_theme()

        # Configurar colores de la ventana principal
        self.root.configure(bg=theme["bg"])

        # Configurar estilo para ttk
        style = ttk.Style()
        style.theme_use('clam')

        # Configurar estilos personalizados
        style.configure('Custom.TButton',
                        background=theme["button_bg"],
                        foreground=theme["button_fg"],
                        borderwidth=1,
                        focuscolor='none')

        style.configure('Custom.TLabel',
                        background=theme["bg"],
                        foreground=theme["fg"])

        style.configure('Custom.TFrame',
                        background=theme["bg"])

    def create_main_interface(self):
        """Crear la interfaz principal"""
        theme = self.theme_system.get_theme()
        fonts = self.theme_system.get_fonts()
        texts = self.theme_system.get_texts()

        # Frame principal
        main_frame = ttk.Frame(self.root, style='Custom.TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # ===== SECCIÓN DE CONTROL =====
        control_frame = ttk.Frame(main_frame, style='Custom.TFrame')
        control_frame.pack(fill='x', pady=(0, 10))

        # Botones principales
        self.start_button = tk.Button(
            control_frame,
            text=texts["start"],
            command=self.toggle_recognition,
            bg=theme["success"],
            fg="white",
            font=fonts["heading"],
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2'
        )
        self.start_button.pack(side='left', padx=(0, 10))

        # Botón de configuración
        config_button = tk.Button(
            control_frame,
            text=texts["config"],
            command=self.open_config,
            bg=theme["button_bg"],
            fg=theme["button_fg"],
            font=fonts["primary"],
            padx=15,
            pady=10,
            relief='flat',
            cursor='hand2'
        )
        config_button.pack(side='left', padx=(0, 10))

        # Botón limpiar
        clear_button = tk.Button(
            control_frame,
            text=texts["clear"],
            command=self.clear_transcription,
            bg=theme["warning"],
            fg="white",
            font=fonts["primary"],
            padx=15,
            pady=10,
            relief='flat',
            cursor='hand2'
        )
        clear_button.pack(side='left', padx=(0, 10))

        # Botón guardar
        save_button = tk.Button(
            control_frame,
            text=texts["save"],
            command=self.save_session,
            bg=theme["accent"],
            fg="white",
            font=fonts["primary"],
            padx=15,
            pady=10,
            relief='flat',
            cursor='hand2'
        )
        save_button.pack(side='left')

        # ===== SECCIÓN DE ESTADO =====
        status_frame = ttk.Frame(main_frame, style='Custom.TFrame')
        status_frame.pack(fill='x', pady=(0, 10))

        self.status_label = tk.Label(
            status_frame,
            text=texts["status_ready"],
            bg=theme["bg"],
            fg=theme["fg"],
            font=fonts["primary"],
            anchor='w'
        )
        self.status_label.pack(fill='x')

        # ===== SECCIÓN DE TRANSCRIPCIÓN =====
        transcription_frame = ttk.Frame(main_frame, style='Custom.TFrame')
        transcription_frame.pack(fill='both', expand=True, pady=(0, 10))

        # Etiqueta de transcripción
        transcription_label = tk.Label(
            transcription_frame,
            text=texts["transcription"],
            bg=theme["bg"],
            fg=theme["fg"],
            font=fonts["heading"],
            anchor='w'
        )
        transcription_label.pack(fill='x', pady=(0, 5))

        # Área de texto de transcripción
        self.transcriptions_text = scrolledtext.ScrolledText(
            transcription_frame,
            wrap=tk.WORD,
            bg=theme["text_bg"],
            fg=theme["text_fg"],
            font=fonts["mono"],
            insertbackground=theme["fg"],
            selectbackground=theme["select_bg"],
            relief='flat',
            borderwidth=2,
            highlightthickness=1,
            highlightcolor=theme["accent"]
        )
        self.transcriptions_text.pack(fill='both', expand=True)

        # ===== SECCIÓN DE ESTADÍSTICAS =====
        if self.config.get('show_stats', True):
            self.create_stats_panel(main_frame)

        # ===== SECCIÓN DE LOG =====
        log_frame = ttk.Frame(main_frame, style='Custom.TFrame')
        log_frame.pack(fill='x', pady=(10, 0))

        # Log de eventos
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=6,
            wrap=tk.WORD,
            bg=theme["text_bg"],
            fg=theme["fg"],
            font=fonts["small"],
            insertbackground=theme["fg"],
            relief='flat',
            borderwidth=1
        )
        self.log_text.pack(fill='x')

    def create_stats_panel(self, parent):
        """Crear panel de estadísticas"""
        theme = self.theme_system.get_theme()
        fonts = self.theme_system.get_fonts()
        texts = self.theme_system.get_texts()

        stats_frame = ttk.Frame(parent, style='Custom.TFrame', relief='solid', borderwidth=1)
        stats_frame.pack(fill='x', pady=(0, 10))

        # Título de estadísticas
        stats_title = tk.Label(
            stats_frame,
            text=texts["stats"],
            bg=theme["bg"],
            fg=theme["accent"],
            font=fonts["heading"]
        )
        stats_title.pack(pady=5)

        # Frame para estadísticas en línea
        stats_content = ttk.Frame(stats_frame, style='Custom.TFrame')
        stats_content.pack(fill='x', padx=10, pady=5)

        # Estadísticas individuales
        self.phrases_label = self.create_stat_widget(stats_content, texts["phrases"], "0")
        self.corrections_label = self.create_stat_widget(stats_content, texts["corrections"], "0")
        self.repetitions_label = self.create_stat_widget(stats_content, texts["repetitions"], "0")
        self.session_time_label = self.create_stat_widget(stats_content, texts["session_time"], "00:00")

    def create_stat_widget(self, parent, label_text, value_text):
        """Crear widget de estadística individual"""
        theme = self.theme_system.get_theme()
        fonts = self.theme_system.get_fonts()

        # Frame contenedor
        stat_frame = ttk.Frame(parent, style='Custom.TFrame')
        stat_frame.pack(side='left', fill='x', expand=True, padx=5)

        # Etiqueta
        label = tk.Label(
            stat_frame,
            text=label_text,
            bg=theme["bg"],
            fg=theme["fg"],
            font=fonts["small"]
        )
        label.pack()

        # Valor
        value_label = tk.Label(
            stat_frame,
            text=value_text,
            bg=theme["bg"],
            fg=theme["accent"],
            font=fonts["primary"]
        )
        value_label.pack()

        return value_label

    def delayed_azure_setup(self):
        """Configurar Azure con delay para evitar problemas de inicialización"""
        try:
            self.log_to_gui("🔄 Configurando Azure Speech SDK...")
            time.sleep(0.5)  # Pequeño delay para estabilidad
            self.setup_azure()
        except Exception as e:
            self.logger.error(f"Error en configuración diferida de Azure: {e}")
            self.log_to_gui(f"❌ Error configurando Azure: {e}")

    def setup_azure(self):
        """CONFIGURACIÓN AZURE LIMPIA SIN PROPIEDADES PROBLEMÁTICAS"""
        try:
            if not self.config.get('azure_key') or not self.config.get('azure_region'):
                self.log_to_gui("⚠️ Configuración Azure incompleta - abriendo configuración")
                self.open_config()
                return

            self.log_to_gui("🔧 Configurando Azure Speech SDK...")

            # === PASO 1: VERIFICAR SISTEMA DE AUDIO ===
            self.log_to_gui("🎤 Verificando sistema de audio...")
            audio_available = self.verify_audio_system()
            if not audio_available:
                self.log_to_gui("⚠️ Problemas con sistema de audio - continuando con configuración básica")

            # === PASO 2: CONFIGURAR SPEECH SDK ===
            self.speech_config = speechsdk.SpeechConfig(
                subscription=self.config['azure_key'],
                region=self.config['azure_region']
            )

            # Configurar idioma
            self.speech_config.speech_recognition_language = self.config.get('azure_language', 'es-ES')

            # === PASO 3: CONFIGURACIONES BÁSICAS SOLAMENTE ===
            self.log_to_gui("⚙️ Aplicando configuraciones básicas...")

            # Solo timeouts básicos que sabemos que existen
            try:
                self.speech_config.set_property(
                    speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
                    str(self.config.get('initial_silence_timeout', 8000))
                )
            except:
                self.log_to_gui("⚠️ Initial silence timeout no disponible")

            try:
                self.speech_config.set_property(
                    speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs,
                    str(self.config.get('end_silence_timeout', 2000))
                )
            except:
                self.log_to_gui("⚠️ End silence timeout no disponible")

            try:
                self.speech_config.set_property(
                    speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs,
                    str(self.config.get('segmentation_silence_timeout', 500))
                )
            except:
                self.log_to_gui("⚠️ Segmentation timeout no disponible")

            # === PASO 4: CONFIGURAR AUDIO ===
            self.log_to_gui("🎵 Configurando entrada de audio...")
            self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

            # === PASO 5: CREAR RECOGNIZER ===
            self.log_to_gui("🤖 Creando reconocedor de voz...")
            self.speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=self.audio_config
            )

            # === PASO 6: CONFIGURAR CALLBACKS ===
            self.setup_speech_callbacks()

            # === PASO 7: CONFIGURAR TTS SI ESTÁ HABILITADO ===
            if self.config.get('tts_enabled', False):
                self.speech_synthesizer = speechsdk.SpeechSynthesizer(
                    speech_config=self.speech_config
                )
                self.log_to_gui("🔊 TTS configurado")

            # === PASO 8: PROBAR CONEXIÓN ===
            self.log_to_gui("🔍 Probando conexión con Azure...")
            self.test_azure_connection()

            # === PASO 9: OPTIMIZAR PIPEWIRE ===
            self.optimize_pipewire_for_dictation()

            # Marcar como listo
            self.azure_ready = True
            self.log_to_gui("✅ Azure Speech SDK configurado correctamente")

        except Exception as e:
            self.logger.error(f"Error configurando Azure: {e}")
            self.log_to_gui(f"❌ Error Azure: {e}")
            self.azure_ready = False
            # Mostrar diálogo de configuración automáticamente
            self.root.after(1000, self.open_config)

    def verify_audio_system(self):
        """Verificar disponibilidad del sistema de audio"""
        try:
            # Verificar PulseAudio/PipeWire
            result = subprocess.run(['pactl', 'info'], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                self.log_to_gui("⚠️ PulseAudio/PipeWire no disponible")
                return False

            # Verificar fuentes de audio
            sources_result = subprocess.run(['pactl', 'list', 'short', 'sources'],
                                            capture_output=True, text=True, timeout=5)
            if sources_result.returncode != 0 or not sources_result.stdout.strip():
                self.log_to_gui("⚠️ No se encontraron fuentes de audio")
                return False

            # Verificar micrófono por defecto
            default_source = subprocess.run(['pactl', 'get-default-source'],
                                            capture_output=True, text=True, timeout=3)
            if default_source.returncode == 0:
                source_name = default_source.stdout.strip()
                self.log_to_gui(f"🎤 Micrófono detectado: {source_name}")

                # Verificar que no esté suspendido
                self.ensure_microphone_active(source_name)

                return True
            else:
                self.log_to_gui("⚠️ No hay micrófono por defecto configurado")
                return False

        except subprocess.TimeoutExpired:
            self.log_to_gui("⏱️ Timeout verificando audio")
            return False
        except Exception as e:
            self.log_to_gui(f"⚠️ Error verificando audio: {e}")
            return False

    def ensure_microphone_active(self, source_name):
        """Asegurar que el micrófono esté activo"""
        try:
            # Verificar estado del micrófono
            info_result = subprocess.run(['pactl', 'list', 'sources'],
                                         capture_output=True, text=True, timeout=5)

            if "SUSPENDED" in info_result.stdout:
                self.log_to_gui("🔄 Activando micrófono suspendido...")
                subprocess.run(['pactl', 'suspend-source', source_name, '0'], timeout=3)
                time.sleep(0.5)
                self.log_to_gui("✅ Micrófono activado")

        except Exception as e:
            self.log_to_gui(f"⚠️ Error activando micrófono: {e}")

    def test_azure_connection(self):
        """Probar conexión con Azure"""
        try:
            # Crear un recognizer temporal para probar
            temp_config = speechsdk.SpeechConfig(
                subscription=self.config['azure_key'],
                region=self.config['azure_region']
            )
            temp_config.speech_recognition_language = self.config.get('azure_language', 'es-ES')

            # Test rápido de configuración
            temp_recognizer = speechsdk.SpeechRecognizer(speech_config=temp_config)
            self.log_to_gui("✅ Conexión Azure verificada")

        except Exception as e:
            self.log_to_gui(f"❌ Error conexión Azure: {e}")
            raise

    def optimize_pipewire_for_dictation(self):
        """Optimizar PipeWire para dictado médico"""
        try:
            self.log_to_gui("🔧 Optimizando PipeWire para dictado...")

            # Configuraciones PipeWire específicas
            optimizations = [
                # Reducir latencia
                ['pactl', 'set-default-source-volume', '@DEFAULT_SOURCE@', '75%'],
                # Asegurar que esté unmuted
                ['pactl', 'set-source-mute', '@DEFAULT_SOURCE@', '0'],
            ]

            for cmd in optimizations:
                try:
                    subprocess.run(cmd, capture_output=True, timeout=3)
                except:
                    continue

            self.log_to_gui("✅ PipeWire optimizado")

        except Exception as e:
            self.log_to_gui(f"⚠️ Error optimizando PipeWire: {e}")

    def setup_speech_callbacks(self):
        """Configurar callbacks de reconocimiento con manejo mejorado"""
        if not self.speech_recognizer:
            return

        def recognizing_callback(evt):
            """Callback para reconocimiento parcial - CONFIRMA AUDIO REAL"""
            if evt.result.text and len(evt.result.text.strip()) > 0:
                self.log_to_gui(f"🎤 Audio: {evt.result.text[:30]}...")
                # Actualizar UI en hilo principal
                self.root.after(0, lambda: self.update_partial_text(evt.result.text))

        def recognized_callback(evt):
            """Callback para reconocimiento completo"""
            if evt.result.text and len(evt.result.text.strip()) > 0:
                self.log_to_gui(f"✅ Reconocido: {evt.result.text}")
                # Procesar en hilo principal
                self.root.after(0, lambda: self.process_recognized_text(evt.result.text))
            else:
                # Reconocimiento vacío - podría indicar problema de audio
                self.log_to_gui("⚠️ Reconocimiento vacío")

        def canceled_callback(evt):
            """Callback para errores y cancelaciones"""
            reason = evt.result.reason
            if reason == speechsdk.ResultReason.Canceled:
                details = evt.result.cancellation_details
                error_msg = f"Reconocimiento cancelado: {details.reason}"

                if details.reason == speechsdk.CancellationReason.Error:
                    error_msg += f" - {details.error_details}"
                    self.log_to_gui(f"❌ {error_msg}")

                    # Manejo específico de errores de audio
                    if "audio" in details.error_details.lower():
                        self.log_to_gui("🔄 Error de audio detectado - reiniciando...")
                        self.root.after(2000, self.restart_recognition)
                else:
                    self.log_to_gui(f"⚠️ {error_msg}")

        def session_started_callback(evt):
            """Sesión iniciada correctamente"""
            self.log_to_gui("🔊 Sesión de reconocimiento iniciada")
            self.update_status("Escuchando...")

        def session_stopped_callback(evt):
            """Sesión detenida"""
            self.log_to_gui("⏹️ Sesión de reconocimiento detenida")
            if self.is_listening:
                # Si debería estar escuchando pero se detuvo, hay un problema
                self.log_to_gui("⚠️ Sesión detenida inesperadamente")
                self.is_listening = False
                self.root.after(0, self.update_ui_state)

        # Conectar todos los callbacks
        self.speech_recognizer.recognizing.connect(recognizing_callback)
        self.speech_recognizer.recognized.connect(recognized_callback)
        self.speech_recognizer.canceled.connect(canceled_callback)
        self.speech_recognizer.session_started.connect(session_started_callback)
        self.speech_recognizer.session_stopped.connect(session_stopped_callback)

    def restart_recognition(self):
        """Reiniciar reconocimiento después de error"""
        try:
            if self.is_listening:
                self.log_to_gui("🔄 Reiniciando reconocimiento...")
                self.stop_recognition()
                time.sleep(1)
                self.start_recognition()
        except Exception as e:
            self.log_to_gui(f"❌ Error reiniciando: {e}")

    def toggle_recognition(self):
        """Alternar estado de reconocimiento"""
        if not self.azure_ready:
            self.log_to_gui("❌ Azure no está configurado")
            self.open_config()
            return

        if self.is_listening:
            self.stop_recognition()
        else:
            self.start_recognition()

    def start_recognition(self):
        """Iniciar reconocimiento con verificaciones completas"""
        try:
            if not self.azure_ready or not self.speech_recognizer:
                self.log_to_gui("❌ Azure no está listo")
                return

            if self.is_listening:
                self.log_to_gui("ℹ️ Ya está reconociendo")
                return

            # Verificar audio antes de iniciar
            self.log_to_gui("🔍 Verificando audio antes de iniciar...")
            if not self.pre_recognition_audio_check():
                self.log_to_gui("⚠️ Problemas de audio detectados - continuando")

            # Recrear recognizer para evitar estados inconsistentes
            self.log_to_gui("🔄 Preparando reconocedor...")
            self.recreate_recognizer()

            # Iniciar reconocimiento continuo
            self.log_to_gui("🎤 Iniciando reconocimiento...")
            self.speech_recognizer.start_continuous_recognition()

            # Actualizar estado
            self.is_listening = True
            self.session_start = time.time()

            # Verificar que realmente inició
            self.root.after(1500, self.verify_recognition_started)

            self.update_ui_state()

        except Exception as e:
            self.logger.error(f"Error iniciando reconocimiento: {e}")
            self.log_to_gui(f"❌ Error iniciando: {e}")
            self.is_listening = False
            self.update_ui_state()

    def pre_recognition_audio_check(self):
        """Verificación pre-reconocimiento del audio"""
        try:
            # Verificar micrófono por defecto
            result = subprocess.run(['pactl', 'get-default-source'],
                                    capture_output=True, text=True, timeout=3)
            if result.returncode != 0:
                return False

            source_name = result.stdout.strip()
            if not source_name:
                return False

            # Verificar que no esté suspendido
            self.ensure_microphone_active(source_name)

            self.log_to_gui(f"✅ Audio verificado: {source_name}")
            return True

        except Exception as e:
            self.log_to_gui(f"⚠️ Error verificando audio: {e}")
            return False

    def recreate_recognizer(self):
        """Recrear recognizer para evitar estados inconsistentes"""
        try:
            # Detener recognizer existente si está activo
            if hasattr(self, 'speech_recognizer') and self.speech_recognizer:
                try:
                    self.speech_recognizer.stop_continuous_recognition()
                except:
                    pass

            # Crear nuevo recognizer
            self.speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=self.audio_config
            )

            # Reconectar callbacks
            self.setup_speech_callbacks()

        except Exception as e:
            self.log_to_gui(f"❌ Error recreando recognizer: {e}")
            raise

    def verify_recognition_started(self):
        """Verificar que el reconocimiento realmente inició"""
        try:
            if self.is_listening:
                self.log_to_gui("✅ Reconocimiento activo - hable ahora")
                self.update_status("Escuchando...")
            else:
                self.log_to_gui("⚠️ Reconocimiento no se inició correctamente")
        except Exception as e:
            self.log_to_gui(f"⚠️ Error verificando reconocimiento: {e}")

    def stop_recognition(self):
        """Detener reconocimiento"""
        try:
            if not self.is_listening:
                return

            self.log_to_gui("⏹️ Deteniendo reconocimiento...")

            if self.speech_recognizer:
                self.speech_recognizer.stop_continuous_recognition()

            self.is_listening = False
            self.update_ui_state()

        except Exception as e:
            self.logger.error(f"Error deteniendo reconocimiento: {e}")
            self.log_to_gui(f"❌ Error deteniendo: {e}")

    def process_recognized_text(self, text):
        """Procesar texto reconocido con correcciones y estadísticas"""
        if not text or not text.strip():
            return

        original_text = text
        corrections_made = 0

        # Aplicar correcciones médicas
        if self.config.get('auto_correct', True):
            corrected_text = self.medical_corrector.correct_text(text)
            corrections_made = self.medical_corrector.corrections_applied - self.stats_collector.stats[
                'corrections_applied']
            text = corrected_text

        # Verificar repeticiones
        is_repetition = self.repetition_detector.is_repetition(text)

        # Actualizar estadísticas
        self.stats_collector.update(text, corrections_made, is_repetition)

        # Procesar con buffer médico
        self.add_to_medical_buffer(text)

        # Actualizar UI
        self.update_stats_display()

        # Log del resultado
        if corrections_made > 0:
            self.log_to_gui(f"📝 Correcciones aplicadas: {corrections_made}")
        if is_repetition:
            self.log_to_gui(f"🔄 Repetición detectada")

    def add_to_medical_buffer(self, text):
        """Agregar texto al buffer médico con procesamiento por lotes"""
        self.medical_buffer += text + " "

        # Cancelar timer anterior si existe
        if self.buffer_timer:
            self.root.after_cancel(self.buffer_timer)

        # Programar procesamiento del buffer
        self.buffer_timer = self.root.after(
            int(self.medical_pause_seconds * 1000),
            self.process_medical_buffer
        )

    def process_medical_buffer(self):
        """Procesar buffer médico acumulado"""
        if not self.medical_buffer.strip():
            return

        # Agregar al área de transcripción
        self.add_to_transcription(self.medical_buffer.strip())

        # Limpiar buffer
        self.medical_buffer = ""
        self.buffer_timer = None

    def add_to_transcription(self, text):
        """Agregar texto al área de transcripción"""
        if not text:
            return

        # Agregar timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_text = f"[{timestamp}] {text}\n\n"

        # Insertar en el área de texto
        self.transcriptions_text.insert(tk.END, formatted_text)
        self.transcriptions_text.see(tk.END)

        # Incrementar contador
        self.transcription_count += 1

    def update_partial_text(self, text):
        """Actualizar texto parcial en tiempo real"""
        # Esta funcionalidad se puede implementar con un área separada
        # Por ahora, solo logeamos
        pass

    def update_ui_state(self):
        """Actualizar estado de la interfaz"""
        theme = self.theme_system.get_theme()
        texts = self.theme_system.get_texts()

        if self.is_listening:
            self.start_button.configure(
                text=texts["stop"],
                bg=theme["error"]
            )
            self.update_status(texts["status_listening"])
        else:
            self.start_button.configure(
                text=texts["start"],
                bg=theme["success"]
            )
            if self.azure_ready:
                self.update_status(texts["status_ready"])
            else:
                self.update_status(texts["status_error"])

    def update_status(self, status_text):
        """Actualizar etiqueta de estado"""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=status_text)

    def update_stats_display(self):
        """Actualizar visualización de estadísticas"""
        if not hasattr(self, 'phrases_label'):
            return

        stats = self.stats_collector.stats

        # Actualizar contadores
        if hasattr(self, 'phrases_label'):
            self.phrases_label.configure(text=str(stats['phrases_count']))
        if hasattr(self, 'corrections_label'):
            self.corrections_label.configure(text=str(stats['corrections_applied']))
        if hasattr(self, 'repetitions_label'):
            self.repetitions_label.configure(text=str(stats['repetitions_detected']))

        # Actualizar tiempo de sesión
        if hasattr(self, 'session_time_label'):
            duration = stats['session_duration']
            minutes, seconds = divmod(duration, 60)
            time_str = f"{minutes:02d}:{seconds:02d}"
            self.session_time_label.configure(text=time_str)

    def start_update_loops(self):
        """Iniciar loops de actualización periódica"""

        def update_stats():
            """Actualizar estadísticas periódicamente"""
            if hasattr(self, 'stats_collector'):
                self.stats_collector.stats['session_duration'] = int(time.time() - self.session_start)
                self.update_stats_display()
            # Programar siguiente actualización
            self.root.after(1000, update_stats)

        # Iniciar actualización de estadísticas
        self.root.after(1000, update_stats)

    def clear_transcription(self):
        """Limpiar área de transcripción"""
        if messagebox.askyesno("Confirmar", "¿Limpiar toda la transcripción?"):
            self.transcriptions_text.delete(1.0, tk.END)
            self.medical_buffer = ""
            self.transcription_count = 0
            self.log_to_gui("🗑️ Transcripción limpiada")

    def save_session(self):
        """Guardar sesión actual"""
        try:
            content = self.transcriptions_text.get(1.0, tk.END)
            if not content.strip():
                messagebox.showwarning("Advertencia", "No hay contenido para guardar")
                return

            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
                initialfile=f"transcripcion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                # ✅ Cambiado de initialname a initialfile
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)

                    # Agregar estadísticas al final
                    stats = self.stats_collector.stats
                    f.write(f"\n\n--- ESTADÍSTICAS DE SESIÓN ---\n")
                    f.write(f"Frases: {stats['phrases_count']}\n")
                    f.write(f"Palabras: {stats['words_count']}\n")
                    f.write(f"Caracteres: {stats['chars_transcribed']}\n")
                    f.write(f"Correcciones aplicadas: {stats['corrections_applied']}\n")
                    f.write(f"Repeticiones detectadas: {stats['repetitions_detected']}\n")
                    f.write(f"Duración: {stats['session_duration']} segundos\n")

                self.log_to_gui(f"💾 Sesión guardada: {filename}")
                messagebox.showinfo("Éxito", f"Sesión guardada correctamente\n{filename}")

        except Exception as e:
            self.logger.error(f"Error guardando sesión: {e}")
            self.log_to_gui(f"❌ Error guardando: {e}")
            messagebox.showerror("Error", f"Error guardando sesión:\n{e}")

    def open_config(self):
        """Abrir ventana de configuración"""
        ConfigWindow(self)

    def log_to_gui(self, message):
        """Agregar mensaje al log de la GUI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"

        if hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, formatted_message)
            self.log_text.see(tk.END)

            # Mantener solo las últimas 100 líneas
            lines = self.log_text.get(1.0, tk.END).split('\n')
            if len(lines) > 100:
                self.log_text.delete(1.0, f"{len(lines) - 100}.0")

        # También enviar al logger
        self.logger.info(message.replace('🔄', '').replace('✅', '').replace('❌', '').strip())

    def on_closing(self):
        """Manejar cierre de la aplicación"""
        try:
            self.log_to_gui("🔚 Cerrando aplicación...")

            # Detener reconocimiento
            if self.is_listening:
                self.stop_recognition()

            # Guardar configuración
            self.save_config()

            # Cerrar Azure SDK
            if hasattr(self, 'speech_recognizer') and self.speech_recognizer:
                try:
                    self.speech_recognizer.stop_continuous_recognition()
                except:
                    pass

            self.logger.info("Aplicación cerrada correctamente")

        except Exception as e:
            self.logger.error(f"Error durante el cierre: {e}")
        finally:
            self.root.destroy()

    def run(self):
        """Ejecutar la aplicación"""
        try:
            self.log_to_gui(f"🚀 Iniciando Voice Bridge v{VERSION}")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Error ejecutando aplicación: {e}")
            messagebox.showerror("Error crítico", f"Error ejecutando aplicación:\n{e}")


# ===== VENTANA DE CONFIGURACIÓN =====
class ConfigWindow:
    """Ventana de configuración de Azure"""

    def __init__(self, parent):
        self.parent = parent
        self.config = parent.config.copy()
        self.create_window()

    def create_window(self):
        """Crear ventana de configuración"""
        self.window = tk.Toplevel(self.parent.root)
        self.window.title("Configuración Azure Speech")
        self.window.geometry("500x400")
        self.window.resizable(False, False)
        self.window.transient(self.parent.root)
        self.window.grab_set()

        # Aplicar tema
        theme = self.parent.theme_system.get_theme()
        self.window.configure(bg=theme["bg"])

        # Crear interfaz
        self.create_interface()

        # Centrar ventana
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")

    def create_interface(self):
        """Crear interfaz de configuración"""
        theme = self.parent.theme_system.get_theme()
        fonts = self.parent.theme_system.get_fonts()
        texts = self.parent.theme_system.get_texts()

        # Frame principal
        main_frame = tk.Frame(self.window, bg=theme["bg"])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Título
        title_label = tk.Label(
            main_frame,
            text=texts["azure_config"],
            bg=theme["bg"],
            fg=theme["accent"],
            font=fonts["heading"]
        )
        title_label.pack(pady=(0, 20))

        # === CONFIGURACIÓN AZURE ===
        # Clave API
        key_frame = tk.Frame(main_frame, bg=theme["bg"])
        key_frame.pack(fill='x', pady=5)

        tk.Label(
            key_frame,
            text=texts["azure_key"],
            bg=theme["bg"],
            fg=theme["fg"],
            font=fonts["primary"]
        ).pack(anchor='w')

        self.key_entry = tk.Entry(
            key_frame,
            bg=theme["entry_bg"],
            fg=theme["entry_fg"],
            font=fonts["primary"],
            show="*"
        )
        self.key_entry.pack(fill='x', pady=(5, 0))
        self.key_entry.insert(0, self.config.get('azure_key', ''))

        # Región
        region_frame = tk.Frame(main_frame, bg=theme["bg"])
        region_frame.pack(fill='x', pady=5)

        tk.Label(
            region_frame,
            text=texts["azure_region"],
            bg=theme["bg"],
            fg=theme["fg"],
            font=fonts["primary"]
        ).pack(anchor='w')

        self.region_var = tk.StringVar(value=self.config.get('azure_region', 'eastus'))
        region_combo = ttk.Combobox(
            region_frame,
            textvariable=self.region_var,
            values=['eastus', 'westus', 'westeurope', 'eastasia', 'southeastasia', 'northeurope'],
            state='readonly'
        )
        region_combo.pack(fill='x', pady=(5, 0))

        # Idioma
        lang_frame = tk.Frame(main_frame, bg=theme["bg"])
        lang_frame.pack(fill='x', pady=5)

        tk.Label(
            lang_frame,
            text=texts["azure_language"],
            bg=theme["bg"],
            fg=theme["fg"],
            font=fonts["primary"]
        ).pack(anchor='w')

        self.lang_var = tk.StringVar(value=self.config.get('azure_language', 'es-ES'))
        lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=['es-ES', 'en-US', 'en-GB', 'fr-FR', 'de-DE', 'it-IT', 'pt-BR'],
            state='readonly'
        )
        lang_combo.pack(fill='x', pady=(5, 0))

        # === CONFIGURACIONES AVANZADAS ===
        advanced_frame = tk.LabelFrame(
            main_frame,
            text="Configuraciones Avanzadas",
            bg=theme["bg"],
            fg=theme["fg"],
            font=fonts["primary"]
        )
        advanced_frame.pack(fill='x', pady=(20, 10))

        # Auto-corrección
        self.auto_correct_var = tk.BooleanVar(value=self.config.get('auto_correct', True))
        auto_correct_check = tk.Checkbutton(
            advanced_frame,
            text="Habilitar corrección automática",
            variable=self.auto_correct_var,
            bg=theme["bg"],
            fg=theme["fg"],
            selectcolor=theme["select_bg"],
            font=fonts["primary"]
        )
        auto_correct_check.pack(anchor='w', padx=10, pady=5)

        # TTS
        self.tts_var = tk.BooleanVar(value=self.config.get('tts_enabled', False))
        tts_check = tk.Checkbutton(
            advanced_frame,
            text="Habilitar síntesis de voz (TTS)",
            variable=self.tts_var,
            bg=theme["bg"],
            fg=theme["fg"],
            selectcolor=theme["select_bg"],
            font=fonts["primary"]
        )
        tts_check.pack(anchor='w', padx=10, pady=5)

        # Mostrar estadísticas
        self.stats_var = tk.BooleanVar(value=self.config.get('show_stats', True))
        stats_check = tk.Checkbutton(
            advanced_frame,
            text="Mostrar panel de estadísticas",
            variable=self.stats_var,
            bg=theme["bg"],
            fg=theme["fg"],
            selectcolor=theme["select_bg"],
            font=fonts["primary"]
        )
        stats_check.pack(anchor='w', padx=10, pady=5)

        # === BOTONES ===
        button_frame = tk.Frame(main_frame, bg=theme["bg"])
        button_frame.pack(fill='x', pady=(20, 0))

        # Botón probar
        test_button = tk.Button(
            button_frame,
            text=texts["test_connection"],
            command=self.test_connection,
            bg=theme["accent"],
            fg="white",
            font=fonts["primary"],
            padx=15,
            pady=8,
            relief='flat',
            cursor='hand2'
        )
        test_button.pack(side='left', padx=(0, 10))

        # Botón guardar
        save_button = tk.Button(
            button_frame,
            text=texts["save_config"],
            command=self.save_config,
            bg=theme["success"],
            fg="white",
            font=fonts["primary"],
            padx=15,
            pady=8,
            relief='flat',
            cursor='hand2'
        )
        save_button.pack(side='left', padx=(0, 10))

        # Botón cancelar
        cancel_button = tk.Button(
            button_frame,
            text=texts["cancel"],
            command=self.window.destroy,
            bg=theme["button_bg"],
            fg=theme["button_fg"],
            font=fonts["primary"],
            padx=15,
            pady=8,
            relief='flat',
            cursor='hand2'
        )
        cancel_button.pack(side='right')

    def test_connection(self):
        """Probar conexión con Azure"""
        try:
            key = self.key_entry.get().strip()
            region = self.region_var.get()
            language = self.lang_var.get()

            if not key or not region:
                messagebox.showerror("Error", "Por favor complete todos los campos")
                return

            # Mostrar mensaje de prueba
            self.parent.log_to_gui("🔍 Probando conexión Azure...")

            # Crear configuración temporal
            temp_config = speechsdk.SpeechConfig(subscription=key, region=region)
            temp_config.speech_recognition_language = language

            # Crear recognizer temporal
            temp_recognizer = speechsdk.SpeechRecognizer(speech_config=temp_config)

            messagebox.showinfo("Éxito", "✅ Conexión exitosa con Azure Speech")
            self.parent.log_to_gui("✅ Prueba de conexión exitosa")

        except Exception as e:
            error_msg = f"Error probando conexión: {e}"
            messagebox.showerror("Error", error_msg)
            self.parent.log_to_gui(f"❌ {error_msg}")

    def save_config(self):
        """Guardar configuración"""
        try:
            # Validar campos
            key = self.key_entry.get().strip()
            region = self.region_var.get()
            language = self.lang_var.get()

            if not key or not region:
                messagebox.showerror("Error", "Por favor complete todos los campos obligatorios")
                return

            # Actualizar configuración
            self.config.update({
                'azure_key': key,
                'azure_region': region,
                'azure_language': language,
                'auto_correct': self.auto_correct_var.get(),
                'tts_enabled': self.tts_var.get(),
                'show_stats': self.stats_var.get()
            })

            # Aplicar a la aplicación principal
            self.parent.config.update(self.config)
            self.parent.save_config()

            # Mostrar mensaje de éxito
            messagebox.showinfo("Éxito", "Configuración guardada correctamente")
            self.parent.log_to_gui("💾 Configuración guardada")

            # Cerrar ventana
            self.window.destroy()

            # Reconfigurar Azure si es necesario
            if not self.parent.azure_ready:
                self.parent.root.after(1000, self.parent.delayed_azure_setup)

        except Exception as e:
            error_msg = f"Error guardando configuración: {e}"
            messagebox.showerror("Error", error_msg)
            self.parent.log_to_gui(f"❌ {error_msg}")


# ===== FUNCIÓN PRINCIPAL =====
def main():
    """Función principal"""
    try:
        # Configurar logging antes de crear la aplicación
        logger = setup_logger()
        logger.info(f"=== INICIANDO VOICE BRIDGE v{VERSION} ===")

        # Verificar dependencias críticas
        try:
            import azure.cognitiveservices.speech as speechsdk
            logger.info("✅ Azure Speech SDK disponible")
        except ImportError:
            logger.error("❌ Azure Speech SDK no encontrado")
            messagebox.showerror("Error",
                                 "Azure Speech SDK no está instalado.\n\nInstale con: pip install azure-cognitiveservices-speech")
            return

        # Crear y ejecutar aplicación
        app = VoiceBridge224()
        app.run()

    except Exception as e:
        logger.error(f"Error crítico en main: {e}")
        messagebox.showerror("Error Crítico", f"Error crítico:\n{e}")


if __name__ == "__main__":
    main()