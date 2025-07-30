#!/usr/bin/env python3
"""
Voice Bridge v2.0.3 - VERSIÓN CORREGIDA SIN ERRORES DE SINTAXIS
Regreso a funcionalidad + GUI configuración + Timeouts Azure configurables

CAMBIOS PRINCIPALES:
1. Timeouts Azure configurables desde GUI (soluciona frases cortadas)
2. Anti-acoplamiento para micrófonos lavalier
3. Buffer médico inteligente
4. Sin comandos especiales complicados
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
import gc

# Configurar pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

class VoiceBridgeV203Fixed:
    def __init__(self):
        """Voice Bridge v2.0.3 - Funcionalidad Médica Optimizada CORREGIDA"""
        self.setup_logging()
        self.logger.info("=== Voice Bridge v2.0.3 FIXED - REGRESO A FUNCIONALIDAD ===")
        
        # Configuración
        self.config = self.load_config()
        
        # Estado simplificado
        self.is_listening = False
        self.is_speaking = False
        self.recognition_paused_for_tts = False
        self.medical_buffer = []
        self.last_activity_time = None
        self.medical_pause_seconds = float(self.config.get('medical_pause_seconds', '4'))
        self.buffer_timer = None
        
        # Azure objects
        self.speech_config = None
        self.speech_recognizer = None
        self.speech_synthesizer = None
        
        # Colas
        self.transcription_queue = queue.Queue()
        
        # GUI y componentes
        self.setup_gui()
        self.cleanup_and_setup_azure()
        self.load_medical_terms()
        self.setup_hotkeys()
        
        # Sesión
        self.session_start = datetime.now()
        self.transcription_count = 0
        
        self.logger.info("Voice Bridge v2.0.3 FIXED iniciado - Modo médico optimizado")
        self.log_to_gui("🏥 Voice Bridge v2.0.3 FIXED - Patología Optimizada")
    
    def setup_logging(self):
        """Logging simplificado"""
        log_dir = Path.home() / "voice-bridge-claude" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"voice_bridge_v203_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Log v2.0.3 FIXED iniciado: {log_file}")
    
    def load_config(self):
        """Configuración optimizada para médico"""
        config = configparser.ConfigParser()
        
        default_config = {
            'azure_speech_key': os.environ.get('AZURE_SPEECH_KEY', ''),
            'azure_region': os.environ.get('AZURE_SPEECH_REGION', 'eastus'),
            'speech_language': 'es-CO',
            'tts_voice': 'es-CO-SalomeNeural',
            'auto_send_to_claude': 'false',
            'tts_enabled': 'true',
            'claude_activation_delay': '0.5',
            'medical_pause_seconds': '4',
            'azure_timeout_mode': 'medical',
            'microphone_type': 'ambient',
            'tts_during_dictation': 'auto',
            'auto_correct_medical': 'true',
            # Timeouts Azure configurables
            'azure_initial_silence_ms': '10000',
            'azure_end_silence_ms': '8000',
            'azure_segmentation_ms': '5000'  # 5s por defecto para frases largas
        }
        
        config_file = Path.home() / "voice-bridge-claude" / "config" / "voice_bridge_config.ini"
        if config_file.exists():
            config.read(config_file)
            for key, value in default_config.items():
                if key not in config['DEFAULT']:
                    config['DEFAULT'][key] = value
        else:
            config['DEFAULT'] = default_config
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                config.write(f)
        
        return config['DEFAULT']
    
    def cleanup_and_setup_azure(self):
        """Limpiar y configurar Azure para modo médico"""
        self.log_to_gui("🧹 Configurando Azure para modo médico...")
        
        # Cleanup
        try:
            if hasattr(self, 'speech_recognizer') and self.speech_recognizer:
                self.speech_recognizer.stop_continuous_recognition_async().wait()
                del self.speech_recognizer
            gc.collect()
            time.sleep(0.3)
        except:
            pass
        
        # Setup médico
        try:
            self.setup_azure_medical_mode()
            self.log_to_gui("✅ Azure configurado para patología")
        except Exception as e:
            self.logger.error(f"Error configurando Azure: {e}")
            self.log_to_gui(f"❌ Error Azure: {e}")
            messagebox.showerror("Error Azure", f"No se pudo configurar Azure:\n{e}")
    
    def setup_azure_medical_mode(self):
        """Configuración Azure específica para dictado médico largo"""
        speech_key = self.config['azure_speech_key']
        region = self.config['azure_region']
        
        if not speech_key:
            raise ValueError("AZURE_SPEECH_KEY no configurado")
        
        self.logger.info(f"Configurando Azure MODO MÉDICO - Región: {region}")
        
        # Configuración base
        self.speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=region
        )
        
        self.speech_config.speech_recognition_language = self.config['speech_language']
        self.speech_config.speech_synthesis_voice_name = self.config['tts_voice']
        
        # Usar modo CONVERSATION para dictados largos
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_RecoMode,
            "CONVERSATION"
        )
        
        # TIMEOUTS CONFIGURABLES DESDE GUI
        initial_silence = self.config.get('azure_initial_silence_ms', '10000')
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
            initial_silence
        )
        
        # CRÍTICO: Tiempo entre palabras (configurable)
        segmentation_silence = self.config.get('azure_segmentation_ms', '5000')
        self.speech_config.set_property(
            speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs,
            segmentation_silence
        )
        
        # Tiempo de finalización (configurable)
        end_silence = self.config.get('azure_end_silence_ms', '8000')
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs,
            end_silence
        )
        
        self.logger.info(f"Timeouts Azure: inicial={initial_silence}ms, segmentación={segmentation_silence}ms, fin={end_silence}ms")
        
        # Configuraciones opcionales
        try:
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceResponse_StablePartialResultThreshold,
                "3"
            )
        except AttributeError:
            self.logger.info("Configuraciones avanzadas no disponibles - usando básicas")
            pass
        
        # Crear reconocedor y sintetizador
        self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        
        self.speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=self.audio_config
        )
        
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config
        )
        
        # Configurar callbacks médicos
        self.setup_medical_callbacks()
        
        self.logger.info("✅ Azure configurado para modo médico")
    
    def setup_medical_callbacks(self):
        """Callbacks optimizados para dictado médico"""
        
        def on_recognized_medical(evt):
            """Procesar texto reconocido en modo médico"""
            try:
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    text = evt.result.text.strip()
                    if text and not self.recognition_paused_for_tts:
                        self.logger.info(f"🏥 MÉDICO RECONOCIDO: '{text}'")
                        
                        # Aplicar correcciones médicas
                        corrected_text = self.apply_medical_corrections(text)
                        
                        # Agregar al buffer médico
                        self.add_to_medical_buffer(corrected_text)
                        
            except Exception as e:
                self.logger.error(f"Error en callback médico: {e}")
        
        def on_recognizing_medical(evt):
            """Texto parcial en modo médico"""
            try:
                if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
                    text = evt.result.text.strip()
                    if text and not self.recognition_paused_for_tts:
                        # Resetear inactividad con cualquier actividad
                        self.last_activity_time = time.time()
                        self.update_partial_text(f"🏥 {text}")
            except Exception as e:
                self.logger.error(f"Error en recognizing médico: {e}")
        
        def on_error_medical(evt):
            """Manejo de errores médicos"""
            try:
                if hasattr(evt, 'result') and evt.result:
                    if hasattr(evt.result, 'error_details'):
                        error_msg = f"Error Azure: {evt.result.error_details}"
                    elif hasattr(evt.result, 'reason'):
                        error_msg = f"Error Azure reason: {evt.result.reason}"
                    else:
                        error_msg = f"Error Azure: {str(evt.result)}"
                else:
                    error_msg = f"Error Azure general: {str(evt)}"
                
                self.logger.error(error_msg)
                self.log_to_gui(f"❌ {error_msg}")
            except Exception as e:
                self.logger.error(f"Error en callback error: {e}")
                self.log_to_gui("❌ Error de reconocimiento")
        
        # Conectar callbacks
        self.speech_recognizer.recognized.connect(on_recognized_medical)
        self.speech_recognizer.recognizing.connect(on_recognizing_medical)
        self.speech_recognizer.canceled.connect(on_error_medical)
        
        self.logger.info("Callbacks médicos configurados")
    
    def add_to_medical_buffer(self, text):
        """Agregar texto al buffer médico con timeout inteligente"""
        try:
            # Resetear timer de inactividad
            self.last_activity_time = time.time()
            
            # Agregar al buffer
            self.medical_buffer.append(text)
            
            # Actualizar displays
            self.update_medical_buffer_display()
            self.update_status("🔴 DICTANDO", "red")
            
            # Cancelar timer anterior
            if self.buffer_timer:
                self.root.after_cancel(self.buffer_timer)
            
            # Programar auto-finalización después de pausa médica configurable
            pause_ms = int(self.medical_pause_seconds * 1000)
            self.buffer_timer = self.root.after(pause_ms, self.finalize_medical_buffer)
            
            self.logger.info(f"📝 Buffer médico: +'{text}' | Total: {len(self.medical_buffer)} segmentos")
            
        except Exception as e:
            self.logger.error(f"Error agregando al buffer médico: {e}")
    
    def finalize_medical_buffer(self):
        """Finalizar y enviar buffer médico acumulado"""
        try:
            if not self.medical_buffer:
                return
            
            # Combinar todo el buffer
            full_medical_text = " ".join(self.medical_buffer)
            
            # Limpiar y formatear
            full_medical_text = self.clean_medical_text(full_medical_text)
            
            # Mostrar en transcripciones
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.transcription_text.insert(tk.END, f"[{timestamp}] {full_medical_text}\n")
            self.transcription_text.see(tk.END)
            
            # Auto-enviar a Claude si está habilitado
            if self.config.getboolean('auto_send_to_claude'):
                self.send_to_claude_medical(full_medical_text)
            
            # Limpiar buffer
            self.medical_buffer.clear()
            self.transcription_count += 1
            
            # Actualizar estado
            self.update_status("🟢 LISTO", "green")
            self.update_medical_buffer_display()
            
            # Feedback por voz
            if self.config.getboolean('tts_enabled'):
                segment_count = len(full_medical_text.split('.'))
                self.speak_medical_feedback(f"Dictado completado. {segment_count} segmentos.")
            
            self.logger.info(f"✅ Buffer médico finalizado: {len(full_medical_text)} caracteres")
            
        except Exception as e:
            self.logger.error(f"Error finalizando buffer médico: {e}")
    
    def apply_medical_corrections(self, text):
        """Aplicar correcciones específicas de patología"""
        corrections = {
            "cloud": "Claude",
            "vasocelular": "basocelular", 
            "empleomorfismo": "pleomorfismo",
            "contexto ureasa": "test de ureasa",
            "hematoxilina y osina": "hematoxilina eosina",
            "californes": "caliciformes",
            "acrópicos": "atróficos",
            "biops": "biopsia",
            "contesteureasa": "test de ureasa",
            "conteste ureasa": "test de ureasa",
        }
        
        corrected = text
        for wrong, right in corrections.items():
            if wrong in corrected.lower():
                corrected = corrected.lower().replace(wrong, right)
                self.logger.info(f"🔧 Corrección médica: {wrong} → {right}")
        
        return corrected
    
    def clean_medical_text(self, text):
        """Limpiar y formatear texto médico final"""
        text = ' '.join(text.split())
        
        if text:
            text = text[0].upper() + text[1:]
        
        if text and not text.endswith('.'):
            text += '.'
        
        return text
    
    def speak_medical_feedback(self, message):
        """Feedback por voz con anti-acoplamiento para micrófonos lavalier"""
        if not self.config.getboolean('tts_enabled') or self.is_speaking:
            return
        
        # Anti-acoplamiento basado en tipo de micrófono
        mic_type = self.config.get('microphone_type', 'ambient')
        tts_mode = self.config.get('tts_during_dictation', 'auto')
        
        # Si estamos dictando y es micrófono lavalier, silenciar TTS
        if self.medical_buffer and mic_type == 'lavalier' and tts_mode == 'auto':
            self.logger.info(f"🔇 TTS silenciado (micrófono lavalier): {message}")
            return
        
        def medical_tts():
            try:
                self.is_speaking = True
                self.recognition_paused_for_tts = True
                
                result = self.speech_synthesizer.speak_text_async(message).get()
                if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
                    self.logger.warning(f"Error TTS médico: {result.reason}")
                    
            except Exception as e:
                self.logger.error(f"Error TTS médico: {e}")
            finally:
                self.is_speaking = False
                time.sleep(0.5)
                self.recognition_paused_for_tts = False
        
        threading.Thread(target=medical_tts, daemon=True).start()
    
    def send_to_claude_medical(self, text):
        """Enviar texto médico a Claude"""
        try:
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            claude_window_id = None
            
            for line in result.stdout.split('\n'):
                if 'Claude' in line:
                    claude_window_id = line.split()[0]
                    break
            
            if claude_window_id:
                subprocess.run(['wmctrl', '-i', '-a', claude_window_id])
                time.sleep(float(self.config.get('claude_activation_delay', 0.5)))
                
                subprocess.run(['xdotool', 'type', text])
                time.sleep(0.1)
                subprocess.run(['xdotool', 'key', 'Return'])
                
                self.log_to_gui(f"📤 Enviado a Claude: {text[:40]}...")
                self.logger.info("Texto médico enviado a Claude")
                
                if self.config.getboolean('tts_enabled'):
                    self.speak_medical_feedback("Enviado a Claude")
            else:
                self.log_to_gui("❌ Claude no encontrado")
                
        except Exception as e:
            self.logger.error(f"Error enviando a Claude: {e}")
            self.log_to_gui(f"❌ Error Claude: {e}")
    
    def start_recognition(self):
        """Iniciar reconocimiento médico"""
        if not self.is_listening and self.speech_recognizer:
            try:
                self.log_to_gui("🎤 Iniciando reconocimiento médico...")
                
                start_time = time.time()
                self.speech_recognizer.start_continuous_recognition_async()
                init_time = time.time() - start_time
                
                self.is_listening = True
                self.start_button.config(state="disabled")
                self.stop_button.config(state="normal")
                
                self.update_status("🎤 ESCUCHANDO", "blue")
                self.log_to_gui(f"✅ Reconocimiento iniciado en {init_time:.2f}s")
                self.logger.info(f"Reconocimiento médico iniciado en {init_time:.2f}s")
                
                if self.config.getboolean('tts_enabled'):
                    self.speak_medical_feedback("Sistema médico listo")
                    
            except Exception as e:
                self.logger.error(f"Error iniciando reconocimiento: {e}")
                self.log_to_gui(f"❌ Error: {e}")
                self.is_listening = False
                self.start_button.config(state="normal")
                self.stop_button.config(state="disabled")
    
    def stop_recognition(self):
        """Detener reconocimiento médico"""
        if self.is_listening:
            try:
                # Finalizar buffer pendiente
                if self.medical_buffer:
                    self.finalize_medical_buffer()
                
                self.speech_recognizer.stop_continuous_recognition_async()
                self.is_listening = False
                self.start_button.config(state="normal")
                self.stop_button.config(state="disabled")
                
                self.update_status("🟢 DETENIDO", "green")
                self.log_to_gui("⏹️ Reconocimiento detenido")
                self.logger.info("Reconocimiento médico detenido")
                
            except Exception as e:
                self.logger.error(f"Error deteniendo reconocimiento: {e}")
    
    def force_finalize_buffer(self):
        """Forzar finalización del buffer actual"""
        if self.medical_buffer:
            if self.buffer_timer:
                self.root.after_cancel(self.buffer_timer)
            self.finalize_medical_buffer()
            self.log_to_gui("✅ Buffer finalizado manualmente")
    
    def clear_medical_buffer(self):
        """Limpiar buffer médico actual"""
        self.medical_buffer.clear()
        self.update_medical_buffer_display()
        if self.buffer_timer:
            self.root.after_cancel(self.buffer_timer)
        self.update_status("🟢 LISTO", "green")
        self.log_to_gui("🗑️ Buffer médico limpiado")
    
    def setup_gui(self):
        """GUI simplificada para modo médico"""
        self.root = tk.Tk()
        self.root.title("Voice Bridge v2.0.3 FIXED - Patología Optimizada")
        self.root.geometry("750x650")
        
        style = ttk.Style()
        style.configure("Medical.TLabel", font=("Arial", 14, "bold"))
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Estado médico
        status_frame = ttk.LabelFrame(main_frame, text="🏥 Estado Médico", padding="10")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(
            status_frame, 
            text="🟢 SISTEMA MÉDICO LISTO",
            style="Medical.TLabel"
        )
        self.status_label.grid(row=0, column=0, pady=5)
        
        # Info de sesión
        self.session_info_var = tk.StringVar()
        ttk.Label(status_frame, textvariable=self.session_info_var).grid(row=1, column=0)
        
        # Controles médicos
        controls_frame = ttk.LabelFrame(main_frame, text="🎤 Controles de Voz", padding="10")
        controls_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.grid(row=0, column=0)
        
        self.start_button = ttk.Button(
            buttons_frame, 
            text="🎤 Iniciar Dictado Médico\n(Ctrl+Shift+V)", 
            command=self.start_recognition
        )
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(
            buttons_frame, 
            text="⏹️ Detener\n(Ctrl+Shift+S)", 
            command=self.stop_recognition,
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="✅ Finalizar Dictado\nActual",
            command=self.force_finalize_buffer
        ).grid(row=0, column=2, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="🗑️ Limpiar\nBuffer",
            command=self.clear_medical_buffer
        ).grid(row=0, column=3, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="⚙️ Configuración\nAvanzada",
            command=self.open_config_window
        ).grid(row=0, column=4, padx=5)
        
        # Buffer médico actual
        buffer_frame = ttk.LabelFrame(main_frame, text="📝 Dictado Médico Actual", padding="5")
        buffer_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.medical_buffer_text = scrolledtext.ScrolledText(
            buffer_frame, 
            height=4, 
            font=("Arial", 11),
            bg="lightcyan",
            wrap=tk.WORD
        )
        self.medical_buffer_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Reconocimiento en tiempo real
        partial_frame = ttk.LabelFrame(main_frame, text="🎙️ Reconocimiento Actual", padding="5")
        partial_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.partial_text_var = tk.StringVar()
        ttk.Label(
            partial_frame, 
            textvariable=self.partial_text_var,
            foreground="blue",
            font=("Arial", 10, "italic"),
            wraplength=700
        ).grid(row=0, column=0)
        
        # Transcripciones finales
        trans_frame = ttk.LabelFrame(main_frame, text="📋 Transcripciones Médicas", padding="5")
        trans_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.transcription_text = scrolledtext.ScrolledText(
            trans_frame,
            height=12,
            font=("Arial", 10)
        )
        self.transcription_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Botones de transcripción
        trans_buttons = ttk.Frame(trans_frame)
        trans_buttons.grid(row=1, column=0, pady=5)
        
        ttk.Button(trans_buttons, text="📤 Enviar a Claude", 
                  command=self.send_selected_to_claude).grid(row=0, column=0, padx=2)
        ttk.Button(trans_buttons, text="🗑️ Limpiar Todo", 
                  command=self.clear_all).grid(row=0, column=1, padx=2)
        ttk.Button(trans_buttons, text="💾 Guardar Sesión", 
                  command=self.save_session).grid(row=0, column=2, padx=2)
        
        # Log del sistema
        log_frame = ttk.LabelFrame(main_frame, text="📊 Log del Sistema", padding="5")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=3,
            font=("Courier", 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Configurar redimensionado
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Cerrar
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Iniciar actualizaciones
        self.root.after(1000, self.update_session_info)
    
    def open_config_window(self):
        """Abrir ventana de configuración avanzada"""
        config_window = tk.Toplevel(self.root)
        config_window.title("⚙️ Configuración Avanzada - Voice Bridge")
        config_window.geometry("550x700")
        config_window.resizable(False, False)
        
        config_window.transient(self.root)
        config_window.grab_set()
        
        main_config_frame = ttk.Frame(config_window, padding="15")
        main_config_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_config_frame, text="⚙️ Configuración Voice Bridge v2.0.3", 
                 font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # TIMEOUTS
        timeout_frame = ttk.LabelFrame(main_config_frame, text="⏱️ Timeouts de Dictado", padding="10")
        timeout_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Pausa médica (buffer)
        ttk.Label(timeout_frame, text="Pausa buffer médico:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.pause_var = tk.DoubleVar(value=self.medical_pause_seconds)
        pause_frame = ttk.Frame(timeout_frame)
        pause_frame.pack(fill=tk.X, pady=5)
        
        pause_scale = tk.Scale(
            pause_frame, 
            from_=1, to=10, 
            resolution=0.5,
            orient=tk.HORIZONTAL,
            variable=self.pause_var,
            command=self.on_pause_change
        )
        pause_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.pause_label = ttk.Label(pause_frame, text=f"{self.medical_pause_seconds}s")
        self.pause_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Separator(timeout_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Timeouts Azure
        ttk.Label(timeout_frame, text="⚙️ Timeouts Azure (CRÍTICO para frases largas):", 
                 font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(5, 10))
        
        # Segmentación
        ttk.Label(timeout_frame, text="🔧 Tiempo entre palabras (segmentación):").pack(anchor=tk.W)
        ttk.Label(timeout_frame, text="↳ Controla cuándo se cortan las frases largas", 
                 font=("Arial", 8), foreground="gray").pack(anchor=tk.W, padx=(10, 0))
        
        self.segmentation_var = tk.DoubleVar(value=int(self.config.get('azure_segmentation_ms', '5000'))/1000)
        seg_frame = ttk.Frame(timeout_frame)
        seg_frame.pack(fill=tk.X, pady=5)
        
        seg_scale = tk.Scale(
            seg_frame,
            from_=1, to=8,
            resolution=0.5,
            orient=tk.HORIZONTAL,
            variable=self.segmentation_var,
            command=self.on_segmentation_change
        )
        seg_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.segmentation_label = ttk.Label(seg_frame, text=f"{int(self.segmentation_var.get())}s")
        self.segmentation_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Finalización
        ttk.Label(timeout_frame, text="⏹️ Tiempo de finalización:").pack(anchor=tk.W, pady=(10, 0))
        
        self.end_silence_var = tk.DoubleVar(value=int(self.config.get('azure_end_silence_ms', '8000'))/1000)
        end_frame = ttk.Frame(timeout_frame)
        end_frame.pack(fill=tk.X, pady=5)
        
        end_scale = tk.Scale(
            end_frame,
            from_=3, to=15,
            resolution=1,
            orient=tk.HORIZONTAL,
            variable=self.end_silence_var,
            command=self.on_end_silence_change
        )
        end_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.end_silence_label = ttk.Label(end_frame, text=f"{int(self.end_silence_var.get())}s")
        self.end_silence_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Info importante
        info_text = """💡 Para dictados largos de patología, usar segmentación 5-6s"""
        ttk.Label(timeout_frame, text=info_text, 
                 font=("Arial", 8), foreground="blue").pack(anchor=tk.W, pady=(10, 0))
        
        # MICRÓFONO
        mic_frame = ttk.LabelFrame(main_config_frame, text="🎤 Tipo de Micrófono", padding="10")
        mic_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.mic_type_var = tk.StringVar(value=self.config.get('microphone_type', 'ambient'))
        
        mic_options = [
            ("🖥️ Ambient (Escritorio/PC)", "ambient"),
            ("🎧 Close (Auriculares)", "close"), 
            ("📎 Lavalier (Solapa)", "lavalier")
        ]
        
        for text, value in mic_options:
            ttk.Radiobutton(
                mic_frame, 
                text=text, 
                variable=self.mic_type_var, 
                value=value,
                command=self.on_mic_type_change
            ).pack(anchor=tk.W, pady=2)
        
        # OPCIONES GENERALES
        general_frame = ttk.LabelFrame(main_config_frame, text="🔧 Opciones", padding="10")
        general_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.auto_send_var = tk.BooleanVar(value=self.config.getboolean('auto_send_to_claude'))
        ttk.Checkbutton(
            general_frame, 
            text="📤 Auto-enviar a Claude", 
            variable=self.auto_send_var,
            command=self.on_auto_send_change
        ).pack(anchor=tk.W, pady=2)
        
        self.tts_enabled_var = tk.BooleanVar(value=self.config.getboolean('tts_enabled'))
        ttk.Checkbutton(
            general_frame, 
            text="🔊 Respuestas por voz", 
            variable=self.tts_enabled_var,
            command=self.on_tts_enabled_change
        ).pack(anchor=tk.W, pady=2)
        
        # BOTONES
        button_frame = ttk.Frame(main_config_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(
            button_frame, 
            text="🔄 Aplicar Azure",
            command=lambda: self.apply_azure_changes(config_window)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame, 
            text="💾 Guardar",
            command=lambda: self.save_config(config_window)
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(
            button_frame, 
            text="❌ Cerrar",
            command=config_window.destroy
        ).pack(side=tk.RIGHT)
    
    def on_pause_change(self, value):
        """Cambio en pausa médica"""
        new_value = float(value)
        self.pause_label.config(text=f"{new_value}s")
        self.medical_pause_seconds = new_value
        self.config['medical_pause_seconds'] = str(new_value)
    
    def on_segmentation_change(self, value):
        """Cambio en segmentación Azure"""
        new_value_s = float(value)
        new_value_ms = int(new_value_s * 1000)
        self.segmentation_label.config(text=f"{int(new_value_s)}s")
        self.config['azure_segmentation_ms'] = str(new_value_ms)
        self.logger.info(f"⚙️ Segmentación: {new_value_s}s")
    
    def on_end_silence_change(self, value):
        """Cambio en finalización Azure"""
        new_value_s = float(value)
        new_value_ms = int(new_value_s * 1000)
        self.end_silence_label.config(text=f"{int(new_value_s)}s")
        self.config['azure_end_silence_ms'] = str(new_value_ms)
        self.logger.info(f"⚙️ Finalización: {new_value_s}s")
    
    def on_mic_type_change(self):
        """Cambio en micrófono"""
        new_type = self.mic_type_var.get()
        self.config['microphone_type'] = new_type
        self.logger.info(f"⚙️ Micrófono: {new_type}")
    
    def on_auto_send_change(self):
        """Cambio en auto-envío"""
        new_value = self.auto_send_var.get()
        self.config['auto_send_to_claude'] = str(new_value).lower()
    
    def on_tts_enabled_change(self):
        """Cambio en TTS"""
        new_value = self.tts_enabled_var.get()
        self.config['tts_enabled'] = str(new_value).lower()
    
    def apply_azure_changes(self, parent_window):
        """Aplicar cambios Azure reiniciando"""
        try:
            was_listening = self.is_listening
            
            if was_listening:
                self.stop_recognition()
                time.sleep(0.5)
            
            self.cleanup_and_setup_azure()
            
            if was_listening:
                time.sleep(0.5)
                self.start_recognition()
            
            seg_timeout = int(self.config.get('azure_segmentation_ms', '5000'))//1000
            self.log_to_gui(f"🔄 Azure reconfigurado: segmentación={seg_timeout}s")
            
            messagebox.showinfo(
                "Azure Aplicado",
                f"✅ Timeouts Azure actualizados:\n\n🔧 Segmentación: {seg_timeout}s\n\nAhora deberías poder dictar frases más largas.",
                parent=parent_window
            )
            
        except Exception as e:
            self.logger.error(f"Error aplicando Azure: {e}")
            messagebox.showerror("Error", f"Error: {e}", parent=parent_window)
    
    def save_config(self, config_window):
        """Guardar configuración"""
        try:
            config_file = Path.home() / "voice-bridge-claude" / "config" / "voice_bridge_config.ini"
            
            config_parser = configparser.ConfigParser()
            config_parser['DEFAULT'] = dict(self.config)
            
            with open(config_file, 'w') as f:
                config_parser.write(f)
            
            self.log_to_gui("💾 Configuración guardada")
            messagebox.showinfo("Guardado", "✅ Configuración guardada exitosamente", parent=config_window)
            config_window.destroy()
            
        except Exception as e:
            self.logger.error(f"Error guardando: {e}")
            messagebox.showerror("Error", f"Error guardando: {e}", parent=config_window)
    
    # MÉTODOS AUXILIARES
    
    def update_status(self, text, color="black"):
        """Actualizar estado médico"""
        try:
            self.status_label.config(text=text)
            color_map = {"red": "red", "green": "green", "blue": "blue", "orange": "orange"}
            self.status_label.config(foreground=color_map.get(color, "black"))
        except:
            pass
    
    def update_medical_buffer_display(self):
        """Actualizar display del buffer"""
        try:
            self.medical_buffer_text.delete(1.0, tk.END)
            if self.medical_buffer:
                display_text = " ".join(self.medical_buffer)
                self.medical_buffer_text.insert(1.0, display_text)
                self.medical_buffer_text.see(tk.END)
        except:
            pass
    
    def update_partial_text(self, text):
        """Actualizar texto parcial"""
        try:
            display_text = text[:200] + "..." if len(text) > 200 else text
            self.partial_text_var.set(display_text)
        except:
            pass
    
    def update_session_info(self):
        """Actualizar info de sesión"""
        try:
            duration = datetime.now() - self.session_start
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            buffer_count = len(self.medical_buffer)
            buffer_info = f"Buffer: {buffer_count} segmentos" if buffer_count > 0 else "Buffer vacío"
            
            info = (f"Sesión: {hours:02d}:{minutes:02d}:{seconds:02d} | "
                    f"Transcripciones: {self.transcription_count} | {buffer_info}")
            
            self.session_info_var.set(info)
        except:
            pass
        finally:
            self.root.after(1000, self.update_session_info)
    
    def log_to_gui(self, message):
        """Log a GUI"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            
            lines = self.log_text.get(1.0, tk.END).count('\n')
            if lines > 50:
                self.log_text.delete(1.0, "10.0")
        except:
            pass
    
    def load_medical_terms(self):
        """Cargar términos médicos"""
        try:
            self.medical_terms = []
            dict_dir = Path.home() / "voice-bridge-claude" / "config" / "diccionarios"
            
            for dict_file in ["frases_completas.txt", "patologia_molecular.txt"]:
                dict_path = dict_dir / dict_file
                if dict_path.exists():
                    with open(dict_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                self.medical_terms.append(line.lower())
            
            self.logger.info(f"Términos médicos: {len(self.medical_terms)}")
        except Exception as e:
            self.logger.error(f"Error cargando términos: {e}")
    
    def setup_hotkeys(self):
        """Hotkeys médicos"""
        try:
            self.pressed_keys = set()
            
            self.hotkey_listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.hotkey_listener.start()
            
            self.logger.info("Hotkeys médicos configurados")
        except Exception as e:
            self.logger.error(f"Error hotkeys: {e}")
    
    def on_key_press(self, key):
        """Procesar hotkeys"""
        try:
            self.pressed_keys.add(key)
            
            ctrl_shift_v = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_char('v')}
            ctrl_shift_s = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_char('s')}
            ctrl_shift_f = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode.from_char('f')}
            
            if self.pressed_keys >= ctrl_shift_v:
                self.root.after_idle(self.start_recognition)
            elif self.pressed_keys >= ctrl_shift_s:
                self.root.after_idle(self.stop_recognition)
            elif self.pressed_keys >= ctrl_shift_f:
                self.root.after_idle(self.force_finalize_buffer)
        except:
            pass
    
    def on_key_release(self, key):
        """Release hotkeys"""
        try:
            self.pressed_keys.discard(key)
        except:
            pass
    
    def send_selected_to_claude(self):
        """Enviar selección a Claude"""
        try:
            try:
                selected = self.transcription_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                selected = self.transcription_text.get(1.0, tk.END).strip()
            
            if selected:
                self.send_to_claude_medical(selected)
            else:
                self.log_to_gui("⚠️ No hay texto")
        except Exception as e:
            self.logger.error(f"Error enviando: {e}")
    
    def clear_all(self):
        """Limpiar todo"""
        self.transcription_text.delete(1.0, tk.END)
        self.medical_buffer.clear()
        self.update_medical_buffer_display()
        self.partial_text_var.set("")
        self.transcription_count = 0
        if self.buffer_timer:
            self.root.after_cancel(self.buffer_timer)
        self.log_to_gui("🗑️ Todo limpiado")
    
    def save_session(self):
        """Guardar sesión médica"""
        try:
            content = self.transcription_text.get(1.0, tk.END).strip()
            if not content:
                self.log_to_gui("⚠️ No hay transcripciones")
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sesion_medica_v203_fixed_{timestamp}.txt"
            
            save_dir = Path.home() / "voice-bridge-claude" / "logs"
            save_dir.mkdir(parents=True, exist_ok=True)
            save_path = save_dir / filename
            
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(f"# Sesión Médica Voice Bridge v2.0.3 FIXED\n")
                f.write(f"# Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Transcripciones: {self.transcription_count}\n\n")
                f.write(content)
            
            self.log_to_gui(f"💾 Sesión guardada: {filename}")
            self.logger.info(f"Sesión guardada: {save_path}")
            
        except Exception as e:
            self.logger.error(f"Error guardando sesión: {e}")
    
    def on_closing(self):
        """Cerrar aplicación"""
        try:
            if self.is_listening:
                self.stop_recognition()
            
            if hasattr(self, 'hotkey_listener'):
                self.hotkey_listener.stop()
            
            # Auto-guardar
            content = self.transcription_text.get(1.0, tk.END).strip()
            if content:
                try:
                    self.save_session()
                except:
                    pass
            
            self.logger.info("Voice Bridge v2.0.3 FIXED cerrado")
            self.root.destroy()
            
        except:
            self.root.destroy()
    
    def run(self):
        """Ejecutar aplicación"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()

def main():
    """Función principal"""
    try:
        if not os.environ.get('AZURE_SPEECH_KEY'):
            print("❌ ERROR: AZURE_SPEECH_KEY no configurado")
            return
        
        app = VoiceBridgeV203Fixed()
        app.run()
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
