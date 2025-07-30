#!/usr/bin/env python3
"""
Voice Bridge v2.1.3 - MODO OSCURO + UI MEJORADA
Versión con modo oscuro y mejoras visuales para uso con microscopio

MEJORAS UI v2.1.3 OSCURO:
1. 🌙 Modo oscuro completo para microscopía
2. 🎨 Fondo gris sutil en modo claro
3. 🔲 Botones circulares con solo íconos
4. 📝 Fuentes antialiasing mejorado
5. 🌍 Opción idioma español
6. 📐 Layout optimizado: botones izquierda, reconocimiento centro
7. 💬 Tooltips informativos
8. 🧹 Sin signos "?" en títulos
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
import gc
import re
from collections import deque, Counter
from difflib import SequenceMatcher

# Configurar pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

class AdvancedThemeSystem:
    """Sistema de temas avanzado con modo oscuro y claro - UI MÉDICA"""
    
    def __init__(self):
        # Detectar fuentes disponibles
        self.available_fonts = self.detect_system_fonts()
        self.selected_fonts = self.select_best_fonts()
        
        # Estado del tema
        self.current_theme = 'light'  # 'light' o 'dark'
        self.current_language = 'en'  # 'en' o 'es'
        
        # Definir todos los temas
        self.themes = {
            'light': self.create_light_theme(),
            'dark': self.create_dark_theme()
        }
        
        # Textos en múltiples idiomas
        self.texts = {
            'en': self.create_english_texts(),
            'es': self.create_spanish_texts()
        }
        
        # Crear configuraciones de fuente mejoradas
        self.fonts = self.create_improved_font_configs()
        
        print(f"🎨 Advanced Theme System initialized:")
        print(f"   🌙 Theme: {self.current_theme}")
        print(f"   🌍 Language: {self.current_language}")
        print(f"   📝 Font: {self.selected_fonts['primary']}")
    
    def detect_system_fonts(self):
        """Detectar fuentes disponibles del sistema"""
        try:
            root_temp = tk.Tk()
            root_temp.withdraw()
            available = list(font.families())
            root_temp.destroy()
            return set(available)
        except:
            return {'Arial', 'Courier New', 'Times New Roman'}
    
    def select_best_fonts(self):
        """Seleccionar las mejores fuentes con antialiasing"""
        font_hierarchy = {
            'primary_fonts': [
                'Segoe UI', 'San Francisco', 'Inter', 'Roboto',
                'Ubuntu', 'DejaVu Sans', 'Liberation Sans', 'Arial'
            ],
            'mono_fonts': [
                'Consolas', 'Monaco', 'SF Mono', 'Fira Code',
                'Ubuntu Mono', 'DejaVu Sans Mono', 'Liberation Mono', 'Courier New'
            ]
        }
        
        selected = {}
        
        # Fuente principal
        for font_name in font_hierarchy['primary_fonts']:
            if font_name in self.available_fonts:
                selected['primary'] = font_name
                break
        else:
            selected['primary'] = 'Arial'
        
        # Fuente monospace
        for font_name in font_hierarchy['mono_fonts']:
            if font_name in self.available_fonts:
                selected['mono'] = font_name
                break
        else:
            selected['mono'] = 'Courier New'
        
        return selected
    
    def create_light_theme(self):
        """Tema claro mejorado"""
        return {
            # Fondo principal gris sutil para destacar tarjetas blancas
            'bg_main': '#f8f9fa',          # Gris muy claro (era #ffffff)
            'bg_surface': '#ffffff',       # Blanco para tarjetas
            'bg_card': '#ffffff',          # Blanco para contenido
            'bg_hover': '#f3f4f6',         # Hover sutil
            'bg_accent': '#f0f9ff',        # Azul muy sutil
            
            # Textos optimizados
            'text_primary': '#1f2937',     # Negro principal
            'text_secondary': '#6b7280',   # Gris medio
            'text_muted': '#9ca3af',       # Gris claro
            'text_accent': '#2563eb',      # Azul acentos
            'text_white': '#ffffff',       # Blanco para botones
            
            # Colores de estado médico
            'success': '#10b981',          # Verde médico
            'warning': '#f59e0b',          # Amarillo advertencia
            'danger': '#ef4444',           # Rojo error
            'primary': '#2563eb',          # Azul principal
            'info': '#8b5cf6',             # Púrpura info
            
            # Colores de botones específicos
            'btn_start': '#22c55e',        # Verde start
            'btn_stop': '#ef4444',         # Rojo stop
            'btn_pause': '#eab308',        # Amarillo pause
            'btn_config': '#94a3b8',       # Gris config
            'btn_stats': '#3b82f6',        # Azul stats
            'btn_trash': '#6b7280',        # Gris oscuro trash
            
            # Bordes y sombras
            'border_light': '#e5e7eb',
            'border_medium': '#d1d5db',
            'shadow': 'rgba(0, 0, 0, 0.1)',
        }
    
    def create_dark_theme(self):
        """Tema oscuro para uso con microscopio"""
        return {
            # Fondos oscuros para reducir reflejos
            'bg_main': '#111827',          # Gris muy oscuro principal
            'bg_surface': '#1f2937',       # Gris oscuro para tarjetas
            'bg_card': '#374151',          # Gris medio para contenido
            'bg_hover': '#4b5563',         # Hover oscuro
            'bg_accent': '#1e3a8a',        # Azul oscuro
            
            # Textos para modo oscuro
            'text_primary': '#f9fafb',     # Blanco principal
            'text_secondary': '#d1d5db',   # Gris claro
            'text_muted': '#9ca3af',       # Gris medio
            'text_accent': '#60a5fa',      # Azul claro acentos
            'text_white': '#ffffff',       # Blanco puro
            
            # Estados médicos en modo oscuro
            'success': '#34d399',          # Verde claro
            'warning': '#fbbf24',          # Amarillo claro
            'danger': '#f87171',           # Rojo claro
            'primary': '#60a5fa',          # Azul claro
            'info': '#a78bfa',             # Púrpura claro
            
            # Botones modo oscuro
            'btn_start': '#10b981',        # Verde start oscuro
            'btn_stop': '#ef4444',         # Rojo stop
            'btn_pause': '#f59e0b',        # Amarillo pause
            'btn_config': '#6b7280',       # Gris config
            'btn_stats': '#3b82f6',        # Azul stats
            'btn_trash': '#4b5563',        # Gris trash
            
            # Bordes modo oscuro
            'border_light': '#374151',
            'border_medium': '#4b5563',
            'shadow': 'rgba(0, 0, 0, 0.3)',
        }
    
    def create_english_texts(self):
        """Textos en inglés"""
        return {
            'title': "Medical AI System",
            'subtitle': "Intelligent medical dictation powered by Azure AI",
            'status_ready': "Medical AI System Ready",
            'status_listening': "Listening with Medical AI",
            'status_dictating': "Dictating Medical Content",
            'controls_title': "Voice Controls",
            'live_title': "Live Recognition",
            'active_recognition': "Active Recognition",
            'medical_buffer': "Current Medical Buffer",
            'corrections': "Contextual Corrections",
            'transcriptions_title': "Medical Transcriptions",
            'session_title': "Session Overview",
            'live_metrics': "Live Metrics",
            'session_info': "Session Info",
            'ai_suggestions': "AI Suggestions",
            'system_log': "System Log",
            'footer': "Voice Bridge v2.1.3 • Medical AI Assistant",
            
            # Botones tooltips
            'btn_start_tooltip': "Start Medical Dictation (Ctrl+Shift+V)",
            'btn_stop_tooltip': "Stop Recognition System (Ctrl+Shift+S)",
            'btn_finalize_tooltip': "Finalize Current Buffer (Ctrl+Shift+F)",
            'btn_clear_tooltip': "Clear Medical Buffer",
            'btn_config_tooltip': "Configuration Settings",
            'btn_stats_tooltip': "Session Statistics",
            'btn_send_tooltip': "Send to Claude",
            'btn_clear_all_tooltip': "Clear All Transcriptions",
            'btn_save_tooltip': "Save Session",
            
            # Métricas
            'dictations': "Dictations",
            'corrections': "Corrections",
            'speed': "Speed",
            'accuracy': "Accuracy",
            
            # Configuración
            'config_title': "Medical AI Configuration",
            'config_subtitle': "Configure timeouts, theme, language and medical settings",
            'theme_section': "Theme & Language",
            'theme_mode': "Interface Theme:",
            'language_option': "Interface Language:",
            'light_mode': "Light Mode",
            'dark_mode': "Dark Mode (Microscopy)",
            'lang_english': "English",
            'lang_spanish': "Español",
        }
    
    def create_spanish_texts(self):
        """Textos en español"""
        return {
            'title': "Sistema de IA Médica",
            'subtitle': "Dictado médico inteligente con tecnología Azure AI",
            'status_ready': "Sistema de IA Médica Listo",
            'status_listening': "Escuchando con IA Médica",
            'status_dictating': "Dictando Contenido Médico",
            'controls_title': "Controles de Voz",
            'live_title': "Reconocimiento en Vivo",
            'active_recognition': "Reconocimiento Activo",
            'medical_buffer': "Buffer Médico Actual",
            'corrections': "Correcciones Contextuales",
            'transcriptions_title': "Transcripciones Médicas",
            'session_title': "Resumen de Sesión",
            'live_metrics': "Métricas en Vivo",
            'session_info': "Información de Sesión",
            'ai_suggestions': "Sugerencias de IA",
            'system_log': "Log del Sistema",
            'footer': "Voice Bridge v2.1.3 • Asistente de IA Médica",
            
            # Botones tooltips
            'btn_start_tooltip': "Iniciar Dictado Médico (Ctrl+Shift+V)",
            'btn_stop_tooltip': "Detener Sistema de Reconocimiento (Ctrl+Shift+S)",
            'btn_finalize_tooltip': "Finalizar Buffer Actual (Ctrl+Shift+F)",
            'btn_clear_tooltip': "Limpiar Buffer Médico",
            'btn_config_tooltip': "Configuración del Sistema",
            'btn_stats_tooltip': "Estadísticas de Sesión",
            'btn_send_tooltip': "Enviar a Claude",
            'btn_clear_all_tooltip': "Limpiar Todas las Transcripciones",
            'btn_save_tooltip': "Guardar Sesión",
            
            # Métricas
            'dictations': "Dictados",
            'corrections': "Correcciones",
            'speed': "Velocidad",
            'accuracy': "Precisión",
            
            # Configuración
            'config_title': "Configuración de IA Médica",
            'config_subtitle': "Configurar timeouts, tema, idioma y ajustes médicos",
            'theme_section': "Tema e Idioma",
            'theme_mode': "Tema de Interfaz:",
            'language_option': "Idioma de Interfaz:",
            'light_mode': "Modo Claro",
            'dark_mode': "Modo Oscuro (Microscopía)",
            'lang_english': "English",
            'lang_spanish': "Español",
        }
    
    def create_improved_font_configs(self):
        """Configuraciones de fuente mejoradas con antialiasing ULTRA"""
        # Configurar antialiasing del sistema
        try:
            import os
            os.environ['TK_SILENCE_DEPRECATION'] = '1'
        except:
            pass
            
        return {
            # Títulos con antialiasing ULTRA mejorado
            'title_large': (self.selected_fonts['primary'], 20, 'bold'),
            'title_medium': (self.selected_fonts['primary'], 15, 'bold'),
            'subtitle': (self.selected_fonts['primary'], 12, 'bold'),
            
            # Texto principal con mayor nitidez
            'body_large': (self.selected_fonts['primary'], 11, 'normal'),
            'body_normal': (self.selected_fonts['primary'], 10, 'normal'),
            'body_bold': (self.selected_fonts['primary'], 10, 'bold'),
            'body_small': (self.selected_fonts['primary'], 9, 'normal'),
            'caption': (self.selected_fonts['primary'], 8, 'normal'),
            
            # Código y técnico más nítido
            'code': (self.selected_fonts['mono'], 9, 'normal'),
            'code_bold': (self.selected_fonts['mono'], 9, 'bold'),
            
            # Botones más nítidos
            'button_large': (self.selected_fonts['primary'], 10, 'bold'),
            'button_normal': (self.selected_fonts['primary'], 9, 'bold'),
            'button_small': (self.selected_fonts['primary'], 8, 'bold'),
        }
    
    def get_colors(self):
        """Obtener colores del tema actual"""
        return self.themes[self.current_theme]
    
    def get_texts(self):
        """Obtener textos del idioma actual"""
        return self.texts[self.current_language]
    
    def get_font(self, key):
        """Obtener fuente por clave"""
        return self.fonts.get(key, self.fonts['body_normal'])
    
    def set_theme(self, theme):
        """Cambiar tema"""
        if theme in self.themes:
            self.current_theme = theme
    
    def set_language(self, language):
        """Cambiar idioma"""
        if language in self.texts:
            self.current_language = language

class ToolTip:
    """Tooltip mejorado para botones"""
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.timer = None
        
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<Motion>", self.on_motion)
    
    def on_enter(self, event=None):
        """Mouse entra al widget"""
        self.cancel_timer()
        self.timer = self.widget.after(self.delay, self.show_tooltip)
    
    def on_leave(self, event=None):
        """Mouse sale del widget"""
        self.cancel_timer()
        self.hide_tooltip()
    
    def on_motion(self, event=None):
        """Mouse se mueve sobre el widget"""
        self.cancel_timer()
        self.timer = self.widget.after(self.delay, self.show_tooltip)
    
    def cancel_timer(self):
        """Cancelar timer del tooltip"""
        if self.timer:
            self.widget.after_cancel(self.timer)
            self.timer = None
    
    def show_tooltip(self):
        """Mostrar tooltip"""
        if self.tooltip_window or not self.text:
            return
        
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#333333",
            foreground="white",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Arial", 9, "normal"),
            padx=8,
            pady=4
        )
        label.pack()
    
    def hide_tooltip(self):
        """Ocultar tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

