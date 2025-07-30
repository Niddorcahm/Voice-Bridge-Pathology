#!/usr/bin/env python3
"""
Voice Bridge v2.1 - Sistema de Dictado Mejorado
Mejoras principales:
- Selector de tipo de micrófono en GUI
- Anti-acoplamiento inteligente según tipo de mic
- Timeout de dictado corregido (inicia con primera palabra)
- Mejor manejo de reconocimiento continuo
- Fix para frases cortadas
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
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
from datetime import datetime
from pathlib import Path
import subprocess
import platform
from enum import Enum
from collections import deque

# Configurar pyautogui para seguridad
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

class DictationMode(Enum):
    """Estados del modo de dictado"""
    WAITING = "waiting"          # Esperando comando
    RECORDING = "recording"      # Grabando dictado
    PROCESSING = "processing"    # Procesando para enviar

class MicrophoneType(Enum):
    """Tipos de micrófono para anti-acoplamiento"""
    AMBIENT = "ambient"          # Micrófono ambiental/solapa
    HEADSET = "headset"          # Auriculares con micrófono
    DIRECTIONAL = "directional"  # Micrófono direccional/boom
    BUILTIN = "builtin"          # Micrófono integrado laptop

class VoiceBridgeV21:
    def __init__(self):
        """Inicializar Voice Bridge v2.1 con mejoras"""
        self.setup_logging()
        self.logger.info("=== Iniciando Voice Bridge v2.1 ===")
        
        # Cargar configuración
        self.config = self.load_config()
        
        # Estado del sistema
        self.dictation_mode = DictationMode.WAITING
        self.dictation_buffer = []
        self.is_listening = False
        self.is_speaking = False
        self.recognition_paused = False
        self.was_listening = False  # Para restaurar estado después de TTS
        self.last_recognition_time = time.time()
        
        # Variables mejoradas para timeout de dictado
        self.dictation_timeout_seconds = int(self.config.get('dictation_timeout_seconds', '8'))
        self.dictation_timeout_timer = None
        self.last_dictation_activity = None
        self.timeout_warning_given = False
        self.waiting_for_first_word = False  # Nueva variable para esperar primera palabra
        
        # Buffer para detección de repeticiones
        self.recent_phrases = deque(maxlen=5)
        
        # Colas de comunicación
        self.transcription_queue = queue.Queue()
        self.command_queue = queue.Queue()
        
        # Setup componentes
        self.setup_azure_speech()
        self.setup_gui()
        self.load_medical_terms()
        self.setup_hotkeys()
        
        # Información de sesión
        self.session_start = datetime.now()
        self.transcription_count = 0
        
        self.logger.info("Voice Bridge v2.1 iniciado correctamente")
        self.log_to_gui("🚀 Voice Bridge v2.1 - Anti-acoplamiento mejorado")
    
    def setup_logging(self):
        """Configurar sistema de logging"""
        log_dir = Path.home() / "voice-bridge-claude" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"voice_bridge_v21_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self):
        """Cargar configuración con valores para v2.1"""
        config = configparser.ConfigParser()
        
        # Valores por defecto optimizados v2.1
        default_config = {
            'azure_speech_key': os.environ.get('AZURE_SPEECH_KEY', ''),
            'azure_region': os.environ.get('AZURE_SPEECH_REGION', 'eastus'),
            'speech_language': os.environ.get('SPEECH_LANGUAGE', 'es-CO'),
            'tts_voice': os.environ.get('TTS_VOICE', 'es-CO-SalomeNeural'),
            'hotkey_start': 'ctrl+shift+v',
            'hotkey_stop': 'ctrl+shift+s',
            'hotkey_emergency': 'ctrl+shift+x',
            'auto_send_to_claude': 'false',
            'claude_window_title': 'Claude',
            'medical_mode': 'true',
            'confidence_threshold': '0.5',
            'tts_enabled': 'true',
            'claude_activation_delay': '0.5',
            # Opciones v2
            'dictation_mode': 'continuous',
            'anti_coupling': 'true',
            'tts_during_dictation': 'false',
            'auto_correct_medical': 'true',
            'dictation_timeout_seconds': '8',
            'timeout_warning_seconds': '3',
            'timeout_audio_warning': 'true',
            # NUEVO v2.1
            'microphone_type': 'ambient',  # ambient, headset, directional, builtin
            'auto_mute_on_tts': 'true',
            'tts_end_delay': '0.5',
            'first_word_timeout': '5',  # Segundos para esperar primera palabra
        }
        
        config_file = Path.home() / "voice-bridge-claude" / "config" / "voice_bridge_config_v21.ini"
        if config_file.exists():
            config.read(config_file)
            self.logger.info(f"Configuración v2.1 cargada desde: {config_file}")
        else:
            # Intentar cargar v2 y actualizar
            config_v2 = Path.home() / "voice-bridge-claude" / "config" / "voice_bridge_config_v2.ini"
            if config_v2.exists():
                config.read(config_v2)
                # Agregar nuevas opciones v2.1
                for key, value in default_config.items():
                    if key not in config['DEFAULT']:
                        config['DEFAULT'][key] = value
            else:
                config['DEFAULT'] = default_config
            
            # Guardar como v2.1
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                config.write(f)
            self.logger.info(f"Archivo de configuración v2.1 creado: {config_file}")
        
        return config['DEFAULT']
    
    def setup_azure_speech(self):
        """Configurar Azure Speech con optimizaciones v2.1"""
        speech_key = self.config['azure_speech_key']
        region = self.config['azure_region']
        
        if not speech_key:
            raise ValueError("❌ AZURE_SPEECH_KEY no configurado")
        
        self.logger.info(f"Configurando Azure Speech v2.1 - Región: {region}")
        
        # Configuración de Azure Speech
        self.speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=region
        )
        
        # Configurar idioma y voz
        self.speech_config.speech_recognition_language = self.config['speech_language']
        self.speech_config.speech_synthesis_voice_name = self.config['tts_voice']
        
        # CONFIGURACIÓN OPTIMIZADA PARA DICTADO CONTINUO
        if self.config.get('dictation_mode') == 'continuous':
            # Usar modo DICTATION
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_RecoMode,
                "DICTATION"
            )
            
            # TIMEOUTS OPTIMIZADOS v2.1
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
                "30000"  # 30 segundos para empezar (muy generoso)
            )
            
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs,
                "20000"  # 20 segundos (manejamos timeout nosotros)
            )
            
            self.speech_config.set_property(
                speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs,
                "3000"  # 3 segundos entre palabras
            )
            
            # Mejorar reconocimiento continuo
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode,
                "Continuous"
            )
            
            # NUEVO v2.1: Configuración según tipo de micrófono
            mic_type = self.config.get('microphone_type', 'ambient')
            if mic_type in ['headset', 'directional']:
                # Menor supresión de ruido para headsets
                self.speech_config.set_property(
                    speechsdk.PropertyId.SpeechServiceConnection_EndpointId,
                    "LowNoiseSuppression"
                )
            
            self.logger.info(f"✅ Modo dictado continuo configurado - Micrófono: {mic_type}")
        
        # Audio config
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
        
        self.logger.info("✅ Azure Speech Services v2.1 configurado correctamente")
    
    def setup_speech_callbacks(self):
        """Configurar callbacks mejorados v2.1"""
        
        def on_recognized(evt):
            """Texto reconocido final"""
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text = evt.result.text.strip()
                if text and not self.recognition_paused and not self.is_speaking:
                    # Actualizar tiempo de última recognición
                    self.last_recognition_time = time.time()
                    
                    # SIEMPRE verificar comandos primero
                    if self.check_and_execute_command(text):
                        return  # Comando ejecutado
                    
                    # Procesar según modo
                    if self.dictation_mode == DictationMode.WAITING:
                        # Modo normal
                        self.transcription_queue.put({
                            'type': 'final',
                            'text': text,
                            'timestamp': datetime.now(),
                            'mode': 'single'
                        })
                    elif self.dictation_mode == DictationMode.RECORDING:
                        # Modo dictado: agregar al buffer
                        self.add_to_dictation_buffer(text)
        
        def on_recognizing(evt):
            """Texto parcial durante reconocimiento"""
            if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
                text = evt.result.text.strip()
                if text and not self.recognition_paused and not self.is_speaking:
                    # Detectar comandos urgentes en texto parcial
                    if self.dictation_mode == DictationMode.RECORDING:
                        text_lower = text.lower()
                        urgent_commands = ["fin dictado", "cancelar dictado", "parar dictado"]
                        for cmd in urgent_commands:
                            if cmd in text_lower and len(text_lower) - len(cmd) < 5:
                                self.partial_command_detected = cmd
                                self.update_partial_text(f"🛑 ¿{cmd}? (esperando confirmación...)")
                                return
                    
                    self.update_partial_text(text)
        
        def on_error(evt):
            """Error en reconocimiento"""
            if not self.recognition_paused:
                error_msg = f"Error de reconocimiento: {evt.result.error_details}"
                self.logger.error(error_msg)
                self.log_to_gui(f"❌ {error_msg}")
        
        # Conectar eventos
        self.speech_recognizer.recognized.connect(on_recognized)
        self.speech_recognizer.recognizing.connect(on_recognizing)
        self.speech_recognizer.canceled.connect(on_error)
    
    def speak_text_safe(self, text):
        """TTS con anti-acoplamiento inteligente v2.1"""
        if not self.config.getboolean('tts_enabled'):
            return
        
        # Determinar si necesita mutear según tipo de micrófono
        mic_type = self.config.get('microphone_type', 'ambient')
        needs_mute = mic_type in ['ambient', 'builtin', 'directional']
        
        self.logger.info(f"TTS: Micrófono tipo '{mic_type}', mutear: {needs_mute}")
        
        # Thread para TTS
        def tts_thread():
            try:
                self.is_speaking = True
                
                # Guardar estado de reconocimiento
                self.was_listening = self.is_listening
                
                # Anti-acoplamiento según tipo de micrófono
                if needs_mute and self.config.getboolean('anti_coupling'):
                    # Pausar reconocimiento
                    self.pause_recognition()
                    
                    # Detener reconocimiento de Azure completamente
                    if self.is_listening:
                        try:
                            self.speech_recognizer.stop_continuous_recognition_async().get()
                            self.is_listening = False
                            time.sleep(0.2)  # Esperar que se detenga
                        except Exception as e:
                            self.logger.error(f"Error deteniendo reconocimiento: {e}")
                    
                    # Mutear micrófono a nivel sistema (Linux)
                    if platform.system() == 'Linux':
                        try:
                            # Mutear todas las fuentes
                            subprocess.run(['pactl', 'set-source-mute', '@DEFAULT_SOURCE@', '1'], 
                                         capture_output=True)
                            self.logger.info("Micrófono muteado")
                        except Exception as e:
                            self.logger.error(f"Error muteando micrófono: {e}")
                
                # Realizar TTS
                result = self.speech_synthesizer.speak_text_async(text).get()
                
                if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
                    self.logger.warning(f"Error TTS: {result.reason}")
                
                # Esperar que termine el audio
                tts_delay = float(self.config.get('tts_end_delay', '0.5'))
                time.sleep(tts_delay)
                
            except Exception as e:
                self.logger.error(f"Error en TTS: {e}")
            finally:
                self.is_speaking = False
                
                # Restaurar micrófono y reconocimiento
                if needs_mute and self.config.getboolean('anti_coupling'):
                    # Desmutear micrófono
                    if platform.system() == 'Linux':
                        try:
                            subprocess.run(['pactl', 'set-source-mute', '@DEFAULT_SOURCE@', '0'], 
                                         capture_output=True)
                            self.logger.info("Micrófono restaurado")
                        except:
                            pass
                    
                    # Esperar un momento antes de reanudar
                    time.sleep(0.3)
                    
                    # Reanudar reconocimiento si estaba activo
                    if self.was_listening:
                        try:
                            self.speech_recognizer.start_continuous_recognition_async()
                            self.is_listening = True
                            self.logger.info("Reconocimiento reanudado")
                        except Exception as e:
                            self.logger.error(f"Error reanudando reconocimiento: {e}")
                
                # Reanudar procesamiento
                self.resume_recognition()
        
        threading.Thread(target=tts_thread, daemon=True).start()
    
    def start_dictation_mode(self):
        """Iniciar modo dictado con timeout mejorado v2.1"""
        if self.dictation_mode != DictationMode.RECORDING:
            self.dictation_mode = DictationMode.RECORDING
            self.dictation_buffer.clear()
            
            # NUEVO v2.1: Esperar primera palabra antes de iniciar timeout
            self.waiting_for_first_word = True
            self.last_dictation_activity = None
            self.timeout_warning_given = False
            
            # NO iniciar timer aquí
            if self.dictation_timeout_timer:
                self.root.after_cancel(self.dictation_timeout_timer)
                self.dictation_timeout_timer = None
            
            self.update_dictation_status("🔴 DICTADO ACTIVO - Esperando primera palabra...", "red")
            self.log_to_gui("📝 Modo dictado iniciado - Comience a hablar...")
            
            # Feedback de voz
            if self.config.getboolean('tts_enabled'):
                self.speak_text_safe("Dictado iniciado, puede comenzar")
    
    def add_to_dictation_buffer(self, text):
        """Agregar texto al buffer con inicio de timeout mejorado"""
        # Verificar comandos primero
        text_lower = text.lower().strip()
        command_keywords = [
            "fin dictado", "fin del dictado", "finalizar dictado", 
            "terminar dictado", "parar dictado", "detener dictado",
            "cancelar dictado", "cancelar", "borrar dictado",
            "enviar a claude", "enviar dictado"
        ]
        
        for cmd in command_keywords:
            if cmd in text_lower:
                text_words = text_lower.split()
                cmd_words = cmd.split()
                
                if all(word in text_words for word in cmd_words):
                    self.logger.info(f"🎯 COMANDO DETECTADO EN BUFFER: {cmd}")
                    self.log_to_gui(f"🎯 Comando detectado: {cmd}")
                    
                    if "fin" in cmd or "terminar" in cmd or "finalizar" in cmd or "parar" in cmd or "detener" in cmd:
                        self.root.after_idle(self.end_dictation_mode)
                        return
                    elif "cancelar" in cmd:
                        self.root.after_idle(self.cancel_dictation)
                        return
                    elif "enviar" in cmd:
                        self.root.after_idle(self.send_buffered_dictation)
                        return
        
        # NUEVO v2.1: Si es la primera palabra, ahora sí iniciar timeout
        if self.waiting_for_first_word:
            self.waiting_for_first_word = False
            self.last_dictation_activity = time.time()
            self.start_dictation_timeout_monitor()
            self.update_dictation_status("🔴 DICTADO ACTIVO", "red")
            self.log_to_gui("✅ Primera palabra detectada - Timeout iniciado")
        else:
            # Resetear timeout con cada nueva entrada
            self.last_dictation_activity = time.time()
            self.timeout_warning_given = False
        
        # Restaurar indicador normal si estaba en warning
        if self.dictation_mode == DictationMode.RECORDING and not self.waiting_for_first_word:
            self.update_dictation_status("🔴 DICTADO ACTIVO", "red")
        
        # Aplicar correcciones médicas
        if self.config.getboolean('auto_correct_medical'):
            text = self.apply_medical_corrections(text)
        
        # Detectar y evitar repeticiones
        if not self.is_repetition(text):
            self.dictation_buffer.append(text)
            self.update_dictation_buffer_display()
            
            if len(self.dictation_buffer) % 5 == 0:
                self.flash_buffer_indicator()
            
            self.logger.info(f"Buffer de dictado: {len(self.dictation_buffer)} segmentos")
        else:
            self.logger.debug(f"Repetición ignorada: {text[:30]}...")
    
    def start_dictation_timeout_monitor(self):
        """Monitor de timeout mejorado v2.1"""
        if self.dictation_timeout_timer:
            self.root.after_cancel(self.dictation_timeout_timer)
        
        self.dictation_timeout_timer = self.root.after(1000, self.check_dictation_timeout)
    
    def check_dictation_timeout(self):
        """Verificar timeout con lógica mejorada"""
        if self.dictation_mode != DictationMode.RECORDING:
            if hasattr(self, 'timeout_progress'):
                self.timeout_progress.grid_remove()
            return
        
        # Si estamos esperando primera palabra, no hacer timeout
        if self.waiting_for_first_word:
            # Verificar timeout de primera palabra (más generoso)
            first_word_timeout = int(self.config.get('first_word_timeout', '5'))
            # Por ahora, solo continuar monitoreando
            self.dictation_timeout_timer = self.root.after(1000, self.check_dictation_timeout)
            return
        
        # Lógica normal de timeout
        if hasattr(self, 'timeout_progress'):
            self.timeout_progress.grid()
            
            if self.last_dictation_activity:
                elapsed = time.time() - self.last_dictation_activity
                remaining = max(0, self.dictation_timeout_seconds - elapsed)
                self.timeout_progress['value'] = remaining
        
        if self.last_dictation_activity:
            inactive_seconds = time.time() - self.last_dictation_activity
            remaining = max(0, self.dictation_timeout_seconds - inactive_seconds)
            
            if remaining <= 3 and not self.timeout_warning_given:
                self.update_dictation_status(
                    f"🟡 DICTADO ACTIVO - Finalizando en {int(remaining)}s...", 
                    "orange"
                )
                
                if remaining <= 2 and not self.timeout_warning_given:
                    self.timeout_warning_given = True
                    if self.config.getboolean('tts_enabled'):
                        self.speak_text_safe("Finalizando dictado")
            
            if inactive_seconds >= self.dictation_timeout_seconds:
                self.logger.info(f"Auto-finalizando dictado por timeout ({self.dictation_timeout_seconds}s)")
                self.auto_end_dictation_mode()
                return
        
        self.dictation_timeout_timer = self.root.after(1000, self.check_dictation_timeout)
    
    def setup_gui(self):
        """GUI mejorada v2.1 con selector de micrófono"""
        self.root = tk.Tk()
        self.root.title("Voice Bridge v2.1 - Patología Molecular")
        self.root.geometry("750x650")
        
        style = ttk.Style()
        style.configure("DictationStatus.TLabel", font=("Arial", 14, "bold"))
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Estado del sistema
        status_frame = ttk.LabelFrame(main_frame, text="Estado del Sistema", padding="10")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Indicador de modo dictado
        self.dictation_status_label = ttk.Label(
            status_frame, 
            text="🟢 ESPERANDO COMANDO",
            style="DictationStatus.TLabel"
        )
        self.dictation_status_label.grid(row=0, column=0, pady=5)
        
        # Info de sesión
        self.session_info_var = tk.StringVar()
        ttk.Label(status_frame, textvariable=self.session_info_var).grid(row=1, column=0)
        
        # Barra de progreso para timeout
        self.timeout_progress = ttk.Progressbar(
            status_frame,
            length=300,
            mode='determinate',
            maximum=self.dictation_timeout_seconds
        )
        self.timeout_progress.grid(row=2, column=0, pady=5)
        self.timeout_progress.grid_remove()
        
        # NUEVO v2.1: Frame de configuración de micrófono
        mic_frame = ttk.LabelFrame(main_frame, text="Configuración de Micrófono", padding="10")
        mic_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Selector de tipo de micrófono
        ttk.Label(mic_frame, text="Tipo de micrófono:").grid(row=0, column=0, padx=(0, 10))
        
        self.mic_type_var = tk.StringVar(value=self.config.get('microphone_type', 'ambient'))
        mic_combo = ttk.Combobox(
            mic_frame, 
            textvariable=self.mic_type_var,
            values=['ambient', 'headset', 'directional', 'builtin'],
            state='readonly',
            width=15
        )
        mic_combo.grid(row=0, column=1)
        mic_combo.bind('<<ComboboxSelected>>', self.on_mic_type_changed)
        
        # Descripción del tipo seleccionado
        self.mic_description_var = tk.StringVar()
        self.update_mic_description()
        ttk.Label(
            mic_frame, 
            textvariable=self.mic_description_var,
            font=("Arial", 9, "italic")
        ).grid(row=1, column=0, columnspan=2, pady=(5, 0))
        
        # Indicador de anti-acoplamiento
        self.anti_coupling_indicator = ttk.Label(
            mic_frame,
            text="",
            font=("Arial", 9)
        )
        self.anti_coupling_indicator.grid(row=2, column=0, columnspan=2)
        self.update_anti_coupling_indicator()
        
        # Controles
        controls_frame = ttk.LabelFrame(main_frame, text="Controles", padding="10")
        controls_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Botones de control
        button_frame = ttk.Frame(controls_frame)
        button_frame.grid(row=0, column=0, columnspan=2)
        
        self.start_button = ttk.Button(
            button_frame, 
            text="🎤 Iniciar Reconocimiento\n(Ctrl+Shift+V)", 
            command=self.start_recognition
        )
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(
            button_frame, 
            text="⏹️ Detener\n(Ctrl+Shift+S)", 
            command=self.stop_recognition,
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=5)
        
        ttk.Button(
            button_frame,
            text="📝 Inicio Dictado",
            command=self.start_dictation_mode
        ).grid(row=0, column=2, padx=5)
        
        ttk.Button(
            button_frame,
            text="✓ Fin Dictado",
            command=self.end_dictation_mode
        ).grid(row=0, column=3, padx=5)
        
        # Buffer de dictado
        buffer_frame = ttk.LabelFrame(main_frame, text="Buffer de Dictado", padding="5")
        buffer_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.dictation_buffer_text = scrolledtext.ScrolledText(
            buffer_frame, 
            height=3, 
            font=("Arial", 11),
            bg="lightyellow",
            wrap=tk.WORD
        )
        self.dictation_buffer_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Texto parcial
        partial_frame = ttk.LabelFrame(main_frame, text="Reconocimiento Actual", padding="5")
        partial_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.partial_text_var = tk.StringVar()
        ttk.Label(
            partial_frame, 
            textvariable=self.partial_text_var,
            foreground="blue",
            font=("Arial", 10, "italic")
        ).grid(row=0, column=0)
        
        # Transcripciones
        trans_frame = ttk.LabelFrame(main_frame, text="Transcripciones", padding="5")
        trans_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.transcription_text = scrolledtext.ScrolledText(
            trans_frame,
            height=8,
            font=("Arial", 10)
        )
        self.transcription_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Botones de transcripción
        trans_buttons = ttk.Frame(trans_frame)
        trans_buttons.grid(row=1, column=0, pady=5)
        
        ttk.Button(trans_buttons, text="📤 Enviar a Claude", 
                  command=self.send_to_claude).grid(row=0, column=0, padx=2)
        ttk.Button(trans_buttons, text="🗑️ Limpiar", 
                  command=self.clear_transcriptions).grid(row=0, column=1, padx=2)
        ttk.Button(trans_buttons, text="💾 Guardar", 
                  command=self.save_transcriptions).grid(row=0, column=2, padx=2)
        
        # Opciones
        options_frame = ttk.LabelFrame(main_frame, text="Opciones", padding="5")
        options_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.auto_send_var = tk.BooleanVar(value=self.config.getboolean('auto_send_to_claude'))
        ttk.Checkbutton(options_frame, text="Envío automático a Claude", 
                       variable=self.auto_send_var).grid(row=0, column=0, sticky=tk.W)
        
        self.tts_enabled_var = tk.BooleanVar(value=self.config.getboolean('tts_enabled'))
        ttk.Checkbutton(options_frame, text="Respuestas por voz (TTS)", 
                       variable=self.tts_enabled_var).grid(row=0, column=1, sticky=tk.W)
        
        # Log del sistema
        log_frame = ttk.LabelFrame(main_frame, text="Log del Sistema", padding="5")
        log_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=3,
            font=("Courier", 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Configurar pesos
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # Cerrar ventana
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Iniciar procesamiento
        self.root.after(100, self.process_queues)
        self.root.after(1000, self.update_session_info)
    
    def on_mic_type_changed(self, event=None):
        """Manejar cambio de tipo de micrófono"""
        new_type = self.mic_type_var.get()
        self.config['microphone_type'] = new_type
        self.save_config()
        self.update_mic_description()
        self.update_anti_coupling_indicator()
        self.log_to_gui(f"🎤 Tipo de micrófono cambiado a: {new_type}")
    
    def update_mic_description(self):
        """Actualizar descripción del micrófono"""
        descriptions = {
            'ambient': "Micrófono ambiental o de solapa - Se muteará durante TTS",
            'headset': "Auriculares con micrófono - No requiere muteo",
            'directional': "Micrófono direccional/boom - Se muteará durante TTS",
            'builtin': "Micrófono integrado del equipo - Se muteará durante TTS"
        }
        mic_type = self.mic_type_var.get()
        self.mic_description_var.set(descriptions.get(mic_type, ""))
    
    def update_anti_coupling_indicator(self):
        """Actualizar indicador de anti-acoplamiento"""
        mic_type = self.mic_type_var.get()
        needs_mute = mic_type in ['ambient', 'builtin', 'directional']
        
        if needs_mute:
            self.anti_coupling_indicator.config(
                text="⚠️ Anti-acoplamiento ACTIVO - El micrófono se muteará durante TTS",
                foreground="orange"
            )
        else:
            self.anti_coupling_indicator.config(
                text="✅ Anti-acoplamiento NO requerido para este tipo de micrófono",
                foreground="green"
            )
    
    def save_config(self):
        """Guardar configuración actual"""
        config = configparser.ConfigParser()
        config['DEFAULT'] = self.config
        
        config_file = Path.home() / "voice-bridge-claude" / "config" / "voice_bridge_config_v21.ini"
        with open(config_file, 'w') as f:
            config.write(f)
    
    def pause_recognition(self):
        """Pausar temporalmente el reconocimiento"""
        self.recognition_paused = True
        self.logger.debug("Reconocimiento pausado")
    
    def resume_recognition(self):
        """Reanudar el reconocimiento"""
        self.recognition_paused = False
        self.logger.debug("Reconocimiento reanudado")
    
    def check_and_execute_command(self, text):
        """Verificar y ejecutar comandos de voz"""
        text_lower = text.lower().strip()
        
        command_mappings = {
            ("inicio dictado", "iniciar dictado", "claude inicio dictado", "empezar dictado"): 
                self.start_dictation_mode,
            
            ("fin dictado", "fin del dictado", "finalizar dictado", "terminar dictado", 
             "claude fin dictado", "parar dictado", "detener dictado"): 
                self.end_dictation_mode,
            
            ("cancelar dictado", "cancelar", "claude cancelar", "borrar dictado"): 
                self.cancel_dictation,
            
            ("enviar a claude", "enviar dictado", "claude enviar"): 
                self.send_buffered_dictation,
            
            ("repetir última", "repetir ultimo", "claude repetir"): 
                self.repeat_last_transcription,
            
            ("estado del sistema", "claude estado", "como estás"): 
                self.speak_system_status,
        }
        
        for command_group, action in command_mappings.items():
            for command in command_group:
                if command in text_lower:
                    confidence = self.calculate_command_confidence(text_lower, command)
                    
                    if confidence > 0.7:
                        self.logger.info(f"Comando ejecutado: {command} (confianza: {confidence:.2f})")
                        self.flash_command_indicator(command)
                        
                        try:
                            action()
                            return True
                        except Exception as e:
                            self.logger.error(f"Error ejecutando comando {command}: {e}")
                            self.log_to_gui(f"❌ Error en comando: {e}")
                    else:
                        self.logger.debug(f"Comando detectado pero confianza baja: {command} ({confidence:.2f})")
        
        return False
    
    def calculate_command_confidence(self, text, command):
        """Calcular confianza del comando"""
        text_words = text.split()
        command_words = command.split()
        
        if text == command:
            return 1.0
        
        if text.startswith(command) or text.endswith(command):
            extra_words = len(text_words) - len(command_words)
            return max(0.8 - (extra_words * 0.1), 0.5)
        
        if command in text:
            return 0.4
        
        return 0.0
    
    def auto_end_dictation_mode(self):
        """Finalizar dictado automáticamente por timeout"""
        if self.dictation_mode == DictationMode.RECORDING:
            self.log_to_gui("⏱️ Dictado finalizado automáticamente por timeout")
            self.end_dictation_mode()
            
            if self.config.getboolean('tts_enabled') and self.dictation_buffer:
                count = len(self.dictation_buffer)
                self.speak_text_safe(f"Timeout. Dictado con {count} segmentos")
    
    def end_dictation_mode(self):
        """Finalizar modo dictado y procesar buffer"""
        if self.dictation_mode == DictationMode.RECORDING:
            if self.dictation_timeout_timer:
                self.root.after_cancel(self.dictation_timeout_timer)
                self.dictation_timeout_timer = None
            
            self.dictation_mode = DictationMode.PROCESSING
            self.update_dictation_status("⏸️ PROCESANDO", "yellow")
            
            if self.dictation_buffer:
                full_text = " ".join(self.dictation_buffer)
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.transcription_text.insert(tk.END, f"[{timestamp}] {full_text}\n")
                self.transcription_text.see(tk.END)
                
                if self.config.getboolean('auto_send_to_claude'):
                    self.send_text_to_claude(full_text)
                else:
                    self.show_dictation_preview(full_text)
                
                self.transcription_count += 1
                
            self.dictation_mode = DictationMode.WAITING
            self.update_dictation_status("🟢 ESPERANDO", "green")
            
            self.last_dictation_activity = None
            self.timeout_warning_given = False
            self.waiting_for_first_word = False
            
            if hasattr(self, 'timeout_progress'):
                self.timeout_progress.grid_remove()
            
            if self.config.getboolean('tts_enabled'):
                self.speak_text_safe("Dictado finalizado")
    
    def apply_medical_corrections(self, text):
        """Aplicar correcciones automáticas a términos médicos"""
        corrections = {
            "context ureasa": "test de ureasa",
            "contexturasa": "test de ureasa",
            "teste ureasa": "test de ureasa",
            "testuresa": "test de ureasa",
            "testeureasa": "test de ureasa",
            "bimbo": "veo",
            "observó": "observo",
            "californes": "caliciformes",
            "empleomorfismo": "pleomorfismo",
            "vasocelular": "basocelular",
            "cloud": "Claude",
            "ninfoplasmoitario": "linfoplasmocitario",
            "linfoplasmositario": "linfoplasmocitario",
            "el ecobacter": "helicobacter",
            "el hipobacter": "helicobacter",
            "hijo barter": "helicobacter",
            "el cobacter": "helicobacter",
            "ecobarter": "helicobacter",
            "santomatoso": "xantomatoso",
            "anterial": "antral",
            "dudenal": "duodenal",
            "vellocitaria": "vellositaria",
            "elungación": "elongación",
            "el hongado": "elongado",
            "lezatrófica": "es atrófica",
            "coilosítico": "coilocítico",
            "drales": "antrales",
        }
        
        corrected = text
        corrections_made = []
        
        for wrong, right in corrections.items():
            if wrong in corrected.lower():
                corrected = corrected.lower().replace(wrong, right)
                corrections_made.append(f"{wrong} → {right}")
        
        if corrections_made:
            self.logger.info(f"Correcciones aplicadas: {', '.join(corrections_made)}")
            if len(corrections_made) <= 2:
                self.log_to_gui(f"✏️ Corregido: {', '.join(corrections_made)}")
        
        return corrected
    
    def is_repetition(self, text):
        """Detectar si el texto es una repetición reciente"""
        normalized = text.lower().strip()
        
        # NUNCA marcar comandos como repetición
        command_keywords = [
            "fin dictado", "fin del dictado", "finalizar dictado", 
            "terminar dictado", "cancelar dictado", "enviar", 
            "claude", "inicio dictado", "parar dictado"
        ]
        
        for cmd in command_keywords:
            if cmd in normalized:
                self.logger.debug(f"Comando detectado, NO es repetición: {cmd}")
                return False
        
        if len(normalized.split()) <= 2:
            return False
        
        for recent in self.recent_phrases:
            similarity = self.calculate_similarity(normalized, recent)
            if similarity > 0.85:
                self.logger.warning(f"Repetición detectada: {text[:30]}...")
                return True
        
        self.recent_phrases.append(normalized)
        return False
    
    def calculate_similarity(self, text1, text2):
        """Calcular similitud simple entre dos textos"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def flash_command_indicator(self, command):
        """Mostrar indicador visual de comando reconocido"""
        original_text = self.dictation_status_label.cget("text")
        original_color = self.dictation_status_label.cget("foreground")
        
        self.dictation_status_label.config(
            text=f"✓ COMANDO: {command.upper()}", 
            foreground="blue"
        )
        
        self.root.after(1000, lambda: self.dictation_status_label.config(
            text=original_text, 
            foreground=original_color
        ))
    
    def flash_buffer_indicator(self):
        """Indicador sutil de que el buffer está creciendo"""
        original_bg = self.dictation_buffer_text.cget("bg")
        self.dictation_buffer_text.config(bg="lightgreen")
        self.root.after(200, lambda: self.dictation_buffer_text.config(bg=original_bg))
    
    def repeat_last_transcription(self):
        """Repetir última transcripción por voz"""
        if self.dictation_buffer and self.dictation_mode == DictationMode.RECORDING:
            last_segment = self.dictation_buffer[-1]
            self.speak_text_safe(f"Último segmento: {last_segment}")
        else:
            all_text = self.transcription_text.get("end-2l", "end-1l").strip()
            if all_text and "]" in all_text:
                last_text = all_text.split("]", 1)[1].strip()
                self.speak_text_safe(f"Última transcripción: {last_text}")
    
    def speak_system_status(self):
        """Hablar estado del sistema"""
        mode_text = {
            DictationMode.WAITING: "esperando comandos",
            DictationMode.RECORDING: f"dictando, {len(self.dictation_buffer)} segmentos",
            DictationMode.PROCESSING: "procesando"
        }
        
        status = f"Sistema en modo {mode_text[self.dictation_mode]}"
        if self.is_listening:
            status += ", reconocimiento activo"
        
        self.speak_text_safe(status)
    
    def update_dictation_status(self, text, color="black"):
        """Actualizar indicador de estado de dictado"""
        try:
            if hasattr(self, 'dictation_status_label'):
                self.dictation_status_label.config(text=text)
                
                if color == "red":
                    self.dictation_status_label.config(foreground="red")
                elif color == "orange":
                    self.dictation_status_label.config(foreground="orange")
                elif color == "yellow":
                    self.dictation_status_label.config(foreground="#DAA520")
                elif color == "green":
                    self.dictation_status_label.config(foreground="green")
                else:
                    self.dictation_status_label.config(foreground="black")
                
                self.dictation_status_label.update_idletasks()
                self.root.update_idletasks()
                
        except Exception as e:
            self.logger.error(f"Error actualizando estado GUI: {e}")
    
    def update_dictation_buffer_display(self):
        """Actualizar visualización del buffer de dictado"""
        self.dictation_buffer_text.delete(1.0, tk.END)
        if self.dictation_buffer:
            recent = self.dictation_buffer[-3:]
            display_text = " ... ".join(recent)
            self.dictation_buffer_text.insert(1.0, display_text)
            self.dictation_buffer_text.see(tk.END)
    
    def show_dictation_preview(self, text):
        """Mostrar preview del dictado antes de enviar"""
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Confirmar Dictado")
        preview_window.geometry("500x300")
        
        ttk.Label(preview_window, text="Dictado completado:", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        text_widget = scrolledtext.ScrolledText(preview_window, height=10, wrap=tk.WORD)
        text_widget.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        text_widget.insert(1.0, text)
        
        button_frame = ttk.Frame(preview_window)
        button_frame.pack(pady=10)
        
        ttk.Button(
            button_frame, 
            text="📤 Enviar a Claude",
            command=lambda: [self.send_text_to_claude(text), preview_window.destroy()]
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="📝 Editar",
            command=lambda: [self.edit_before_send(text_widget, preview_window)]
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="❌ Cancelar",
            command=preview_window.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def edit_before_send(self, text_widget, window):
        """Permitir edición antes de enviar"""
        edited_text = text_widget.get(1.0, tk.END).strip()
        if edited_text:
            self.send_text_to_claude(edited_text)
        window.destroy()
    
    def update_partial_text(self, text):
        """Actualizar texto parcial con indicador de modo"""
        if self.dictation_mode == DictationMode.RECORDING:
            self.partial_text_var.set(f"📝 {text}")
        else:
            self.partial_text_var.set(f"🎤 {text}")
    
    def update_session_info(self):
        """Actualizar información de sesión"""
        duration = datetime.now() - self.session_start
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        mode_text = {
            DictationMode.WAITING: "Esperando",
            DictationMode.RECORDING: "Dictando",
            DictationMode.PROCESSING: "Procesando"
        }
        
        info = (f"Sesión: {hours:02d}:{minutes:02d}:{seconds:02d} | "
                f"Transcripciones: {self.transcription_count} | "
                f"Modo: {mode_text[self.dictation_mode]}")
        
        self.session_info_var.set(info)
        self.root.after(1000, self.update_session_info)
    
    def process_queues(self):
        """Procesar colas de transcripción y comandos"""
        try:
            while not self.transcription_queue.empty():
                item = self.transcription_queue.get_nowait()
                self.handle_transcription(item)
        except queue.Empty:
            pass
        
        try:
            while not self.command_queue.empty():
                command = self.command_queue.get_nowait()
                self.handle_command(command)
        except queue.Empty:
            pass
        
        self.root.after(100, self.process_queues)
    
    def handle_transcription(self, item):
        """Manejar transcripción según modo"""
        if item['type'] == 'final' and item.get('mode') == 'single':
            timestamp = item['timestamp'].strftime("%H:%M:%S")
            text = item['text']
            
            self.transcription_text.insert(tk.END, f"[{timestamp}] {text}\n")
            self.transcription_text.see(tk.END)
            self.transcription_count += 1
            
            if self.config.getboolean('auto_send_to_claude'):
                self.send_text_to_claude(text)
    
    def handle_command(self, command):
        """Manejar comando del sistema"""
        self.logger.info(f"Ejecutando comando: {command}")
    
    def load_medical_terms(self):
        """Cargar términos médicos personalizados"""
        self.medical_terms = []
        dict_dir = Path.home() / "voice-bridge-claude" / "config" / "diccionarios"
        
        dict_files = ["frases_completas.txt", "patologia_molecular.txt"]
        
        total_terms = 0
        for dict_file in dict_files:
            dict_path = dict_dir / dict_file
            if dict_path.exists():
                with open(dict_path, 'r', encoding='utf-8') as f:
                    terms = 0
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.medical_terms.append(line.lower())
                            terms += 1
                    self.logger.info(f"Diccionario {dict_file}: {terms} términos cargados")
                    total_terms += terms
        
        self.logger.info(f"Total términos médicos: {total_terms}")
        self.apply_medical_terms_to_recognizer()
    
    def apply_medical_terms_to_recognizer(self):
        """Aplicar términos médicos al reconocedor"""
        try:
            if hasattr(self, 'speech_recognizer'):
                phrase_list = speechsdk.PhraseListGrammar.from_recognizer(self.speech_recognizer)
                
                command_terms = [
                    "fin dictado", "inicio dictado", "cancelar dictado",
                    "claude fin dictado", "claude inicio dictado"
                ]
                
                critical_terms = [
                    "Claude", "pleomorfismo nuclear", "carcinoma basocelular",
                    "células atípicas", "test de ureasa", "células caliciformes"
                ]
                
                for term in command_terms:
                    phrase_list.addPhrase(term)
                
                for term in critical_terms:
                    phrase_list.addPhrase(term)
                
                for term in self.medical_terms[:200]:
                    phrase_list.addPhrase(term)
                
                self.logger.info(f"Términos médicos aplicados: {len(command_terms) + len(critical_terms) + len(self.medical_terms[:200])}")
        except Exception as e:
            self.logger.error(f"Error aplicando términos médicos: {e}")
    
    def setup_hotkeys(self):
        """Configurar hotkeys globales"""
        self.pressed_keys = set()
        
        self.hotkey_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.hotkey_listener.start()
        
        self.logger.info("Hotkeys configurados")
    
    def on_key_press(self, key):
        """Manejar teclas presionadas"""
        self.pressed_keys.add(key)
        
        ctrl_shift_v = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_char('v')}
        ctrl_shift_s = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_char('s')}
        ctrl_shift_d = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_char('d')}
        
        if self.pressed_keys >= ctrl_shift_v:
            self.root.after_idle(self.start_recognition)
        elif self.pressed_keys >= ctrl_shift_s:
            self.root.after_idle(self.stop_recognition)
        elif self.pressed_keys >= ctrl_shift_d:
            self.root.after_idle(self.toggle_dictation_mode)
    
    def on_key_release(self, key):
        """Manejar teclas liberadas"""
        self.pressed_keys.discard(key)
    
    def toggle_dictation_mode(self):
        """Alternar modo dictado con hotkey"""
        if self.dictation_mode == DictationMode.WAITING:
            self.start_dictation_mode()
        elif self.dictation_mode == DictationMode.RECORDING:
            self.end_dictation_mode()
    
    def start_recognition(self):
        """Iniciar reconocimiento de voz"""
        if not self.is_listening:
            try:
                self.speech_recognizer.start_continuous_recognition_async()
                self.is_listening = True
                self.start_button.config(state="disabled")
                self.stop_button.config(state="normal")
                self.log_to_gui("🎤 Reconocimiento iniciado")
                self.logger.info("Reconocimiento iniciado")
                
                if self.config.getboolean('tts_enabled'):
                    self.speak_text_safe("Sistema listo")
                    
            except Exception as e:
                self.logger.error(f"Error iniciando reconocimiento: {e}")
                messagebox.showerror("Error", f"No se pudo iniciar: {e}")
    
    def stop_recognition(self):
        """Detener reconocimiento de voz"""
        if self.is_listening:
            try:
                if self.dictation_mode == DictationMode.RECORDING:
                    self.end_dictation_mode()
                
                self.speech_recognizer.stop_continuous_recognition_async()
                self.is_listening = False
                self.start_button.config(state="normal")
                self.stop_button.config(state="disabled")
                self.partial_text_var.set("")
                self.log_to_gui("⏹️ Reconocimiento detenido")
                self.logger.info("Reconocimiento detenido")
                
            except Exception as e:
                self.logger.error(f"Error deteniendo reconocimiento: {e}")
    
    def send_to_claude(self):
        """Enviar transcripción a Claude"""
        try:
            try:
                selected = self.transcription_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                selected = self.transcription_text.get(1.0, tk.END).strip()
            
            if selected:
                self.send_text_to_claude(selected)
            else:
                self.log_to_gui("⚠️ No hay texto para enviar")
        except Exception as e:
            self.logger.error(f"Error enviando a Claude: {e}")
    
    def send_text_to_claude(self, text):
        """Enviar texto a Claude Desktop"""
        try:
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            claude_window_id = None
            
            for line in result.stdout.split('\n'):
                if 'Claude' in line:
                    claude_window_id = line.split()[0]
                    break
            
            if claude_window_id:
                subprocess.run(['wmctrl', '-i', '-a', claude_window_id])
                
                activation_delay = float(self.config.get('claude_activation_delay', 1.0))
                time.sleep(activation_delay)
                
                subprocess.run(['xdotool', 'type', text])
                time.sleep(0.1)
                subprocess.run(['xdotool', 'key', 'Return'])
                
                self.log_to_gui(f"📤 Enviado a Claude: {text[:50]}...")
                self.logger.info(f"Texto enviado a Claude")
                
                if self.config.getboolean('tts_enabled'):
                    self.speak_text_safe("Enviado a Claude")
            else:
                self.log_to_gui("❌ Ventana Claude no encontrada")
                
        except Exception as e:
            self.logger.error(f"Error enviando a Claude: {e}")
            self.log_to_gui(f"❌ Error: {e}")
    
    def send_buffered_dictation(self):
        """Enviar el buffer de dictado actual a Claude"""
        if self.dictation_buffer:
            full_text = " ".join(self.dictation_buffer)
            self.send_text_to_claude(full_text)
            self.dictation_buffer.clear()
            self.update_dictation_buffer_display()
    
    def cancel_dictation(self):
        """Cancelar dictado actual"""
        if self.dictation_mode == DictationMode.RECORDING:
            if self.dictation_timeout_timer:
                self.root.after_cancel(self.dictation_timeout_timer)
                self.dictation_timeout_timer = None
            
            self.dictation_buffer.clear()
            self.dictation_mode = DictationMode.WAITING
            self.update_dictation_status("🟢 ESPERANDO", "green")
            self.update_dictation_buffer_display()
            self.last_dictation_activity = None
            self.timeout_warning_given = False
            self.waiting_for_first_word = False
            
            if hasattr(self, 'timeout_progress'):
                self.timeout_progress.grid_remove()
            
            self.log_to_gui("❌ Dictado cancelado")
            
            if self.config.getboolean('tts_enabled'):
                self.speak_text_safe("Dictado cancelado")
    
    def clear_transcriptions(self):
        """Limpiar área de transcripciones"""
        self.transcription_text.delete(1.0, tk.END)
        self.partial_text_var.set("")
        self.dictation_buffer.clear()
        self.update_dictation_buffer_display()
        self.transcription_count = 0
        self.log_to_gui("🗑️ Transcripciones limpiadas")
    
    def save_transcriptions(self):
        """Guardar transcripciones a archivo"""
        try:
            content = self.transcription_text.get(1.0, tk.END).strip()
            if not content:
                self.log_to_gui("⚠️ No hay transcripciones para guardar")
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcripciones_patologia_v21_{timestamp}.txt"
            
            save_dir = Path.home() / "voice-bridge-claude" / "logs"
            save_dir.mkdir(parents=True, exist_ok=True)
            save_path = save_dir / filename
            
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(f"# Transcripciones Voice Bridge v2.1\n")
                f.write(f"# Sesión: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total: {self.transcription_count} transcripciones\n")
                f.write(f"# Modo: Dictado Continuo Mejorado\n")
                f.write(f"# Micrófono: {self.config.get('microphone_type', 'ambient')}\n\n")
                f.write(content)
            
            self.log_to_gui(f"💾 Guardado: {filename}")
            self.logger.info(f"Transcripciones guardadas: {save_path}")
            
        except Exception as e:
            self.logger.error(f"Error guardando: {e}")
            self.log_to_gui(f"❌ Error guardando: {e}")
    
    def log_to_gui(self, message):
        """Agregar mensaje al log de la GUI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
        lines = self.log_text.get(1.0, tk.END).count('\n')
        if lines > 100:
            self.log_text.delete(1.0, "10.0")
    
    def on_closing(self):
        """Manejar cierre de la aplicación"""
        if self.is_listening:
            self.stop_recognition()
        
        if hasattr(self, 'hotkey_listener'):
            self.hotkey_listener.stop()
        
        content = self.transcription_text.get(1.0, tk.END).strip()
        if content:
            try:
                self.save_transcriptions()
            except:
                pass
        
        self.logger.info("Voice Bridge v2.1 cerrado")
        self.root.destroy()
    
    def run(self):
        """Ejecutar la aplicación"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()

def main():
    """Función principal"""
    try:
        if not os.environ.get('AZURE_SPEECH_KEY'):
            print("❌ ERROR: AZURE_SPEECH_KEY no configurado")
            print("export AZURE_SPEECH_KEY='tu_key_aqui'")
            return
        
        app = VoiceBridgeV21()
        app.run()
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
