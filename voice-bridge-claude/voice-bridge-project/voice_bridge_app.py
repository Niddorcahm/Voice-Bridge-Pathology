#!/usr/bin/env python3
"""
Voice Bridge para Claude Desktop - Patología Molecular
Aplicación principal para reconocimiento de voz en tiempo real
Autor: Sistema para Patólogo Molecular
Fecha: 2025-07-06
"""
import subprocess
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
import sys

# Configurar pyautogui para seguridad
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

class VoiceBridgePathology:
    def __init__(self):
        """Inicializar Voice Bridge para Patología"""
        self.setup_logging()
        self.logger.info("=== Iniciando Voice Bridge Pathology ===")
        
        # Cargar configuración
        self.config = self.load_config()
        
        # Setup Azure Speech
        self.setup_azure_speech()
        
        # Estado de la aplicación
        self.is_listening = False
        self.is_speaking = False
        self.transcription_queue = queue.Queue()
        self.hotkey_listener = None
        self.session_start = datetime.now()
        self.transcription_count = 0
        
        # GUI
        self.setup_gui()
        
        # Términos médicos
        self.load_medical_terms()
        
        # Hotkeys
        self.setup_hotkeys()
        
        self.logger.info("Voice Bridge iniciado correctamente")
        self.log_to_gui("🎉 Voice Bridge listo para patología molecular")
    
    def setup_logging(self):
        """Configurar sistema de logging"""
        # Crear directorio de logs
        log_dir = Path.home() / "voice-bridge-claude" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar logging
        log_file = log_dir / f"voice_bridge_{datetime.now().strftime('%Y%m%d')}.log"
        
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
        """Cargar configuración desde archivo y variables de entorno"""
        config = configparser.ConfigParser()
        
        # Configuración por defecto
        default_config = {
            'azure_speech_key': os.environ.get('AZURE_SPEECH_KEY', ''),
            'azure_region': os.environ.get('AZURE_SPEECH_REGION', 'eastus'),
            'speech_language': os.environ.get('SPEECH_LANGUAGE', 'es-CO'),
            'tts_voice': os.environ.get('TTS_VOICE', 'es-CO-SalomeNeural'),
            'hotkey_start': 'ctrl+shift+v',
            'hotkey_stop': 'ctrl+shift+s',
            'hotkey_emergency': 'ctrl+shift+x',
            'auto_send_to_claude': 'true',
            'claude_window_title': 'Claude',
            'medical_mode': 'true',
            'confidence_threshold': '0.7',
            'tts_enabled': 'true',
            'claude_activation_delay': '0.2'
        }
        
        # Intentar cargar archivo de configuración
        config_file = Path.home() / "voice-bridge-claude" / "config" / "voice_bridge_config.ini"
        if config_file.exists():
            config.read(config_file)
            self.logger.info(f"Configuración cargada desde: {config_file}")
        else:
            config['DEFAULT'] = default_config
            # Crear archivo de configuración
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                config.write(f)
            self.logger.info(f"Archivo de configuración creado: {config_file}")
        
        return config['DEFAULT']
    
    def setup_azure_speech(self):
        """Configurar Azure Speech Services"""
        speech_key = self.config['azure_speech_key']
        region = self.config['azure_region']
        
        if not speech_key:
            raise ValueError("❌ AZURE_SPEECH_KEY no configurado. Revisar variables de entorno.")
        
        self.logger.info(f"Configurando Azure Speech - Región: {region}")
        
        # Configuración de Azure Speech
        self.speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=region
        )
        
        # Configurar idioma y voz
        self.speech_config.speech_recognition_language = self.config['speech_language']
        self.speech_config.speech_synthesis_voice_name = self.config['tts_voice']
        
        # Configuración específica para español médico
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_RecoMode,
            "INTERACTIVE"  # Mejor para terminología técnica
        )
        
        # Mejorar precisión para acentos colombianos
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_UserDefinedQueryParameters,
            "language=es-CO&domain=medical"
        )
        
        # Configuraciones avanzadas para patología
        if self.config.getboolean('medical_mode'):
            # Mejorar precisión para términos médicos
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode,
                "Continuous"
            )
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceResponse_ProfanityOption,
                "Raw"
            )
           # NUEVAS LÍNEAS PARA REDUCIR LATENCIA:
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
                "5000"  # 3 segundos max de silencio inicial
            )
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs,
                "3000"   # 0.5 segundos de silencio para finalizar
            )
            self.speech_config.set_property(
                speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs,
                "1500"   # 0.2 segundos entre palabras
            )
            
            # Configuración para frases largas
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_RecoMode,
                "CONVERSATION"  # Modo conversación para frases largas
            )
            
            # Deshabilitar segmentación automática
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceResponse_StablePartialResultThreshold,
                "3"
            )
            
            # Mejorar reconocimiento de términos técnicos
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_TranslationToLanguages,
                "es-CO"  # Forzar español colombiano
            )

            # Resultados más detallados (nombre correcto)
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceResponse_RequestDetailedResultTrueFalse,
                "true"
            )

        # Audio config
        self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        
        # Crear reconocedor de voz
        self.speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=self.audio_config
        )
        
        # Crear sintetizador de voz
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config
        )
        
        # Configurar callbacks
        self.setup_speech_callbacks()
        
        self.logger.info("✅ Azure Speech Services configurado correctamente")
    
    def setup_speech_callbacks(self):
        """Configurar callbacks de reconocimiento de voz"""
        
        def on_recognized(evt):
            """Texto reconocido final"""
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text = evt.result.text.strip()
                if text:
                    confidence = self.extract_confidence(evt.result)
                    
                    # DEBUG: Agregar estas líneas temporalmente
                    print(f"DEBUG - Texto final: '{text}'")
                    print(f"DEBUG - Confianza extraída: {confidence}")
                    print(f"DEBUG - JSON completo: {evt.result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult, 'NO JSON')}")

                    self.transcription_queue.put({
                        'type': 'final',
                        'text': text,
                        'confidence': confidence,
                        'timestamp': datetime.now()
                    })
                    self.logger.info(f"Texto reconocido: {text[:50]}... (confianza: {confidence:.2f})")
        
        def on_recognizing(evt):
            """Texto parcial durante reconocimiento"""
            if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
                text = evt.result.text.strip()
                if text:
                    self.update_partial_text(text)
        
        def on_error(evt):
            """Error en reconocimiento"""
            error_msg = f"Error de reconocimiento: {evt.result.error_details}"
            self.logger.error(error_msg)
            self.transcription_queue.put({
                'type': 'error',
                'text': error_msg,
                'timestamp': datetime.now()
            })
        
        # Conectar eventos
        self.speech_recognizer.recognized.connect(on_recognized)
        self.speech_recognizer.recognizing.connect(on_recognizing)
        self.speech_recognizer.canceled.connect(on_error)
    
    def extract_confidence(self, result):
        """Extraer nivel de confianza del resultado"""
        try:
            json_result = json.loads(result.properties.get(
                speechsdk.PropertyId.SpeechServiceResponse_JsonResult, '{}'
            ))
            return json_result.get('NBest', [{}])[0].get('Confidence', 0.0)
        except:
            return 0.0
    
    def load_medical_terms(self):
        """Cargar términos médicos desde diccionarios personalizados"""
        self.medical_terms = []
        diccionarios_dir = Path.home() / "voice-bridge-claude" / "config" / "diccionarios"
    
        # Lista de diccionarios por PRIORIDAD (el primero tiene mayor prioridad)
        diccionarios_files = [
            "frases_completas.txt",      # PRIORIDAD MÁXIMA - Frases largas
            "patologia_molecular.txt",   # PRIORIDAD ALTA - Tu vocabulario real
        ]
    
        total_terminos = 0
    
        for dic_file in diccionarios_files:
            dic_path = diccionarios_dir / dic_file
        
            if dic_path.exists():
                with open(dic_path, 'r', encoding='utf-8') as f:
                    terminos_archivo = 0
                    for line in f:
                        line = line.strip()
                        # Ignorar líneas vacías y comentarios
                        if line and not line.startswith('#'):
                            self.medical_terms.append(line.lower())
                            terminos_archivo += 1
                
                    self.logger.info(f"Diccionario {dic_file}: {terminos_archivo} términos cargados")
                    total_terminos += terminos_archivo
            else:
                self.logger.warning(f"Diccionario no encontrado: {dic_path}")
    
        self.logger.info(f"Total términos médicos personalizados: {total_terminos}")
    
        # Aplicar términos al reconocedor con PRIORIDAD MÁXIMA
        self.apply_medical_terms_to_recognizer()

    def apply_medical_terms_to_recognizer(self):
        """Aplicar términos médicos con prioridad optimizada"""
        try:
            if not hasattr(self, 'speech_recognizer'):
                self.logger.warning("Reconocedor no disponible para aplicar términos médicos")
                return
            
            # Crear lista de frases con máxima prioridad
            phrase_list = speechsdk.PhraseListGrammar.from_recognizer(self.speech_recognizer)
        
            # TÉRMINOS DE PRIORIDAD CRÍTICA (se procesan primero)
            critical_terms = [
                "Claude",  # CRÍTICO: Para evitar "Cloud"
                "pleomorfismo nuclear", 
                "carcinoma basocelular",
                "células atípicas",
                "invasión focal",
                "dermis papilar",
                "compatible con",
                "gastritis crónica",
                "metaplasia intestinal",
                "Helicobacter spp",
                "clasificación de Viena",
                "OLGA estadio",
                "OLGIM estadio"
            ]
        
            # Agregar términos críticos con boost máximo
            for term in critical_terms:
                phrase_list.addPhrase(term)
                # Agregar variantes para mayor robustez
                phrase_list.addPhrase(term.replace(" ", ""))  # sin espacios
                if "-" in term:
                    phrase_list.addPhrase(term.replace("-", " "))  # espacios en lugar de guiones
        
            # Agregar resto de términos médicos (optimizado para performance)
            for term in self.medical_terms[:250]:  # Top 250 términos más importantes
                phrase_list.addPhrase(term)
        
            self.logger.info(f"Términos médicos aplicados con prioridad: {len(self.medical_terms[:250])}")
        
        except Exception as e:
            self.logger.error(f"Error aplicando términos médicos: {e}")
    
    def setup_gui(self):
        """Configurar interfaz gráfica"""
        self.root = tk.Tk()
        self.root.title("Voice Bridge - Patología Molecular")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Configurar ícono y estilo
        try:
            icon_path = Path.home() / "voice-bridge-claude" / "assets" / "voice-bridge.png"
            if icon_path.exists():
                # Para sistemas Linux con tkinter
                self.root.iconphoto(True, tk.PhotoImage(file=str(icon_path)))
            else:
                self.root.iconbitmap(default='')  # Usar ícono por defecto
        except Exception as e:
            self.logger.warning(f"No se pudo cargar icono: {e}")
        
        # Frame principal con padding
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Header con información de estado
        header_frame = ttk.LabelFrame(main_frame, text="Estado del Sistema", padding="10")
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_var = tk.StringVar(value="🟢 Sistema listo")
        status_label = ttk.Label(header_frame, textvariable=self.status_var, 
                                font=("Arial", 12, "bold"))
        status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Información de sesión
        self.session_info_var = tk.StringVar()
        self.update_session_info()
        session_label = ttk.Label(header_frame, textvariable=self.session_info_var, 
                                 font=("Arial", 9))
        session_label.grid(row=1, column=0, sticky=tk.W)
        
        # Controles principales
        controls_frame = ttk.LabelFrame(main_frame, text="Control de Voz", padding="10")
        controls_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.start_button = ttk.Button(controls_frame, 
                                      text="🎤 Iniciar Reconocimiento\n(Ctrl+Shift+V)", 
                                      command=self.start_recognition, 
                                      width=25)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(controls_frame, 
                                     text="⏹️ Detener\n(Ctrl+Shift+S)", 
                                     command=self.stop_recognition, 
                                     width=25, 
                                     state="disabled")
        self.stop_button.grid(row=0, column=1)
        
        # Texto parcial (reconocimiento en tiempo real)
        partial_frame = ttk.LabelFrame(main_frame, text="Reconocimiento en Tiempo Real", padding="5")
        partial_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.partial_text_var = tk.StringVar()
        partial_label = ttk.Label(partial_frame, textvariable=self.partial_text_var, 
                                 foreground="blue", font=("Arial", 10, "italic"),
                                 wraplength=550)
        partial_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Transcripciones finales
        transcription_frame = ttk.LabelFrame(main_frame, text="Transcripciones", padding="5")
        transcription_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.transcription_text = scrolledtext.ScrolledText(transcription_frame, 
                                                           height=8, width=70,
                                                           font=("Arial", 10))
        self.transcription_text.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Botones de transcripción
        transcription_buttons = ttk.Frame(transcription_frame)
        transcription_buttons.grid(row=1, column=0, columnspan=3, pady=(5, 0))
        
        ttk.Button(transcription_buttons, text="📤 Enviar a Claude", 
                  command=self.send_to_claude).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(transcription_buttons, text="🗑️ Limpiar", 
                  command=self.clear_transcriptions).grid(row=0, column=1, padx=5)
        ttk.Button(transcription_buttons, text="💾 Guardar", 
                  command=self.save_transcriptions).grid(row=0, column=2, padx=(5, 0))
        
        # Opciones
        options_frame = ttk.LabelFrame(main_frame, text="Configuración", padding="5")
        options_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.auto_send_var = tk.BooleanVar(value=self.config.getboolean('auto_send_to_claude'))
        ttk.Checkbutton(options_frame, text="Envío automático a Claude", 
                       variable=self.auto_send_var).grid(row=0, column=0, sticky=tk.W)
        
        self.tts_enabled_var = tk.BooleanVar(value=self.config.getboolean('tts_enabled'))
        ttk.Checkbutton(options_frame, text="Respuestas por voz (TTS)", 
                       variable=self.tts_enabled_var).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # Log del sistema
        log_frame = ttk.LabelFrame(main_frame, text="Log del Sistema", padding="5")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=4, width=70,
                                                 font=("Courier", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar redimensionado
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)  # Transcripciones expandibles
        main_frame.rowconfigure(5, weight=1)  # Log expandible
        
        # Frame de microscopía
        microscopy_frame = ttk.LabelFrame(main_frame, text="Modo Microscopía", padding="5")
        microscopy_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.microscopy_mode_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(microscopy_frame, text="Confirmación por voz de dictados", 
                       variable=self.microscopy_mode_var).grid(row=0, column=0, sticky=tk.W)

        self.read_back_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(microscopy_frame, text="Leer transcripción completa", 
                       variable=self.read_back_var).grid(row=0, column=1, sticky=tk.W)
                
        # Configurar cierre de ventana
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Procesar queue de transcripciones
        self.root.after(100, self.process_transcription_queue)
        
        # Actualizar información de sesión periódicamente
        self.root.after(1000, self.update_session_info_periodic)
    
    def setup_hotkeys(self):
        """Configurar hotkeys globales"""
        try:
            self.pressed_keys = set()
            
            # Iniciar listener de hotkeys
            self.hotkey_listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.hotkey_listener.start()
            
            self.logger.info("Hotkeys configurados: Ctrl+Shift+V (iniciar), Ctrl+Shift+S (detener)")
            
        except Exception as e:
            self.logger.error(f"Error configurando hotkeys: {e}")
            messagebox.showwarning("Hotkeys", "No se pudieron configurar los hotkeys globales")
    
    def on_key_press(self, key):
        """Manejar teclas presionadas"""
        self.pressed_keys.add(key)
        
        # Verificar combinaciones
        ctrl_shift_v = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_char('v')}
        ctrl_shift_s = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_char('s')}
        ctrl_shift_x = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_char('x')}
        
        if self.pressed_keys >= ctrl_shift_v:
            self.root.after_idle(self.start_recognition)
        elif self.pressed_keys >= ctrl_shift_s:
            self.root.after_idle(self.stop_recognition)
        elif self.pressed_keys >= ctrl_shift_x:
            self.root.after_idle(self.emergency_stop)
    
    def on_key_release(self, key):
        """Manejar teclas liberadas"""
        self.pressed_keys.discard(key)
    
    def update_partial_text(self, text):
        """Actualizar texto parcial en la GUI - versión mejorada para frases largas"""
        # Mostrar más texto (hasta 100 caracteres en lugar de cortarlo)
        if len(text) > 100:
            display_text = text[:100] + "..."
        else:
            display_text = text
    
        self.partial_text_var.set(f"🎤 {display_text}")
    
    def update_session_info(self):
        """Actualizar información de sesión"""
        duration = datetime.now() - self.session_start
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        info = f"Sesión: {hours:02d}:{minutes:02d}:{seconds:02d} | Transcripciones: {self.transcription_count}"
        self.session_info_var.set(info)
    
    def update_session_info_periodic(self):
        """Actualizar información de sesión periódicamente"""
        self.update_session_info()
        self.root.after(1000, self.update_session_info_periodic)
    
    def process_transcription_queue(self):
        """Procesar transcripciones del queue"""
        try:
            while not self.transcription_queue.empty():
                transcription = self.transcription_queue.get_nowait()
                self.handle_transcription(transcription)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_transcription_queue)
    
    def handle_transcription(self, transcription):
        """Manejar nueva transcripción"""
        if transcription['type'] == 'final':
            text = transcription['text']
            timestamp = transcription['timestamp'].strftime("%H:%M:%S")
            confidence = transcription.get('confidence', 1.0)  # Default a 1.0 si no hay info

            # Filtrar por confianza mínima
            min_confidence = 0.0  # Acepta todo
            # if confidence < min_confidence:
            #     self.log_to_gui(f"⚠️ Baja confianza ({confidence:.2f}): {text[:30]}...")
            #     return
            
            # Mostrar en GUI
            formatted_text = f"[{timestamp}] {text}\n"
            self.transcription_text.insert(tk.END, formatted_text)
            self.transcription_text.see(tk.END)
            
            # Contar transcripciones
            self.transcription_count += 1
            
            # Limpiar texto parcial
            self.partial_text_var.set("")
            
            # CONFIRMACIÓN POR VOZ ***
            if self.tts_enabled_var.get():
                # Para transcripciones cortas: leer completo
                if len(text) < 50:
                    self.speak_text(f"Recibido: {text}")
                else:
                    # Para transcripciones largas: confirmar palabras clave
                    key_words = self.extract_key_medical_terms(text)
                    if key_words:
                        self.speak_text(f"Recibido dictado con: {', '.join(key_words)}")
                    else:
                        self.speak_text("Dictado recibido")
            
            # Auto-enviar a Claude si está habilitado
            if self.auto_send_var.get():
                self.send_text_to_claude(text)
                # Confirmar envío por voz
                if self.tts_enabled_var.get():
                    self.speak_text("Enviado a Claude")
            
            self.log_to_gui(f"✅ Transcripción: {text[:40]}... (conf: {confidence:.2f})")
            
        elif transcription['type'] == 'error':
            self.log_to_gui(f"❌ {transcription['text']}")
                                                    
    def extract_key_medical_terms(self, text):
        """Extraer términos médicos clave de la transcripción"""
        key_terms = [
            "carcinoma", "adenocarcinoma", "pleomorfismo", "células atípicas", 
            "gastritis", "metaplasia", "hiperqueratosis", "invasión", "compatible"
        ]
    
        found_terms = []
        text_lower = text.lower()
        for term in key_terms:
            if term in text_lower:
                found_terms.append(term)
    
        return found_terms[:3]  # Máximo 3 términos para no ser verboso
    
    def process_voice_commands(self, text):
        """Procesar comandos de voz para control hands-free"""
        text_lower = text.lower()
    
        # Comandos básicos
        if "repetir transcripción" in text_lower:
            last_transcription = self.get_last_transcription()
            if last_transcription:
                self.speak_text(f"Última transcripción: {last_transcription}")
    
        elif "enviar a claude" in text_lower:
            self.send_to_claude()
            self.speak_text("Enviado a Claude")
    
        elif "limpiar transcripciones" in text_lower:
            self.clear_transcriptions()
            self.speak_text("Transcripciones limpiadas")
    
        elif "estado del sistema" in text_lower:
            status = f"Sistema activo. {self.transcription_count} transcripciones realizadas"
            self.speak_text(status)
    
        return True  # Comando procesado

    def get_last_transcription(self):
        """Obtener última transcripción"""
        content = self.transcription_text.get("end-2l", "end-1l").strip()
        if content:
            # Extraer solo el texto, sin timestamp
            if "]" in content:
                return content.split("]", 1)[1].strip()
        return None
      
    def start_recognition(self):
        """Iniciar reconocimiento de voz"""
        if not self.is_listening:
            try:
                self.speech_recognizer.start_continuous_recognition_async()
                self.is_listening = True
                self.status_var.set("🔴 Escuchando...")
                self.start_button.config(state="disabled")
                self.stop_button.config(state="normal")
                self.log_to_gui("🎤 Reconocimiento de voz iniciado")
                self.logger.info("Reconocimiento iniciado")
                
                # Notificación por voz si está habilitada
                if self.tts_enabled_var.get():
                    self.speak_text("Reconocimiento iniciado")
                    
            except Exception as e:
                self.logger.error(f"Error iniciando reconocimiento: {e}")
                messagebox.showerror("Error", f"No se pudo iniciar el reconocimiento:\n{e}")
    
    def stop_recognition(self):
        """Detener reconocimiento de voz"""
        if self.is_listening:
            try:
                self.speech_recognizer.stop_continuous_recognition_async()
                self.is_listening = False
                self.status_var.set("🟢 Sistema listo")
                self.start_button.config(state="normal")
                self.stop_button.config(state="disabled")
                self.partial_text_var.set("")
                self.log_to_gui("⏹️ Reconocimiento detenido")
                self.logger.info("Reconocimiento detenido")
                
                # Notificación por voz si está habilitada
                if self.tts_enabled_var.get():
                    self.speak_text("Reconocimiento detenido")
                    
            except Exception as e:
                self.logger.error(f"Error deteniendo reconocimiento: {e}")
    
    def emergency_stop(self):
        """Parada de emergencia"""
        self.stop_recognition()
        self.log_to_gui("🚨 Parada de emergencia activada")
        if self.tts_enabled_var.get():
            self.speak_text("Parada de emergencia")
    
    def send_to_claude(self):
        """Enviar transcripción seleccionada a Claude"""
        try:
            # Obtener texto seleccionado o todo el texto
            try:
                selected_text = self.transcription_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                # No hay selección, usar todas las transcripciones
                all_text = self.transcription_text.get(1.0, tk.END).strip()
                if not all_text:
                    self.log_to_gui("⚠️ No hay texto para enviar")
                    return
                selected_text = all_text
            
            if selected_text:
                self.send_text_to_claude(selected_text)
            else:
                self.log_to_gui("⚠️ No hay texto seleccionado")
                
        except Exception as e:
            self.logger.error(f"Error enviando a Claude: {e}")
            self.log_to_gui(f"❌ Error enviando a Claude: {e}")
    
    def send_text_to_claude(self, text):
        """Enviar texto a Claude Desktop via herramientas nativas Linux"""
        try:
            claude_title = self.config.get('claude_window_title', 'Claude')
        
            # Buscar ventana de Claude con wmctrl - LÓGICA MEJORADA
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            claude_window_id = None
        
            for line in result.stdout.split('\n'):
                if line.strip():
                    # Dividir línea: window_id, desktop, hostname, title
                    parts = line.split(None, 3)
                    if len(parts) >= 4:
                        window_id, desktop, hostname, title = parts
                        # Buscar EXACTAMENTE "Claude" en el título
                        if title.strip() == 'Claude':
                            claude_window_id = window_id
                            self.log_to_gui(f"🎯 Claude encontrado: {window_id} - {title}")
                            break
        
            if claude_window_id:
                # Activar ventana de Claude
                subprocess.run(['wmctrl', '-i', '-a', claude_window_id])
            
                # Esperar activación
                delay = float(self.config.get('claude_activation_delay', 0.5))
                time.sleep(delay)
            
                # Enviar texto usando xdotool
                subprocess.run(['xdotool', 'type', text])
                time.sleep(0.1)
                subprocess.run(['xdotool', 'key', 'Return'])
            
                self.log_to_gui(f"📤 Enviado a Claude: {text[:30]}...")
                self.logger.info(f"Texto enviado a Claude: {text[:50]}...")
            
            else:
                self.log_to_gui(f"❌ Ventana 'Claude' no encontrada")
                self.log_to_gui("💡 Verifica que Claude Desktop esté abierto")
            
                # Mostrar ventanas disponibles para debug
                for line in result.stdout.split('\n'):
                    if line.strip() and 'Claude' in line:
                        self.log_to_gui(f"🔍 Encontrado: {line}")
                
        except Exception as e:
            self.logger.error(f"Error en automatización: {e}")
            self.log_to_gui(f"❌ Error automatización: {e}")

    def speak_text(self, text):
        """Sintetizar texto a voz"""
        if self.tts_enabled_var.get() and not self.is_speaking:
            try:
                def tts_thread():
                    self.is_speaking = True
                    try:
                        result = self.speech_synthesizer.speak_text_async(text).get()
                        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
                            self.logger.warning(f"Error TTS: {result.reason}")
                    except Exception as e:
                        self.logger.error(f"Error en síntesis: {e}")
                    finally:
                        self.is_speaking = False
                
                threading.Thread(target=tts_thread, daemon=True).start()
                
            except Exception as e:
                self.logger.error(f"Error configurando TTS: {e}")
    
    def clear_transcriptions(self):
        """Limpiar transcripciones"""
        self.transcription_text.delete(1.0, tk.END)
        self.partial_text_var.set("")
        self.transcription_count = 0
        self.log_to_gui("🗑️ Transcripciones limpiadas")
    
    def save_transcriptions(self):
        """Guardar transcripciones a archivo"""
        try:
            content = self.transcription_text.get(1.0, tk.END).strip()
            if not content:
                self.log_to_gui("⚠️ No hay transcripciones para guardar")
                return
            
            # Crear archivo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcripciones_patologia_{timestamp}.txt"
            
            save_dir = Path.home() / "voice-bridge-claude" / "logs"
            save_dir.mkdir(parents=True, exist_ok=True)
            save_path = save_dir / filename
            
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(f"# Transcripciones Voice Bridge - Patología Molecular\n")
                f.write(f"# Sesión: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total transcripciones: {self.transcription_count}\n\n")
                f.write(content)
            
            self.log_to_gui(f"💾 Guardado: {filename}")
            self.logger.info(f"Transcripciones guardadas: {save_path}")
            
        except Exception as e:
            self.logger.error(f"Error guardando transcripciones: {e}")
            self.log_to_gui(f"❌ Error guardando: {e}")
    
    def log_to_gui(self, message):
        """Agregar mensaje al log de la GUI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        
        # Limitar tamaño del log
        lines = self.log_text.get(1.0, tk.END).count('\n')
        if lines > 100:
            self.log_text.delete(1.0, "10.0")
    
    def on_closing(self):
        """Manejar cierre de la aplicación"""
        if self.is_listening:
            self.stop_recognition()
        
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        
        # Guardar transcripciones automáticamente si existen
        content = self.transcription_text.get(1.0, tk.END).strip()
        if content:
            try:
                self.save_transcriptions()
            except:
                pass
        
        self.logger.info("Voice Bridge cerrado")
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
        # Verificar variables de entorno críticas
        if not os.environ.get('AZURE_SPEECH_KEY'):
            print("❌ ERROR: AZURE_SPEECH_KEY no configurado")
            print("Configura las variables de entorno:")
            print("export AZURE_SPEECH_KEY='tu_key_aqui'")
            print("export AZURE_SPEECH_REGION='eastus'")
            sys.exit(1)
        
        # Crear y ejecutar aplicación
        app = VoiceBridgePathology()
        app.run()
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