# [MANTENER CLASES DE LÓGICA MÉDICA IDÉNTICAS - NO CAMBIAR]
class MedicalContextCorrector:
    """Corrector contextual inteligente - IDÉNTICO"""
    
    def __init__(self):
        self.load_medical_context_rules()
        self.specialties = {
            'pathology': ['biopsia', 'histologia', 'citologia', 'inmunohistoquimica'],
            'gastroenterology': ['gastritis', 'mucosa', 'helicobacter', 'metaplasia'],
            'oncology': ['carcinoma', 'adenocarcinoma', 'neoplasia', 'tumor'],
            'general': ['claude', 'observo', 'paciente', 'diagnostico']
        }
        self.current_specialty = 'general'
        self.context_history = deque(maxlen=5)
    
    def load_medical_context_rules(self):
        self.context_rules = {
            'pathology_context': {
                'triggers': ['biopsia', 'histologia', 'tejido', 'muestra'],
                'corrections': {
                    'cloud': 'Claude', 'vasocelular': 'basocelular',
                    'empleomorfismo': 'pleomorfismo', 'células a típicas': 'células atípicas',
                    'hiperqueratósis': 'hiperqueratosis', 'invasión vocal': 'invasión focal'
                }
            },
            'gastro_context': {
                'triggers': ['gastritis', 'mucosa', 'gástric', 'duodeno'],
                'corrections': {
                    'contesteureasa': 'test de ureasa', 'conteste ureasa': 'test de ureasa',
                    'helicobacter spp': 'Helicobacter spp', 'califormes': 'caliciformes',
                    'acrópicos': 'atróficos', 'olga estadio': 'OLGA estadio'
                }
            }
        }
    
    def detect_specialty(self, text):
        text_lower = text.lower()
        specialty_scores = {}
        for specialty, keywords in self.specialties.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            specialty_scores[specialty] = score
        
        if specialty_scores:
            detected = max(specialty_scores, key=specialty_scores.get)
            if specialty_scores[detected] > 0:
                self.current_specialty = detected
                return detected
        return self.current_specialty
    
    def get_contextual_corrections(self, text):
        specialty = self.detect_specialty(text)
        corrected_text = text
        applied_corrections = []
        
        general_corrections = {'cloud': 'Claude', 'bimbo': 'veo', 'observó': 'observo'}
        
        for wrong, right in general_corrections.items():
            if wrong in corrected_text.lower():
                corrected_text = re.sub(re.escape(wrong), right, corrected_text, flags=re.IGNORECASE)
                applied_corrections.append(f"{wrong} → {right}")
        
        for context_name, context_data in self.context_rules.items():
            triggers_found = any(trigger in text.lower() for trigger in context_data['triggers'])
            if triggers_found or specialty in context_name:
                for wrong, right in context_data['corrections'].items():
                    if wrong in corrected_text.lower():
                        corrected_text = re.sub(re.escape(wrong), right, corrected_text, flags=re.IGNORECASE)
                        applied_corrections.append(f"{wrong} → {right}")
        
        self.context_history.append({
            'text': text[:50], 'specialty': specialty,
            'corrections': applied_corrections, 'timestamp': datetime.now()
        })
        
        return corrected_text, applied_corrections, specialty

class AdvancedRepetitionDetector:
    """Detector de repeticiones - IDÉNTICO"""
    
    def __init__(self, similarity_threshold=0.8, time_window_seconds=30):
        self.similarity_threshold = similarity_threshold
        self.time_window_seconds = time_window_seconds
        self.recent_phrases = deque(maxlen=10)
        self.phrase_patterns = Counter()
        
    def calculate_similarity(self, text1, text2):
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def is_repetition(self, new_text):
        if not new_text or len(new_text.strip()) < 3:
            return False
            
        new_text_clean = new_text.lower().strip()
        current_time = time.time()
        
        self.recent_phrases = deque([
            phrase for phrase in self.recent_phrases 
            if current_time - phrase['timestamp'] <= self.time_window_seconds
        ], maxlen=10)
        
        for phrase_data in self.recent_phrases:
            similarity = self.calculate_similarity(new_text_clean, phrase_data['text'])
            if similarity >= self.similarity_threshold:
                phrase_data['repetition_count'] += 1
                return {
                    'is_repetition': True, 'similarity': similarity,
                    'original': phrase_data['text'], 'method': 'similarity',
                    'count': phrase_data['repetition_count']
                }
        
        self.recent_phrases.append({
            'text': new_text_clean, 'timestamp': current_time, 'repetition_count': 0
        })
        
        return {'is_repetition': False, 'method': 'new_phrase'}

class SmartStatsCollector:
    """Estadísticas inteligentes - IDÉNTICO"""
    
    def __init__(self):
        self.session_start = datetime.now()
        self.stats = {
            'total_phrases': 0, 'total_characters': 0, 'corrections_applied': 0,
            'repetitions_detected': 0, 'avg_phrase_length': 0,
            'specialties_detected': Counter(), 'most_common_corrections': Counter(),
            'recognition_quality': [], 'pause_patterns': []
        }
    
    def record_phrase(self, text, corrections, specialty, pause_duration):
        self.stats['total_phrases'] += 1
        self.stats['total_characters'] += len(text)
        self.stats['corrections_applied'] += len(corrections)
        self.stats['specialties_detected'][specialty] += 1
        self.stats['pause_patterns'].append(pause_duration)
        
        for correction in corrections:
            self.stats['most_common_corrections'][correction] += 1
        
        self.stats['avg_phrase_length'] = self.stats['total_characters'] / self.stats['total_phrases']
    
    def record_repetition(self, repetition_data):
        self.stats['repetitions_detected'] += 1
    
    def get_optimization_suggestions(self):
        suggestions = []
        if len(self.stats['pause_patterns']) > 5:
            avg_pause = sum(self.stats['pause_patterns']) / len(self.stats['pause_patterns'])
            if avg_pause < 3:
                suggestions.append({
                    'type': 'timeout',
                    'message': f"Sugerencia: Reducir timeout a {avg_pause + 1:.1f}s",
                    'recommended_value': avg_pause + 1
                })
        return suggestions
    
    def get_session_summary(self):
        duration = datetime.now() - self.session_start
        return {
            'duration': str(duration).split('.')[0],
            'phrases_per_minute': self.stats['total_phrases'] / (duration.seconds / 60) if duration.seconds > 0 else 0,
            'characters_per_minute': self.stats['total_characters'] / (duration.seconds / 60) if duration.seconds > 0 else 0,
            'correction_rate': (self.stats['corrections_applied'] / self.stats['total_phrases'] * 100) if self.stats['total_phrases'] > 0 else 0,
            'repetition_rate': (self.stats['repetitions_detected'] / self.stats['total_phrases'] * 100) if self.stats['total_phrases'] > 0 else 0,
            **self.stats
        }

# CLASE PRINCIPAL CON TEMA OSCURO Y UI MEJORADA
class VoiceBridgeV213Advanced:
    def __init__(self):
        """Voice Bridge v2.1.3 - MODO OSCURO + UI AVANZADA"""
        self.setup_logging()
        self.logger.info("=== Voice Bridge v2.1.3 - MODO OSCURO + UI AVANZADA ===")
        
        # Sistema de temas avanzado
        self.theme_system = AdvancedThemeSystem()
        
        # Configuración
        self.config = self.load_config()
        
        # Cargar preferencias de tema e idioma
        self.load_ui_preferences()
        
        # Componentes inteligentes (heredados idénticos)
        self.medical_corrector = MedicalContextCorrector()
        self.repetition_detector = AdvancedRepetitionDetector()
        self.stats_collector = SmartStatsCollector()
        
        # Estado del sistema
        self.is_listening = False
        self.is_speaking = False
        self.recognition_paused_for_tts = False
        self.medical_buffer = []
        self.last_activity_time = None
        self.medical_pause_seconds = float(self.config.get('medical_pause_seconds', '6'))
        self.buffer_timer = None
        
        # Azure objects
        self.speech_config = None
        self.speech_recognizer = None
        self.speech_synthesizer = None
        
        # Colas
        self.transcription_queue = queue.Queue()
        
        # Setup componentes
        self.setup_advanced_gui()
        self.cleanup_and_setup_azure()
        self.load_medical_terms()
        self.setup_hotkeys()
        
        # Sesión
        self.session_start = datetime.now()
        self.transcription_count = 0
        
        self.logger.info("Voice Bridge v2.1.3 MODO OSCURO iniciado")
        self.log_to_gui("🌙 Voice Bridge v2.1.3 - Dark Mode + Advanced UI")
        
        # Iniciar actualizaciones
        self.start_advanced_updates()
    
    def setup_logging(self):
        """Logging avanzado"""
        log_dir = Path.home() / "voice-bridge-claude" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"voice_bridge_v213_advanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Log v2.1.3 AVANZADO iniciado: {log_file}")
    
    def load_config(self):
        """Configuración con opciones avanzadas"""
        config = configparser.ConfigParser()
        
        default_config = {
            # Configuración base
            'azure_speech_key': os.environ.get('AZURE_SPEECH_KEY', ''),
            'azure_region': os.environ.get('AZURE_SPEECH_REGION', 'eastus'),
            'speech_language': 'es-CO', 'tts_voice': 'es-CO-SalomeNeural',
            'auto_send_to_claude': 'false', 'tts_enabled': 'true',
            'claude_activation_delay': '0.5', 'medical_pause_seconds': '6',
            'microphone_type': 'ambient', 'auto_correct_medical': 'true',
            'azure_initial_silence_ms': '10000', 'azure_end_silence_ms': '10000',
            'azure_segmentation_ms': '6000', 'contextual_correction': 'true',
            'advanced_repetition_detection': 'true', 'smart_stats_collection': 'true',
            'auto_optimization_suggestions': 'true', 'similarity_threshold': '0.8',
            'repetition_time_window': '30', 'show_correction_details': 'true',
            'show_performance_stats': 'true',
            
            # Nuevas opciones UI v2.1.3
            'ui_theme': 'light', 'ui_language': 'en',
            'rounded_buttons': 'true', 'show_tooltips': 'true',
            'antialiasing': 'true'
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
    
    def load_ui_preferences(self):
        """Cargar preferencias de UI"""
        theme = self.config.get('ui_theme', 'light')
        language = self.config.get('ui_language', 'en')
        
        self.theme_system.set_theme(theme)
        self.theme_system.set_language(language)
        
        self.logger.info(f"UI Preferences: {theme} theme, {language} language")
    
    def save_ui_preferences(self):
        """Guardar preferencias de UI"""
        self.config['ui_theme'] = self.theme_system.current_theme
        self.config['ui_language'] = self.theme_system.current_language
        
        # Guardar a archivo
        try:
            config_file = Path.home() / "voice-bridge-claude" / "config" / "voice_bridge_config.ini"
            config_parser = configparser.ConfigParser()
            config_parser['DEFAULT'] = dict(self.config)
            
            with open(config_file, 'w') as f:
                config_parser.write(f)
                
        except Exception as e:
            self.logger.error(f"Error saving UI preferences: {e}")
    
    def setup_advanced_gui(self):
        """GUI avanzada con tema oscuro y antialiasing mejorado"""
        self.root = tk.Tk()
        
        # CONFIGURAR ANTIALIASING ULTRA
        try:
            # Forzar antialiasing del sistema
            self.root.tk.call('tk', 'scaling', 1.0)
            self.root.option_add('*font', f'{self.theme_system.selected_fonts["primary"]} 10')
            # Activar renderizado suave de fuentes
            self.root.tk.call('tk', 'fontchooser', 'configure', '-parent', self.root)
        except:
            pass
        
        # Configurar ventana principal
        texts = self.theme_system.get_texts()
        self.root.title(f"Voice Bridge v2.1.3 - {texts['title']}")
        self.root.geometry("1300x900")
        self.root.minsize(1100, 700)
        
        # Aplicar colores del tema
        colors = self.theme_system.get_colors()
        self.root.configure(bg=colors['bg_main'])
        
        # CONTAINER PRINCIPAL con tema aplicado
        main_container = tk.Frame(
            self.root, 
            bg=colors['bg_main'],
            padx=25, pady=20
        )
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # CREAR LAYOUT AVANZADO
        self.create_advanced_header(main_container)
        self.create_advanced_main_content(main_container)
        self.create_advanced_footer(main_container)
        
        # EVENT HANDLERS
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # UPDATES
        self.root.after(1000, self.update_advanced_session_info)
    
    def create_advanced_header(self, parent):
        """Header avanzado con tema - SIN SIGNOS EXTRAÑOS"""
        colors = self.theme_system.get_colors()
        texts = self.theme_system.get_texts()
        
        header_frame = tk.Frame(parent, bg=colors['bg_main'])
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        # TÍTULO PRINCIPAL - LIMPIO
        title_label = tk.Label(
            header_frame,
            text=f"🏥 {texts['title']}",
            font=self.theme_system.get_font('title_large'),
            fg=colors['text_primary'],
            bg=colors['bg_main']
        )
        title_label.pack(pady=(0, 5))
        
        # SUBTÍTULO - LIMPIO
        subtitle_label = tk.Label(
            header_frame,
            text=f"{texts['subtitle']} • v2.1.3 Advanced UI • {self.theme_system.selected_fonts['primary']} Font",
            font=self.theme_system.get_font('body_normal'),
            fg=colors['text_secondary'],
            bg=colors['bg_main']
        )
        subtitle_label.pack(pady=(0, 20))
        
        # ESTADO PRINCIPAL
        self.main_status_label = tk.Label(
            header_frame,
            text=f"🟢 {texts['status_ready']}",
            font=self.theme_system.get_font('subtitle'),
            fg=colors['success'],
            bg=colors['bg_main']
        )
        self.main_status_label.pack()
    
    def create_advanced_main_content(self, parent):
        """Contenido principal con layout optimizado"""
        colors = self.theme_system.get_colors()
        
        content_frame = tk.Frame(parent, bg=colors['bg_main'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # LAYOUT OPTIMIZADO: Botones izquierda, reconocimiento centro, sidebar derecha
        
        # COLUMNA IZQUIERDA - Botones de control (más estrecha)
        left_column = tk.Frame(content_frame, bg=colors['bg_main'], width=120)
        left_column.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        left_column.pack_propagate(False)
        
        # COLUMNA CENTRAL - Área principal de reconocimiento (más ancha)
        center_column = tk.Frame(content_frame, bg=colors['bg_main'])
        center_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        # COLUMNA DERECHA - Panel lateral (igual)
        right_column = tk.Frame(content_frame, bg=colors['bg_surface'], width=300)
        right_column.pack(side=tk.RIGHT, fill=tk.Y)
        right_column.pack_propagate(False)
        
        # CREAR SECCIONES OPTIMIZADAS
        self.create_advanced_controls(left_column)
        self.create_advanced_live_feedback(center_column)
        self.create_advanced_transcriptions(center_column)
        self.create_advanced_sidebar(right_column)
    
    def create_rounded_button(self, parent, text, bg_color, fg_color, command, tooltip_text=""):
        """Crear botón redondeado consistente"""
        # Configuración uniforme para todos los botones
        button_config = {
            'text': text,
            'bg': bg_color,
            'fg': fg_color,
            'command': command,
            'width': 4,  # Ancho fijo en caracteres
            'height': 2,  # Alto fijo 
            'border': 0,
            'cursor': 'hand2',
            'font': ('Arial', 14, 'bold'),
            'relief': 'raised',  # Simular bordes redondeados
            'bd': 2,
            'activebackground': bg_color,
            'activeforeground': fg_color
        }
        
        button = tk.Button(parent, **button_config)
        
        # Agregar tooltip si se especifica
        if tooltip_text and self.config.getboolean('show_tooltips'):
            ToolTip(button, tooltip_text)
        
        return button
    
    def create_advanced_controls(self, parent):
        """Controles avanzados con botones redondeados UNIFORMES"""
        colors = self.theme_system.get_colors()
        texts = self.theme_system.get_texts()
        
        # TÍTULO DE CONTROLES - LIMPIO
        section_title = tk.Label(
            parent,
            text=texts['controls_title'],
            font=self.theme_system.get_font('subtitle'),
            fg=colors['text_primary'],
            bg=colors['bg_main']
        )
        section_title.pack(pady=(0, 15))
        
        # CONTAINER DE BOTONES VERTICALES
        controls_container = tk.Frame(parent, bg=colors['bg_main'])
        controls_container.pack(fill=tk.X)
        
        # BOTÓN START - Verde con ícono play
        self.start_button = self.create_rounded_button(
            controls_container,
            "▶",
            colors['btn_start'],
            colors['text_white'],
            self.start_recognition,
            texts['btn_start_tooltip']
        )
        self.start_button.pack(pady=(0, 12))
        
        # BOTÓN STOP - Rojo con ícono stop 
        self.stop_button = self.create_rounded_button(
            controls_container,
            "⏹",
            colors['btn_stop'],
            colors['text_white'],
            self.stop_recognition,
            texts['btn_stop_tooltip']
        )
        self.stop_button.config(state="disabled")
        self.stop_button.pack(pady=(0, 12))
        
        # BOTÓN FINALIZE - Amarillo con ícono pause
        finalize_button = self.create_rounded_button(
            controls_container,
            "⏸",
            colors['btn_pause'],
            colors['text_white'],
            self.force_finalize_buffer,
            texts['btn_finalize_tooltip']
        )
        finalize_button.pack(pady=(0, 12))
        
        # BOTÓN CLEAR - Gris oscuro con ícono basura
        clear_button = self.create_rounded_button(
            controls_container,
            "🗑",
            colors['btn_trash'],
            colors['text_white'],
            self.clear_medical_buffer,
            texts['btn_clear_tooltip']
        )
        clear_button.pack(pady=(0, 12))
        
        # SEPARADOR
        separator = tk.Frame(controls_container, height=2, bg=colors['border_light'])
        separator.pack(fill=tk.X, pady=12)
        
        # BOTÓN CONFIG - Gris claro con engranaje
        config_button = self.create_rounded_button(
            controls_container,
            "⚙",
            colors['btn_config'],
            colors['text_white'],
            self.open_advanced_configuration,
            texts['btn_config_tooltip']
        )
        config_button.pack(pady=(0, 12))
        
        # BOTÓN STATS - Azul con ícono estadísticas
        stats_button = self.create_rounded_button(
            controls_container,
            "📊",
            colors['btn_stats'],
            colors['text_white'],
            self.open_advanced_stats,
            texts['btn_stats_tooltip']
        )
        stats_button.pack(pady=(0, 12))
        
        # HOTKEYS INFO - LIMPIO
        hotkeys_label = tk.Label(
            parent,
            text="⌨️ Ctrl+Shift+V/S/F",
            font=self.theme_system.get_font('caption'),
            fg=colors['text_muted'],
            bg=colors['bg_main'],
            wraplength=100
        )
        hotkeys_label.pack(pady=(20, 0))
    
    def create_advanced_live_feedback(self, parent):
        """Feedback en vivo centrado y prominente"""
        colors = self.theme_system.get_colors()
        texts = self.theme_system.get_texts()
        
        # TÍTULO DE SECCIÓN
        section_title = tk.Label(
            parent,
            text=texts['live_title'],
            font=self.theme_system.get_font('title_medium'),
            fg=colors['text_primary'],
            bg=colors['bg_main']
        )
        section_title.pack(anchor=tk.W, pady=(0, 20))
        
        # CONTAINER PRINCIPAL con tema
        feedback_container = tk.Frame(
            parent, 
            bg=colors['bg_surface'],
            relief='flat',
            bd=1
        )
        feedback_container.pack(fill=tk.X, pady=(0, 30))
        
        # Padding interno
        feedback_content = tk.Frame(feedback_container, bg=colors['bg_surface'])
        feedback_content.pack(fill=tk.X, padx=20, pady=20)
        
        # RECONOCIMIENTO ACTIVO (más prominente)
        partial_title = tk.Label(
            feedback_content,
            text=f"🎙️ {texts['active_recognition']}",
            font=self.theme_system.get_font('subtitle'),
            fg=colors['text_primary'],
            bg=colors['bg_surface']
        )
        partial_title.pack(anchor=tk.W, pady=(0, 10))
        
        self.partial_text_var = tk.StringVar()
        self.partial_text_display = tk.Label(
            feedback_content,
            textvariable=self.partial_text_var,
            font=self.theme_system.get_font('body_large'),
            fg=colors['primary'],
            bg=colors['bg_surface'],
            wraplength=800,
            justify=tk.LEFT,
            anchor=tk.W
        )
        self.partial_text_display.pack(anchor=tk.W, fill=tk.X, pady=(0, 20))
        
        # BUFFER ACTUAL
        buffer_title = tk.Label(
            feedback_content,
            text=f"📝 {texts['medical_buffer']}",
            font=self.theme_system.get_font('subtitle'),
            fg=colors['text_primary'],
            bg=colors['bg_surface']
        )
        buffer_title.pack(anchor=tk.W, pady=(0, 10))
        
        self.buffer_display = scrolledtext.ScrolledText(
            feedback_content,
            height=4,
            font=self.theme_system.get_font('body_normal'),
            bg=colors['bg_card'],
            fg=colors['text_primary'],
            wrap=tk.WORD,
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=colors['border_medium'],
            selectbackground=colors['primary'],
            selectforeground=colors['text_white']
        )
        self.buffer_display.pack(fill=tk.X, pady=(0, 20))
        
        # CORRECCIONES
        corrections_title = tk.Label(
            feedback_content,
            text=f"🔧 {texts['corrections']}",
            font=self.theme_system.get_font('subtitle'),
            fg=colors['text_primary'],
            bg=colors['bg_surface']
        )
        corrections_title.pack(anchor=tk.W, pady=(0, 10))
        
        self.corrections_display = scrolledtext.ScrolledText(
            feedback_content,
            height=3,
            font=self.theme_system.get_font('code'),
            bg=colors['bg_accent'] if colors['bg_accent'] else colors['bg_card'],
            fg=colors['text_secondary'],
            wrap=tk.WORD,
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=colors['border_medium']
        )
        self.corrections_display.pack(fill=tk.X)
    
    def create_advanced_transcriptions(self, parent):
        """Transcripciones con tema"""
        colors = self.theme_system.get_colors()
        texts = self.theme_system.get_texts()
        
        # TÍTULO DE SECCIÓN
        section_title = tk.Label(
            parent,
            text=texts['transcriptions_title'],
            font=self.theme_system.get_font('title_medium'),
            fg=colors['text_primary'],
            bg=colors['bg_main']
        )
        section_title.pack(anchor=tk.W, pady=(0, 20))
        
        # ÁREA DE TRANSCRIPCIONES con tema
        self.transcriptions_text = scrolledtext.ScrolledText(
            parent,
            height=12,
            font=self.theme_system.get_font('body_normal'),
            bg=colors['bg_card'],
            fg=colors['text_primary'],
            wrap=tk.WORD,
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=colors['border_medium'],
            selectbackground=colors['primary'],
            selectforeground=colors['text_white']
        )
        self.transcriptions_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # CONTROLES DE TRANSCRIPCIÓN con tema
        trans_controls = tk.Frame(parent, bg=colors['bg_main'])
        trans_controls.pack(fill=tk.X)
        
        # Botones con íconos y tema
        button_config = {
            'font': self.theme_system.get_font('button_normal'),
            'border': 0,
            'padx': 15, 'pady': 8,
            'cursor': 'hand2'
        }
        
        send_button = tk.Button(
            trans_controls,
            text="📤 " + ("Enviar a Claude" if texts == self.theme_system.texts['es'] else "Send to Claude"),
            bg=colors['primary'],
            fg=colors['text_white'],
            command=self.send_selected_to_claude,
            **button_config
        )
        send_button.pack(side=tk.LEFT, padx=(0, 10))
        if self.config.getboolean('show_tooltips'):
            ToolTip(send_button, texts['btn_send_tooltip'])
        
        clear_all_button = tk.Button(
            trans_controls,
            text="🗑️ " + ("Limpiar Todo" if texts == self.theme_system.texts['es'] else "Clear All"),
            bg=colors['btn_trash'],
            fg=colors['text_white'],
            command=self.clear_all_advanced,
            **button_config
        )
        clear_all_button.pack(side=tk.LEFT, padx=10)
        if self.config.getboolean('show_tooltips'):
            ToolTip(clear_all_button, texts['btn_clear_all_tooltip'])
        
        save_button = tk.Button(
            trans_controls,
            text="💾 " + ("Guardar Sesión" if texts == self.theme_system.texts['es'] else "Save Session"),
            bg=colors['success'],
            fg=colors['text_white'],
            command=self.save_advanced_session,
            **button_config
        )
        save_button.pack(side=tk.RIGHT)
        if self.config.getboolean('show_tooltips'):
            ToolTip(save_button, texts['btn_save_tooltip'])
    
    def create_advanced_sidebar(self, parent):
        """Sidebar con tema"""
        colors = self.theme_system.get_colors()
        texts = self.theme_system.get_texts()
        
        # Padding interno con tema
        sidebar_content = tk.Frame(parent, bg=colors['bg_surface'])
        sidebar_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # TÍTULO SIDEBAR
        sidebar_title = tk.Label(
            sidebar_content,
            text=texts['session_title'],
            font=self.theme_system.get_font('title_medium'),
            fg=colors['text_primary'],
            bg=colors['bg_surface']
        )
        sidebar_title.pack(pady=(0, 20))
        
        # ESTADÍSTICAS EN VIVO
        stats_section = tk.Frame(sidebar_content, bg=colors['bg_surface'])
        stats_section.pack(fill=tk.X, pady=(0, 20))
        
        stats_title = tk.Label(
            stats_section,
            text=texts['live_metrics'],
            font=self.theme_system.get_font('subtitle'),
            fg=colors['text_primary'],
            bg=colors['bg_surface']
        )
        stats_title.pack(anchor=tk.W, pady=(0, 10))
        
        # Métricas individuales con tema
        self.create_advanced_metric(stats_section, "📝", texts['dictations'], "0", 'dictations_count')
        self.create_advanced_metric(stats_section, "🔧", texts['corrections'], "0", 'corrections_count')
        self.create_advanced_metric(stats_section, "⚡", texts['speed'], "0/min", 'speed_metric')
        self.create_advanced_metric(stats_section, "🎯", texts['accuracy'], "100%", 'accuracy_metric')
        
        # INFORMACIÓN DE SESIÓN
        session_section = tk.Frame(sidebar_content, bg=colors['bg_surface'])
        session_section.pack(fill=tk.X, pady=(0, 20))
        
        session_title = tk.Label(
            session_section,
            text=texts['session_info'],
            font=self.theme_system.get_font('subtitle'),
            fg=colors['text_primary'],
            bg=colors['bg_surface']
        )
        session_title.pack(anchor=tk.W, pady=(0, 10))
        
        self.session_info_var = tk.StringVar()
        session_info_label = tk.Label(
            session_section,
            textvariable=self.session_info_var,
            font=self.theme_system.get_font('body_small'),
            fg=colors['text_secondary'],
            bg=colors['bg_surface'],
            justify=tk.LEFT,
            wraplength=250
        )
        session_info_label.pack(anchor=tk.W)
        
        # SUGERENCIAS IA
        suggestions_section = tk.Frame(sidebar_content, bg=colors['bg_surface'])
        suggestions_section.pack(fill=tk.X, pady=(0, 20))
        
        suggestions_title = tk.Label(
            suggestions_section,
            text=texts['ai_suggestions'],
            font=self.theme_system.get_font('subtitle'),
            fg=colors['info'],
            bg=colors['bg_surface']
        )
        suggestions_title.pack(anchor=tk.W, pady=(0, 10))
        
        self.suggestions_text = scrolledtext.ScrolledText(
            suggestions_section,
            height=4,
            font=self.theme_system.get_font('body_small'),
            bg=colors['bg_card'],
            fg=colors['text_secondary'],
            wrap=tk.WORD,
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=colors['border_light']
        )
        self.suggestions_text.pack(fill=tk.X)
        
        # LOG DEL SISTEMA
        log_section = tk.Frame(sidebar_content, bg=colors['bg_surface'])
        log_section.pack(fill=tk.BOTH, expand=True)
        
        log_title = tk.Label(
            log_section,
            text=texts['system_log'],
            font=self.theme_system.get_font('subtitle'),
            fg=colors['text_primary'],
            bg=colors['bg_surface']
        )
        log_title.pack(anchor=tk.W, pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(
            log_section,
            height=6,
            font=self.theme_system.get_font('code'),
            bg=colors['bg_card'],
            fg=colors['text_secondary'],
            wrap=tk.WORD,
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=colors['border_light']
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_advanced_metric(self, parent, icon, label, value, var_name):
        """Crear métrica individual con tema"""
        colors = self.theme_system.get_colors()
        
        metric_frame = tk.Frame(parent, bg=colors['bg_surface'])
        metric_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Etiqueta con icono
        label_text = tk.Label(
            metric_frame,
            text=f"{icon} {label}",
            font=self.theme_system.get_font('body_small'),
            fg=colors['text_secondary'],
            bg=colors['bg_surface']
        )
        label_text.pack(side=tk.LEFT)
        
        # Valor
        value_label = tk.Label(
            metric_frame,
            text=value,
            font=self.theme_system.get_font('body_bold'),
            fg=colors['text_primary'],
            bg=colors['bg_surface']
        )
        value_label.pack(side=tk.RIGHT)
        
        # Guardar referencia
        setattr(self, var_name, value_label)
    
    def create_advanced_footer(self, parent):
        """Footer con tema"""
        colors = self.theme_system.get_colors()
        texts = self.theme_system.get_texts()
        
        footer_frame = tk.Frame(parent, bg=colors['bg_main'])
        footer_frame.pack(fill=tk.X, pady=(20, 0))
        
        theme_text = "Dark Mode" if self.theme_system.current_theme == 'dark' else "Light Mode"
        
        footer_text = tk.Label(
            footer_frame,
            text=f"{texts['footer']} • {theme_text} • {self.theme_system.selected_fonts['primary']} Font",
            font=self.theme_system.get_font('caption'),
            fg=colors['text_muted'],
            bg=colors['bg_main']
        )
        footer_text.pack()
    
    # [MANTENER MÉTODOS DE FUNCIONALIDAD CORE IDÉNTICOS - SOLO ADAPTAR GUI]
    
    def cleanup_and_setup_azure(self):
        """Setup Azure - SIMPLIFICADO"""
        self.log_to_gui("🧹 Configurando Azure...")
        
        try:
            # Activar micrófono
            self.activate_microphone_pipewire()
            
            # Si ya existe recognizer, solo hacer cleanup
            if hasattr(self, 'speech_recognizer') and self.speech_recognizer:
                try:
                    self.speech_recognizer.stop_continuous_recognition_async().wait()
                except:
                    pass
            
            # Llamar a setup_azure_medical_mode que ahora usa la lógica de v2.1
            self.setup_azure_medical_mode()
            
            self.log_to_gui("✅ Azure configurado")
            
        except Exception as e:
            self.logger.error(f"Error configurando Azure: {e}")
            self.log_to_gui(f"❌ Error Azure: {e}")
            messagebox.showerror("Error Azure", f"No se pudo configurar Azure:\n{e}")
    
    def setup_azure_medical_mode(self):
        """Setup Azure médico - VERSIÓN FUNCIONAL BASADA EN v2.1"""
        speech_key = self.config['azure_speech_key']
        region = self.config['azure_region']
    
        if not speech_key:
            raise ValueError("AZURE_SPEECH_KEY no configurado")
        
        self.logger.info(f"Configurando Azure (modo v2.1) - Región: {region}")
        
        # PASO 1: Configuración básica (como v2.1)
        self.speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=region
        )
        
        # Configurar idioma y voz
        self.speech_config.speech_recognition_language = self.config['speech_language']
        self.speech_config.speech_synthesis_voice_name = self.config['tts_voice']
        
        # PASO 2: Usar modo DICTATION como v2.1 (NO CONVERSATION)
        try:
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_RecoMode,
                "DICTATION"  # CAMBIO CLAVE: DICTATION en lugar de CONVERSATION
            )
            self.logger.info("✅ Modo DICTATION configurado")
        except:
            self.logger.warning("No se pudo configurar modo DICTATION, usando default")
        
        # PASO 3: Timeouts más conservadores (como v2.1)
        try:
            # Solo configurar timeouts básicos que funcionan con PipeWire
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
                "30000"  # 30 segundos como v2.1
            )
            
            # NO configurar estos que causan problemas:
            # - Speech_SegmentationSilenceTimeoutMs
            # - SpeechServiceConnection_EndSilenceTimeoutMs
            
        except Exception as e:
            self.logger.warning(f"Error configurando timeouts: {e}")
        
        # PASO 4: Crear audio config SIMPLE (como v2.1)
        try:
            self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
            self.logger.info("✅ Audio config creado")
        except Exception as e:
            self.logger.error(f"Error creando audio config: {e}")
            raise
        
        # PASO 5: Crear recognizer SIMPLE (como v2.1)
        try:
            self.speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=self.audio_config
            )
            self.logger.info("✅ Speech recognizer creado")
        except Exception as e:
            self.logger.error(f"Error creando recognizer: {e}")
            raise
        
        # PASO 6: Crear synthesizer
        try:
            self.speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config
            )
            self.logger.info("✅ Speech synthesizer creado")
        except Exception as e:
            self.logger.error(f"Error creando synthesizer: {e}")
            raise
        
        # PASO 7: Configurar callbacks
        self.setup_enhanced_callbacks()
        
        self.logger.info("✅ Azure configurado exitosamente (modo v2.1 compatible)")
   
    def verify_azure_setup(self):
        """Verificar que Azure esté configurado correctamente"""
        checks = []
        
        checks.append(("speech_config", hasattr(self, 'speech_config') and self.speech_config is not None))
        checks.append(("audio_config", hasattr(self, 'audio_config') and self.audio_config is not None))
        checks.append(("speech_recognizer", hasattr(self, 'speech_recognizer') and self.speech_recognizer is not None))
        checks.append(("speech_synthesizer", hasattr(self, 'speech_synthesizer') and self.speech_synthesizer is not None))
        
        all_ok = all(check[1] for check in checks)
        
        self.logger.info("=== Verificación Azure ===")
        for name, status in checks:
            self.logger.info(f"  {name}: {'✅' if status else '❌'}")
        self.logger.info(f"  Estado general: {'✅ OK' if all_ok else '❌ FALLO'}")
        
        return all_ok   
   
    def setup_enhanced_callbacks(self):
        """Callbacks - IDÉNTICOS"""
        
        def on_recognized_advanced(evt):
            try:
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    original_text = evt.result.text.strip()
                    if original_text and not self.recognition_paused_for_tts:
                        self.logger.info(f"🌙 TEXTO MODO AVANZADO: '{original_text}'")
                        
                        repetition_result = self.repetition_detector.is_repetition(original_text)
                        
                        if repetition_result['is_repetition']:
                            self.logger.warning(f"🔍 REPETICIÓN DETECTADA: {repetition_result['method']}")
                            self.log_to_gui(f"🔍 Repetición ignorada: {original_text[:30]}...")
                            self.stats_collector.record_repetition(repetition_result)
                            return
                        
                        corrected_text, corrections, detected_specialty = self.medical_corrector.get_contextual_corrections(original_text)
                        
                        if corrections:
                            self.logger.info(f"🔧 CORRECCIONES APLICADAS: {corrections}")
                            corrections_display = " | ".join(corrections)
                            self.corrections_display.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {corrections_display}\n")
                            self.corrections_display.see(tk.END)
                        
                        self.last_activity_time = time.time()
                        self.add_to_advanced_buffer(corrected_text, corrections, detected_specialty)
                        
            except Exception as e:
                self.logger.error(f"Error en callback avanzado: {e}")
        
        def on_recognizing_advanced(evt):
            try:
                if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
                    text = evt.result.text.strip()
                    if text and not self.recognition_paused_for_tts:
                        self.last_activity_time = time.time()
                        specialty = self.medical_corrector.detect_specialty(text)
                        self.update_partial_advanced_text(f"🌙 {text} | 🔬 {specialty.title()}")
            except Exception as e:
                self.logger.error(f"Error en recognizing avanzado: {e}")
        
        def on_error_advanced(evt):
            try:
                if hasattr(evt, 'result') and evt.result:
                    error_msg = f"Error Azure Avanzado: {getattr(evt.result, 'error_details', str(evt.result))}"
                else:
                    error_msg = f"Error Azure Avanzado: {str(evt)}"
                
                self.logger.error(error_msg)
                self.log_to_gui(f"❌ {error_msg}")
            except Exception as e:
                self.logger.error(f"Error en callback error: {e}")
                self.log_to_gui("❌ Error de reconocimiento")
        
        self.speech_recognizer.recognized.connect(on_recognized_advanced)
        self.speech_recognizer.recognizing.connect(on_recognizing_advanced)
        self.speech_recognizer.canceled.connect(on_error_advanced)
        
        self.logger.info("Callbacks avanzados configurados")
    
    def add_to_advanced_buffer(self, text, corrections, specialty):
        """Buffer avanzado - IDÉNTICO en lógica"""
        try:
            self.last_activity_time = time.time()
            self.medical_buffer.append(text)
            
            pause_duration = self.medical_pause_seconds
            self.stats_collector.record_phrase(text, corrections, specialty, pause_duration)
            
            self.update_advanced_buffer_display()
            self.update_main_advanced_status("🔴 Dictating with Advanced UI", "primary")
            
            if self.buffer_timer:
                self.root.after_cancel(self.buffer_timer)
            
            pause_ms = int(self.medical_pause_seconds * 1000)
            self.buffer_timer = self.root.after(pause_ms, self.finalize_advanced_buffer)
            
            self.logger.info(f"📝 Buffer avanzado: +'{text}' | Especialidad: {specialty}")
            
        except Exception as e:
            self.logger.error(f"Error en buffer avanzado: {e}")
    
    def finalize_advanced_buffer(self):
        """Finalización avanzada - IDÉNTICA en lógica"""
        try:
            if not self.medical_buffer:
                return
            
            full_text = " ".join(self.medical_buffer)
            full_text = self.clean_medical_text(full_text)
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            specialty = self.medical_corrector.current_specialty
            specialty_tag = f"[{specialty.upper()}]" if specialty != 'general' else ""
            
            display_text = f"[{timestamp}] {specialty_tag} {full_text}\n"
            self.transcriptions_text.insert(tk.END, display_text)
            self.transcriptions_text.see(tk.END)
            
            if self.config.getboolean('auto_send_to_claude'):
                self.send_to_claude_medical(full_text)
            
            self.medical_buffer.clear()
            self.transcription_count += 1
            
            texts = self.theme_system.get_texts()
            self.update_main_advanced_status(f"🟢 {texts['status_ready']}", "success")
            self.update_advanced_buffer_display()
            
            if self.config.getboolean('tts_enabled'):
                segment_count = len(full_text.split('.'))
                feedback_msg = f"Medical dictation {specialty} completed. {segment_count} segments."
                self.speak_advanced_feedback(feedback_msg)
            
            self.logger.info(f"✅ Buffer avanzado finalizado: {len(full_text)} caracteres")
            
        except Exception as e:
            self.logger.error(f"Error finalizando buffer avanzado: {e}")
    
    def clean_medical_text(self, text):
        """Limpiar texto médico - IDÉNTICO"""
        text = ' '.join(text.split())
        if text:
            text = text[0].upper() + text[1:]
        if text and not text.endswith('.'):
            text += '.'
        return text
    
    def speak_advanced_feedback(self, message):
        """TTS con anti-acoplamiento como v2.1"""
        if not self.config.getboolean('tts_enabled') or self.is_speaking:
            return
        
        mic_type = self.config.get('microphone_type', 'ambient')
        
        def advanced_tts():
            try:
                self.is_speaking = True
                
                # IMPORTANTE: Sistema anti-acoplamiento de v2.1
                if mic_type in ['ambient', 'builtin', 'lavalier']:
                    # Pausar reconocimiento COMPLETAMENTE
                    self.recognition_paused_for_tts = True
                    
                    # Si está escuchando, detener Azure temporalmente
                    if self.is_listening:
                        try:
                            self.speech_recognizer.stop_continuous_recognition_async().get()
                            time.sleep(0.2)
                        except:
                            pass
                    
                    # Mutear micrófono a nivel sistema (Linux)
                    try:
                        subprocess.run(['pactl', 'set-source-mute', '@DEFAULT_SOURCE@', '1'], 
                                     capture_output=True)
                        self.logger.info("Micrófono muteado para TTS")
                    except:
                        pass
                
                # Realizar TTS
                result = self.speech_synthesizer.speak_text_async(message).get()
                
                if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
                    self.logger.warning(f"Error TTS: {result.reason}")
                
                # Esperar un poco más
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error TTS: {e}")
            finally:
                self.is_speaking = False
                
                # Restaurar micrófono
                if mic_type in ['ambient', 'builtin', 'lavalier']:
                    try:
                        # Desmutear micrófono
                        subprocess.run(['pactl', 'set-source-mute', '@DEFAULT_SOURCE@', '0'], 
                                     capture_output=True)
                        time.sleep(0.3)
                        
                        # Reanudar reconocimiento si estaba activo
                        if self.is_listening and hasattr(self, 'speech_recognizer'):
                            self.speech_recognizer.start_continuous_recognition_async()
                            
                    except:
                        pass
                        
                self.recognition_paused_for_tts = False
        
        threading.Thread(target=advanced_tts, daemon=True).start()
    
    def send_to_claude_medical(self, text):
        """Envío a Claude - IDÉNTICO"""
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
                    self.speak_advanced_feedback("Sent to Claude")
            else:
                self.log_to_gui("❌ Claude not found")
                
        except Exception as e:
            self.logger.error(f"Error enviando a Claude: {e}")
            self.log_to_gui(f"❌ Error Claude: {e}")
    
    # MÉTODOS DE ACTUALIZACIÓN GUI AVANZADOS
    
    def update_main_advanced_status(self, text, status_type="normal"):
        """Actualizar estado principal avanzado"""
        try:
            colors = self.theme_system.get_colors()
            self.main_status_label.config(text=text)
            
            if status_type == "primary":
                self.main_status_label.config(fg=colors['primary'])
            elif status_type == "success":
                self.main_status_label.config(fg=colors['success'])
            elif status_type == "error":
                self.main_status_label.config(fg=colors['danger'])
            else:
                self.main_status_label.config(fg=colors['text_primary'])
        except:
            pass
    
    def update_advanced_buffer_display(self):
        """Actualizar display del buffer avanzado"""
        try:
            self.buffer_display.delete(1.0, tk.END)
            if self.medical_buffer:
                display_text = " ".join(self.medical_buffer)
                self.buffer_display.insert(1.0, display_text)
                self.buffer_display.see(tk.END)
        except:
            pass
    
    def update_partial_advanced_text(self, text):
        """Actualizar texto parcial avanzado"""
        try:
            display_text = text[:500] + "..." if len(text) > 500 else text
            self.partial_text_var.set(display_text)
        except:
            pass
    
    def start_advanced_updates(self):
        """Iniciar actualizaciones avanzadas"""
        self.update_live_advanced_stats()
        self.check_advanced_suggestions()
    
    def update_live_advanced_stats(self):
        """Actualizar estadísticas avanzadas"""
        try:
            summary = self.stats_collector.get_session_summary()
            
            # Actualizar métricas en sidebar
            self.dictations_count.config(text=str(summary['total_phrases']))
            self.corrections_count.config(text=str(summary['corrections_applied']))
            self.speed_metric.config(text=f"{summary['phrases_per_minute']:.1f}/min")
            
            if summary['total_phrases'] > 0:
                accuracy = 100 - (summary['repetitions_detected'] / summary['total_phrases'] * 100)
                self.accuracy_metric.config(text=f"{accuracy:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Error actualizando estadísticas avanzadas: {e}")
        finally:
            self.root.after(2000, self.update_live_advanced_stats)
    
    def check_advanced_suggestions(self):
        """Verificar sugerencias avanzadas"""
        try:
            suggestions = self.stats_collector.get_optimization_suggestions()
            
            if suggestions:
                self.suggestions_text.delete(1.0, tk.END)
                for suggestion in suggestions[-3:]:
                    timestamp = datetime.now().strftime("%H:%M")
                    self.suggestions_text.insert(tk.END, f"[{timestamp}] 💡 {suggestion['message']}\n\n")
                self.suggestions_text.see(tk.END)
                        
        except Exception as e:
            self.logger.error(f"Error verificando sugerencias: {e}")
        finally:
            self.root.after(30000, self.check_advanced_suggestions)
    
    def update_advanced_session_info(self):
        """Actualizar información de sesión avanzada"""
        try:
            duration = datetime.now() - self.session_start
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            buffer_count = len(self.medical_buffer)
            specialty = self.medical_corrector.current_specialty
            theme_text = "Dark" if self.theme_system.current_theme == 'dark' else "Light"
            
            texts = self.theme_system.get_texts()
            
            info = (f"⏱️ Duration: {hours:02d}:{minutes:02d}:{seconds:02d}\n"
                   f"🏥 Medical dictations: {self.transcription_count}\n"
                   f"🔬 Current specialty: {specialty.title()}\n"
                   f"📊 Active buffer: {buffer_count} segments\n"
                   f"🌙 Theme: {theme_text} Mode")
            
            self.session_info_var.set(info)
        except:
            pass
        finally:
            self.root.after(1000, self.update_advanced_session_info)
    
    def log_to_gui(self, message):
        """Log avanzado"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            
            lines = self.log_text.get(1.0, tk.END).count('\n')
            if lines > 50:
                self.log_text.delete(1.0, "10.0")
        except:
            pass
    
    # MÉTODOS DE CONTROL AVANZADOS
    
    def start_recognition(self):
        """Iniciar reconocimiento avanzado"""
        colors = self.theme_system.get_colors()
        texts = self.theme_system.get_texts()
        
        if not self.is_listening and self.speech_recognizer:
            try:
                self.log_to_gui("🌙 Iniciando reconocimiento avanzado...")
                
                start_time = time.time()
                
                # Activar micrófono antes de iniciar
                subprocess.run(['pactl', 'suspend-source', '@DEFAULT_SOURCE@', '0'], capture_output=True)
                time.sleep(0.5)
                
                self.speech_recognizer.start_continuous_recognition_async()
                init_time = time.time() - start_time
                
                self.is_listening = True
                self.start_button.config(state="disabled", bg=colors['text_muted'])
                self.stop_button.config(state="normal", bg=colors['btn_stop'])
                
                self.update_main_advanced_status(f"🎤 {texts['status_listening']}", "primary")
                self.log_to_gui(f"✅ Reconocimiento avanzado iniciado en {init_time:.2f}s")
                self.logger.info(f"Reconocimiento avanzado iniciado en {init_time:.2f}s")
                
                if self.config.getboolean('tts_enabled'):
                    self.speak_advanced_feedback("Advanced medical system ready")
                    
            except Exception as e:
                self.logger.error(f"Error iniciando reconocimiento avanzado: {e}")
                self.log_to_gui(f"❌ Error: {e}")
                self.is_listening = False
                self.start_button.config(state="normal", bg=colors['btn_start'])
                self.stop_button.config(state="disabled", bg=colors['text_muted'])
    
    def stop_recognition(self):
        """Detener reconocimiento avanzado"""
        colors = self.theme_system.get_colors()
        texts = self.theme_system.get_texts()
        
        if self.is_listening:
            try:
                if self.medical_buffer:
                    self.finalize_advanced_buffer()
                
                self.speech_recognizer.stop_continuous_recognition_async()
                self.is_listening = False
                self.start_button.config(state="normal", bg=colors['btn_start'])
                self.stop_button.config(state="disabled", bg=colors['text_muted'])
                
                self.update_main_advanced_status(f"🟢 {texts['status_ready']}", "success")
                self.log_to_gui("⏹️ Reconocimiento avanzado detenido")
                self.logger.info("Reconocimiento avanzado detenido")
                
            except Exception as e:
                self.logger.error(f"Error deteniendo reconocimiento: {e}")
    
    def force_finalize_buffer(self):
        """Finalizar buffer manualmente"""
        if self.medical_buffer:
            if self.buffer_timer:
                self.root.after_cancel(self.buffer_timer)
            self.finalize_advanced_buffer()
            self.log_to_gui("✅ Buffer finalizado manualmente")
    
    def clear_medical_buffer(self):
        """Limpiar buffer médico"""
        colors = self.theme_system.get_colors()
        texts = self.theme_system.get_texts()
        
        self.medical_buffer.clear()
        self.update_advanced_buffer_display()
        if self.buffer_timer:
            self.root.after_cancel(self.buffer_timer)
        self.update_main_advanced_status(f"🟢 {texts['status_ready']}", "success")
        self.log_to_gui("🗑️ Buffer médico limpiado")
    
    def send_selected_to_claude(self):
        """Enviar selección a Claude"""
        try:
            try:
                selected = self.transcriptions_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                selected = self.transcriptions_text.get(1.0, tk.END).strip()
            
            if selected:
                self.send_to_claude_medical(selected)
            else:
                self.log_to_gui("⚠️ No text to send")
        except Exception as e:
            self.logger.error(f"Error sending to Claude: {e}")
    
    def clear_all_advanced(self):
        """Limpiar todo avanzado"""
        colors = self.theme_system.get_colors()
        texts = self.theme_system.get_texts()
        
        self.transcriptions_text.delete(1.0, tk.END)
        self.medical_buffer.clear()
        self.update_advanced_buffer_display()
        self.partial_text_var.set("")
        self.corrections_display.delete(1.0, tk.END)
        self.transcription_count = 0
        if self.buffer_timer:
            self.root.after_cancel(self.buffer_timer)
        self.update_main_advanced_status(f"🟢 {texts['status_ready']}", "success")
        self.log_to_gui("🗑️ Sistema completamente limpiado")
    
    def save_advanced_session(self):
        """Guardar sesión avanzada"""
        try:
            content = self.transcriptions_text.get(1.0, tk.END).strip()
            if not content:
                self.log_to_gui("⚠️ No transcriptions to save")
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            theme_text = self.theme_system.current_theme
            lang_text = self.theme_system.current_language
            filename = f"session_advanced_v213_{theme_text}_{lang_text}_{timestamp}.txt"
            
            save_dir = Path.home() / "voice-bridge-claude" / "logs"
            save_dir.mkdir(parents=True, exist_ok=True)
            save_path = save_dir / filename
            
            summary = self.stats_collector.get_session_summary()
            
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(f"# Voice Bridge v2.1.3 Advanced UI Session\n")
                f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Theme: {self.theme_system.current_theme} mode\n")
                f.write(f"# Language: {self.theme_system.current_language}\n")
                f.write(f"# Font: {self.theme_system.selected_fonts['primary']}\n")
                f.write(f"# Medical dictations: {self.transcription_count}\n")
                f.write(f"# Corrections applied: {summary['corrections_applied']}\n")
                f.write(f"# Repetitions detected: {summary['repetitions_detected']}\n")
                f.write(f"# Performance: {summary['characters_per_minute']:.1f} chars/min\n\n")
                f.write("## MEDICAL TRANSCRIPTIONS - ADVANCED UI\n\n")
                f.write(content)
                
                if summary['most_common_corrections']:
                    f.write(f"\n\n## CONTEXTUAL CORRECTIONS APPLIED\n\n")
                    for correction, count in summary['most_common_corrections'].most_common(5):
                        f.write(f"- {correction}: {count} times\n")
            
            self.log_to_gui(f"💾 Advanced session saved: {filename}")
            self.logger.info(f"Advanced session saved: {save_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving advanced session: {e}")
    
    # CONFIGURACIÓN AVANZADA
    
    def open_advanced_configuration(self):
        """Ventana de configuración avanzada con tema y idioma"""
        colors = self.theme_system.get_colors()
        texts = self.theme_system.get_texts()
        
        config_window = tk.Toplevel(self.root)
        config_window.title(f"⚙️ {texts['config_title']}")
        config_window.geometry("650x800")
        config_window.resizable(False, False)
        config_window.configure(bg=colors['bg_main'])
    
        # Modal
        config_window.transient(self.root)
        config_window.grab_set()
    
        # Container principal
        main_container = tk.Frame(
            config_window, 
            bg=colors['bg_main'],
            padx=30, pady=20
        )
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # HEADER
        header_frame = tk.Frame(main_container, bg=colors['bg_main'])
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        title_label = tk.Label(
            header_frame,
            text=f"⚙️ {texts['config_title']}",
            font=self.theme_system.get_font('title_medium'),
            fg=colors['text_primary'],
            bg=colors['bg_main']
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text=texts['config_subtitle'],
            font=self.theme_system.get_font('body_normal'),
            fg=colors['text_secondary'],
            bg=colors['bg_main']
        )
        subtitle_label.pack(pady=(5, 0))
        
        # SCROLL CONTAINER
        canvas = tk.Canvas(
            main_container, 
            bg=colors['bg_main'],
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=colors['bg_main'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
    
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # === SECCIÓN 1: TEMA E IDIOMA (NUEVA) ===
        theme_section = tk.Frame(
            scrollable_frame, 
            bg=colors['bg_surface'],
            padx=20, pady=15
        )
        theme_section.pack(fill=tk.X, pady=(0, 20))
        
        theme_title = tk.Label(
            theme_section,
            text=f"🎨 {texts['theme_section']}",
            font=self.theme_system.get_font('subtitle'),
            fg=colors['text_primary'],
            bg=colors['bg_surface']
        )
        theme_title.pack(anchor=tk.W, pady=(0, 15))
        
        # Selector de tema
        theme_frame = tk.Frame(theme_section, bg=colors['bg_surface'])
        theme_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            theme_frame,
            text=f"🌙 {texts['theme_mode']}",
            font=self.theme_system.get_font('body_bold'),
            fg=colors['text_primary'],
            bg=colors['bg_surface']
        ).pack(anchor=tk.W)
        
        self.theme_var = tk.StringVar(value=self.theme_system.current_theme)
        
        theme_options_frame = tk.Frame(theme_frame, bg=colors['bg_surface'])
        theme_options_frame.pack(fill=tk.X, pady=(5, 0))
        
        light_radio = tk.Radiobutton(
            theme_options_frame,
            text=f"☀️ {texts['light_mode']}",
            variable=self.theme_var,
            value='light',
            command=self.on_theme_change,
            font=self.theme_system.get_font('body_normal'),
            fg=colors['text_primary'],
            bg=colors['bg_surface'],
            selectcolor=colors['bg_surface'],
            activebackground=colors['bg_hover']
        )
        light_radio.pack(anchor=tk.W, pady=2)
        
        dark_radio = tk.Radiobutton(
            theme_options_frame,
            text=f"🌙 {texts['dark_mode']}",
            variable=self.theme_var,
            value='dark',
            command=self.on_theme_change,
            font=self.theme_system.get_font('body_normal'),
            fg=colors['text_primary'],
            bg=colors['bg_surface'],
            selectcolor=colors['bg_surface'],
            activebackground=colors['bg_hover']
        )
        dark_radio.pack(anchor=tk.W, pady=2)
        
        # Selector de idioma
        lang_frame = tk.Frame(theme_section, bg=colors['bg_surface'])
        lang_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            lang_frame,
            text=f"🌍 {texts['language_option']}",
            font=self.theme_system.get_font('body_bold'),
            fg=colors['text_primary'],
            bg=colors['bg_surface']
        ).pack(anchor=tk.W)
        
        self.language_var = tk.StringVar(value=self.theme_system.current_language)
        
        lang_options_frame = tk.Frame(lang_frame, bg=colors['bg_surface'])
        lang_options_frame.pack(fill=tk.X, pady=(5, 0))
        
        en_radio = tk.Radiobutton(
            lang_options_frame,
            text=f"🇺🇸 {texts['lang_english']}",
            variable=self.language_var,
            value='en',
            command=self.on_language_change,
            font=self.theme_system.get_font('body_normal'),
            fg=colors['text_primary'],
            bg=colors['bg_surface'],
            selectcolor=colors['bg_surface'],
            activebackground=colors['bg_hover']
        )
        en_radio.pack(anchor=tk.W, pady=2)
        
        es_radio = tk.Radiobutton(
            lang_options_frame,
            text=f"🇪🇸 {texts['lang_spanish']}",
            variable=self.language_var,
            value='es',
            command=self.on_language_change,
            font=self.theme_system.get_font('body_normal'),
            fg=colors['text_primary'],
            bg=colors['bg_surface'],
            selectcolor=colors['bg_surface'],
            activebackground=colors['bg_hover']
        )
        es_radio.pack(anchor=tk.W, pady=2)
        
        # === SECCIÓN 2: TIMEOUTS AZURE ===
        timeouts_section = tk.Frame(
            scrollable_frame, 
            bg=colors['bg_surface'],
            padx=20, pady=15
        )
        timeouts_section.pack(fill=tk.X, pady=(0, 20))
        
        timeouts_title = tk.Label(
            timeouts_section,
            text="⏱️ Azure Speech Timeouts (Critical)",
            font=self.theme_system.get_font('subtitle'),
            fg=colors['text_primary'],
            bg=colors['bg_surface']
        )
        timeouts_title.pack(anchor=tk.W, pady=(0, 15))
        
        # Pausa buffer médico
        buffer_frame = tk.Frame(timeouts_section, bg=colors['bg_surface'])
        buffer_frame.pack(fill=tk.X, pady=(0, 12))
        
        tk.Label(
            buffer_frame,
            text="📝 Medical buffer pause:",
            font=self.theme_system.get_font('body_bold'),
            fg=colors['text_primary'],
            bg=colors['bg_surface']
        ).pack(anchor=tk.W)
        
        tk.Label(
            buffer_frame,
            text="   Time before finalizing current dictation buffer",
            font=self.theme_system.get_font('caption'),
            fg=colors['text_muted'],
            bg=colors['bg_surface']
        ).pack(anchor=tk.W, pady=(2, 5))
        
        self.pause_var = tk.DoubleVar(value=float(self.config.get('medical_pause_seconds', '6')))
        pause_control_frame = tk.Frame(buffer_frame, bg=colors['bg_surface'])
        pause_control_frame.pack(fill=tk.X)
        
        pause_scale = tk.Scale(
            pause_control_frame,
            from_=1, to=10,
            resolution=0.5,
            orient=tk.HORIZONTAL,
            variable=self.pause_var,
            command=self.on_pause_change,
            bg=colors['bg_surface'],
            fg=colors['text_primary'],
            activebackground=colors['primary'],
            highlightthickness=0
        )
        pause_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.pause_label = tk.Label(
            pause_control_frame,
            text=f"{self.pause_var.get()}s",
            font=self.theme_system.get_font('body_bold'),
            fg=colors['primary'],
            bg=colors['bg_surface']
        )
        self.pause_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Separador
        separator1 = tk.Frame(timeouts_section, height=1, bg=colors['border_light'])
        separator1.pack(fill=tk.X, pady=(15, 15))
        
        # Segmentación Azure (MUY IMPORTANTE)
        seg_frame = tk.Frame(timeouts_section, bg=colors['bg_surface'])
        seg_frame.pack(fill=tk.X, pady=(0, 12))
        
        tk.Label(
            seg_frame,
            text="🔧 Azure segmentation timeout:",
            font=self.theme_system.get_font('body_bold'),
            fg=colors['danger'],
            bg=colors['bg_surface']
        ).pack(anchor=tk.W)
        
        tk.Label(
            seg_frame,
            text="   ⚠️  CRITICAL: Controls when long phrases get cut off",
            font=self.theme_system.get_font('caption'),
            fg=colors['danger'],
            bg=colors['bg_surface']
        ).pack(anchor=tk.W, pady=(2, 5))
        
        self.segmentation_var = tk.DoubleVar(value=int(self.config.get('azure_segmentation_ms', '6000'))/1000)
        seg_control_frame = tk.Frame(seg_frame, bg=colors['bg_surface'])
        seg_control_frame.pack(fill=tk.X)
        
        seg_scale = tk.Scale(
            seg_control_frame,
            from_=2, to=10,
            resolution=0.5,
            orient=tk.HORIZONTAL,
            variable=self.segmentation_var,
            command=self.on_segmentation_change,
            bg=colors['bg_surface'],
            fg=colors['text_primary'],
            activebackground=colors['danger'],
            highlightthickness=0
        )
        seg_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.segmentation_label = tk.Label(
            seg_control_frame,
            text=f"{int(self.segmentation_var.get())}s",
            font=self.theme_system.get_font('body_bold'),
            fg=colors['danger'],
            bg=colors['bg_surface']
        )
        self.segmentation_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # End silence
        end_frame = tk.Frame(timeouts_section, bg=colors['bg_surface'])
        end_frame.pack(fill=tk.X, pady=(0, 12))
        
        tk.Label(
            end_frame,
            text="⏹️ Azure end silence timeout:",
            font=self.theme_system.get_font('body_bold'),
            fg=colors['text_primary'],
            bg=colors['bg_surface']
        ).pack(anchor=tk.W)
        
        tk.Label(
            end_frame,
            text="   Time to wait before finalizing recognition",
            font=self.theme_system.get_font('caption'),
            fg=colors['text_muted'],
            bg=colors['bg_surface']
        ).pack(anchor=tk.W, pady=(2, 5))
        
        self.end_silence_var = tk.DoubleVar(value=int(self.config.get('azure_end_silence_ms', '10000'))/1000)
        end_control_frame = tk.Frame(end_frame, bg=colors['bg_surface'])
        end_control_frame.pack(fill=tk.X)
        
        end_scale = tk.Scale(
            end_control_frame,
            from_=5, to=15,
            resolution=1,
            orient=tk.HORIZONTAL,
            variable=self.end_silence_var,
            command=self.on_end_silence_change,
            bg=colors['bg_surface'],
            fg=colors['text_primary'],
            activebackground=colors['primary'],
            highlightthickness=0
        )
        end_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.end_silence_label = tk.Label(
            end_control_frame,
            text=f"{int(self.end_silence_var.get())}s",
            font=self.theme_system.get_font('body_bold'),
            fg=colors['primary'],
            bg=colors['bg_surface']
        )
        self.end_silence_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # === SECCIÓN 3: MICRÓFONO ===
        mic_section = tk.Frame(
            scrollable_frame,
            bg=colors['bg_surface'],
            padx=20, pady=15
        )
        mic_section.pack(fill=tk.X, pady=(0, 20))
        
        mic_title = tk.Label(
            mic_section,
            text="🎤 Microphone Type (Anti-Coupling)",
            font=self.theme_system.get_font('subtitle'),
            fg=colors['text_primary'],
            bg=colors['bg_surface']
        )
        mic_title.pack(anchor=tk.W, pady=(0, 15))
        
        mic_info = tk.Label(
            mic_section,
            text="🔄 Lavalier mics can cause feedback loops when TTS responds",
            font=self.theme_system.get_font('caption'),
            fg=colors['warning'],
            bg=colors['bg_surface']
        )
        mic_info.pack(anchor=tk.W, pady=(0, 10))
        
        self.mic_type_var = tk.StringVar(value=self.config.get('microphone_type', 'ambient'))
        
        mic_options = [
            ("🖥️ Desktop/Ambient", "ambient", "Standard desktop or webcam microphone"),
            ("🎧 Headset/Close", "close", "Headset or close-positioned microphone"),
            ("📎 Lavalier/Lapel", "lavalier", "Clip-on lavalier microphone (auto-mutes TTS)")
        ]
        
        for text, value, description in mic_options:
            option_frame = tk.Frame(mic_section, bg=colors['bg_surface'])
            option_frame.pack(fill=tk.X, pady=3)
            
            radio = tk.Radiobutton(
                option_frame,
                text=text,
                variable=self.mic_type_var,
                value=value,
                command=self.on_mic_type_change,
                font=self.theme_system.get_font('body_normal'),
                fg=colors['text_primary'],
                bg=colors['bg_surface'],
                selectcolor=colors['bg_surface'],
                activebackground=colors['bg_hover']
            )
            radio.pack(anchor=tk.W)
            
            desc_label = tk.Label(
                option_frame,
                text=f"   {description}",
                font=self.theme_system.get_font('caption'),
                fg=colors['text_muted'],
                bg=colors['bg_surface']
            )
            desc_label.pack(anchor=tk.W, padx=(20, 0))
        
        # === SECCIÓN 4: OPCIONES GENERALES ===
        general_section = tk.Frame(
            scrollable_frame,
            bg=colors['bg_surface'],
            padx=20, pady=15
        )
        general_section.pack(fill=tk.X, pady=(0, 20))
        
        general_title = tk.Label(
            general_section,
            text="🔧 General Options",
            font=self.theme_system.get_font('subtitle'),
            fg=colors['text_primary'],
            bg=colors['bg_surface']
        )
        general_title.pack(anchor=tk.W, pady=(0, 15))
        
        # Auto-send
        self.auto_send_var = tk.BooleanVar(value=self.config.getboolean('auto_send_to_claude'))
        auto_send_check = tk.Checkbutton(
            general_section,
            text="📤 Auto-send medical dictations to Claude",
            variable=self.auto_send_var,
            command=self.on_auto_send_change,
            font=self.theme_system.get_font('body_normal'),
            fg=colors['text_primary'],
            bg=colors['bg_surface'],
            selectcolor=colors['bg_surface'],
            activebackground=colors['bg_hover']
        )
        auto_send_check.pack(anchor=tk.W, pady=(0, 8))
        
        # TTS
        self.tts_enabled_var = tk.BooleanVar(value=self.config.getboolean('tts_enabled'))
        tts_check = tk.Checkbutton(
            general_section,
            text="🔊 Enable voice feedback (TTS responses)",
            variable=self.tts_enabled_var,
            command=self.on_tts_enabled_change,
            font=self.theme_system.get_font('body_normal'),
            fg=colors['text_primary'],
            bg=colors['bg_surface'],
            selectcolor=colors['bg_surface'],
            activebackground=colors['bg_hover']
        )
        tts_check.pack(anchor=tk.W, pady=(0, 8))
        
        # Auto correction
        self.auto_correct_var = tk.BooleanVar(value=self.config.getboolean('auto_correct_medical'))
        correct_check = tk.Checkbutton(
            general_section,
            text="🔧 Auto-correct medical terminology",
            variable=self.auto_correct_var,
            command=self.on_auto_correct_change,
            font=self.theme_system.get_font('body_normal'),
            fg=colors['text_primary'],
            bg=colors['bg_surface'],
            selectcolor=colors['bg_surface'],
            activebackground=colors['bg_hover']
        )
        correct_check.pack(anchor=tk.W)
        
        # === INFORMACIÓN IMPORTANTE ===
        info_section = tk.Frame(
            scrollable_frame,
            bg=colors['bg_accent'] if colors['bg_accent'] else '#fffbeb',
            padx=20, pady=15
        )
        info_section.pack(fill=tk.X, pady=(0, 20))
        
        info_title = tk.Label(
            info_section,
            text="💡 Configuration Tips",
            font=self.theme_system.get_font('subtitle'),
            fg=colors['warning'],
            bg=colors['bg_accent'] if colors['bg_accent'] else '#fffbeb'
        )
        info_title.pack(anchor=tk.W, pady=(0, 10))
        
        tips = [
            "🔧 For long pathology phrases: use segmentation 6-8s",
            "📎 Lavalier microphones: system auto-mutes TTS to prevent loops",
            "⏱️ Buffer pause: adjust based on your speaking rhythm",
            "🌙 Dark mode: ideal for microscopy work to reduce screen glare",
            "🔄 Apply Azure changes to test new timeout settings"
        ]
        
        for tip in tips:
            tip_label = tk.Label(
                info_section,
                text=tip,
                font=self.theme_system.get_font('body_small'),
                fg=colors['text_secondary'],
                bg=colors['bg_accent'] if colors['bg_accent'] else '#fffbeb'
            )
            tip_label.pack(anchor=tk.W, pady=1)
        
        # === BOTONES ===
        button_section = tk.Frame(main_container, bg=colors['bg_main'])
        button_section.pack(fill=tk.X, pady=(20, 0))
        
        # Configuración común para botones
        button_config = {
            'font': self.theme_system.get_font('button_normal'),
            'border': 0,
            'padx': 20, 'pady': 12,
            'cursor': 'hand2'
        }
        
        # Botón aplicar tema
        apply_theme_button = tk.Button(
            button_section,
            text="🎨 Apply Theme Changes",
            bg=colors['info'],
            fg=colors['text_white'],
            command=lambda: self.apply_theme_changes(config_window),
            **button_config
        )
        apply_theme_button.pack(side=tk.LEFT, padx=(0, 12))
        
        # Botón aplicar Azure
        apply_button = tk.Button(
            button_section,
            text="🔄 Apply Azure Changes",
            bg=colors['warning'],
            fg=colors['text_white'],
            command=lambda: self.apply_azure_changes_advanced(config_window),
            **button_config
        )
        apply_button.pack(side=tk.LEFT, padx=(0, 12))
        
        # Botón cerrar
        close_button = tk.Button(
            button_section,
            text="❌ Close",
            bg=colors['text_muted'],
            fg=colors['text_white'],
            command=config_window.destroy,
            **button_config
        )
        close_button.pack(side=tk.RIGHT)
        
        # Botón guardar
        save_button = tk.Button(
            button_section,
            text="💾 Save All Settings",
            bg=colors['success'],
            fg=colors['text_white'],
            command=lambda: self.save_config_advanced(config_window),
            **button_config
        )
        save_button.pack(side=tk.RIGHT, padx=(12, 0))
    
    # MÉTODOS DE CALLBACK PARA LA CONFIGURACIÓN AVANZADA
    
    def on_theme_change(self):
        """Cambio de tema"""
        new_theme = self.theme_var.get()
        self.theme_system.set_theme(new_theme)
        self.logger.info(f"🎨 Tema cambiado a: {new_theme}")
    
    def on_language_change(self):
        """Cambio de idioma"""
        new_language = self.language_var.get()
        self.theme_system.set_language(new_language)
        self.logger.info(f"🌍 Idioma cambiado a: {new_language}")
    
    def on_pause_change(self, value):
        """Cambio en pausa médica"""
        new_value = float(value)
        self.pause_label.config(text=f"{new_value}s")
        self.medical_pause_seconds = new_value
        self.config['medical_pause_seconds'] = str(new_value)
    
    def on_segmentation_change(self, value):
        """Cambio en segmentación Azure - CRÍTICO"""
        new_value_s = float(value)
        new_value_ms = int(new_value_s * 1000)
        self.segmentation_label.config(text=f"{int(new_value_s)}s")
        self.config['azure_segmentation_ms'] = str(new_value_ms)
        self.logger.info(f"⚙️ Segmentación Azure: {new_value_s}s")
    
    def on_end_silence_change(self, value):
        """Cambio en finalización Azure"""
        new_value_s = float(value)
        new_value_ms = int(new_value_s * 1000)
        self.end_silence_label.config(text=f"{int(new_value_s)}s")
        self.config['azure_end_silence_ms'] = str(new_value_ms)
        self.logger.info(f"⚙️ Finalización Azure: {new_value_s}s")
    
    def on_mic_type_change(self):
        """Cambio en tipo de micrófono"""
        new_type = self.mic_type_var.get()
        self.config['microphone_type'] = new_type
        self.logger.info(f"🎤 Micrófono configurado: {new_type}")
        
        if new_type == 'lavalier':
            self.log_to_gui("📎 Micrófono lavalier: TTS auto-silenciado durante dictado")
    
    def on_auto_send_change(self):
        """Cambio en auto-envío"""
        new_value = self.auto_send_var.get()
        self.config['auto_send_to_claude'] = str(new_value).lower()

    def on_tts_enabled_change(self):
        """Cambio en TTS"""
        new_value = self.tts_enabled_var.get()
        self.config['tts_enabled'] = str(new_value).lower()
    
    def on_auto_correct_change(self):
        """Cambio en auto-corrección médica"""
        new_value = self.auto_correct_var.get()
        self.config['auto_correct_medical'] = str(new_value).lower()
    
    def apply_theme_changes(self, parent_window):
        """Aplicar cambios de tema e idioma"""
        try:
            # Guardar preferencias UI
            self.save_ui_preferences()
            
            theme_text = "Dark Mode" if self.theme_system.current_theme == 'dark' else "Light Mode"
            lang_text = "Español" if self.theme_system.current_language == 'es' else "English"
            
            messagebox.showinfo(
                "Theme Applied",
                f"✅ UI settings updated:\n\n"
                f"🎨 Theme: {theme_text}\n"
                f"🌍 Language: {lang_text}\n\n"
                f"⚠️ Restart the application to see full theme changes.",
                parent=parent_window
            )
            
            self.log_to_gui(f"🎨 Theme: {self.theme_system.current_theme}, Lang: {self.theme_system.current_language}")
            
        except Exception as e:
            self.logger.error(f"Error applying theme changes: {e}")
            messagebox.showerror("Error", f"Error applying theme: {e}", parent=parent_window)
    
    def apply_azure_changes_advanced(self, parent_window):
        """Aplicar cambios Azure avanzados"""
        try:
            was_listening = self.is_listening
            
            if was_listening:
                self.stop_recognition()
                time.sleep(0.5)
            
            self.cleanup_and_setup_azure()
            
            if was_listening:
                time.sleep(0.5)
                self.start_recognition()
            
            seg_timeout = int(self.config.get('azure_segmentation_ms', '6000'))//1000
            end_timeout = int(self.config.get('azure_end_silence_ms', '10000'))//1000
            
            self.log_to_gui(f"🔄 Azure reconfigurado: seg={seg_timeout}s, end={end_timeout}s")
            
            messagebox.showinfo(
                "Azure Configuration Applied",
                f"✅ Azure Speech timeouts updated:\n\n"
                f"🔧 Segmentation: {seg_timeout}s\n"
                f"⏹️ End silence: {end_timeout}s\n"
                f"🎤 Microphone: {self.config.get('microphone_type')}\n\n"
                f"Test with a long medical phrase now.",
                parent=parent_window
            )
            
        except Exception as e:
            self.logger.error(f"Error aplicando cambios Azure: {e}")
            messagebox.showerror("Error", f"Error applying changes: {e}", parent=parent_window)
    
    def save_config_advanced(self, config_window):
        """Guardar configuración avanzada completa"""
        try:
            # Actualizar configuración con preferencias UI
            self.config['ui_theme'] = self.theme_system.current_theme
            self.config['ui_language'] = self.theme_system.current_language
            
            config_file = Path.home() / "voice-bridge-claude" / "config" / "voice_bridge_config.ini"
            
            config_parser = configparser.ConfigParser()
            config_parser['DEFAULT'] = dict(self.config)
            
            with open(config_file, 'w') as f:
                config_parser.write(f)
            
            self.log_to_gui("💾 Configuración completa guardada")
            messagebox.showinfo(
                "Configuration Saved", 
                "✅ All settings including theme and language have been saved successfully.\n\n"
                "Restart the application to see full changes.", 
                parent=config_window
            )
            config_window.destroy()
            
        except Exception as e:
            self.logger.error(f"Error guardando configuración: {e}")
            messagebox.showerror("Error", f"Error saving: {e}", parent=config_window)
    
    def open_advanced_stats(self):
        """Ventana de estadísticas avanzadas"""
        colors = self.theme_system.get_colors()
        texts = self.theme_system.get_texts()
        summary = self.stats_collector.get_session_summary()
        
        theme_text = "Dark Mode" if self.theme_system.current_theme == 'dark' else "Light Mode"
        lang_text = "Español" if self.theme_system.current_language == 'es' else "English"
        
        stats_info = f"""📊 Voice Bridge Advanced Statistics

⏱️ Session Duration: {summary['duration']}
🎤 Total Dictations: {summary['total_phrases']}
📝 Characters Dictated: {summary['total_characters']}
🔧 Corrections Applied: {summary['corrections_applied']}
🔍 Repetitions Detected: {summary['repetitions_detected']}
⚡ Performance: {summary['characters_per_minute']:.1f} chars/min

🔬 Current Specialty: {self.medical_corrector.current_specialty.title()}
🎨 UI Theme: {theme_text}
🌍 Language: {lang_text}
📝 Font: {self.theme_system.selected_fonts['primary']}
🧠 AI Features: All intelligent features active

💡 System optimized for medical professionals with advanced UI"""
        
        messagebox.showinfo("📊 Advanced Session Statistics", stats_info)
    
    # MÉTODOS AUXILIARES HEREDADOS IDÉNTICOS
    
    def load_medical_terms(self):
        """Cargar términos médicos - IDÉNTICO"""
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
            
            self.logger.info(f"Términos médicos avanzados: {len(self.medical_terms)}")
        except Exception as e:
            self.logger.error(f"Error cargando términos médicos: {e}")
    
    def setup_hotkeys(self):
        """Hotkeys - IDÉNTICOS"""
        try:
            self.pressed_keys = set()
            
            self.hotkey_listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.hotkey_listener.start()
            
            self.logger.info("Hotkeys avanzados configurados")
        except Exception as e:
            self.logger.error(f"Error hotkeys: {e}")
    
    def on_key_press(self, key):
        """Manejo de teclas - IDÉNTICO"""
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
        """Release de teclas - IDÉNTICO"""
        try:
            self.pressed_keys.discard(key)
        except:
            pass
    
    def on_closing(self):
        """Cierre avanzado"""
        try:
            if self.is_listening:
                self.stop_recognition()
            
            if hasattr(self, 'hotkey_listener'):
                self.hotkey_listener.stop()
            
            # Auto-guardar configuración UI
            self.save_ui_preferences()
            
            # Auto-guardar sesión
            content = self.transcriptions_text.get(1.0, tk.END).strip()
            if content:
                try:
                    self.save_advanced_session()
                except:
                    pass
            
            self.logger.info("Voice Bridge v2.1.3 AVANZADO cerrado")
            self.root.destroy()
            
        except:
            self.root.destroy()
    
    def run(self):
        """Ejecutar aplicación avanzada"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()

def main():
    """Función principal v2.1.3 Avanzado"""
    try:
        if not os.environ.get('AZURE_SPEECH_KEY'):
            print("❌ ERROR: AZURE_SPEECH_KEY no configurado")
            return
        
        app = VoiceBridgeV213Advanced()
        app.run()
        
    except Exception as e:
        print(f"❌ Error crítico v2.1.3 Avanzado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
