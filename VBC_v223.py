# !/usr/bin/env python3
"""
Voice Bridge v2.2.3 - Sistema Optimizado de Dictado Médico (CORREGIDO)
=========================================================================
Versión optimizada con respuesta rápida y configuración completa - Error de SectionProxy corregido
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


class ConfigWindow:
    """Ventana completa de configuración - CORREGIDA"""

    def __init__(self, parent, config_dict):
        self.parent = parent
        # CORRECCIÓN: Convertir el dict correctamente
        self.config = dict(config_dict) if config_dict else {}
        self.window = None
        self.create_window()

    def create_window(self):
        """Crear ventana de configuración"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("⚙️ Configuración Voice Bridge")
        self.window.geometry("600x500")
        self.window.resizable(True, True)
        self.window.transient(self.parent)
        self.window.grab_set()

        # Centrar ventana
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (500 // 2)
        self.window.geometry(f"600x500+{x}+{y}")

        self.create_interface()

    def create_interface(self):
        """Crear interfaz de configuración"""
        # Frame principal
        main_frame = tk.Frame(self.window, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        title_label = tk.Label(main_frame, text="⚙️ Configuración Voice Bridge v2.2.3",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))

        # Notebook para pestañas
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Pestañas
        self.create_azure_tab(notebook)
        self.create_recognition_tab(notebook)
        self.create_ui_tab(notebook)
        self.create_advanced_tab(notebook)

        # Botones
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)

        save_btn = tk.Button(buttons_frame, text="💾 Guardar y Aplicar",
                             command=self.save_config, bg="#27ae60", fg="white",
                             font=('Arial', 11, 'bold'), padx=20, pady=8)
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))

        cancel_btn = tk.Button(buttons_frame, text="❌ Cancelar",
                               command=self.window.destroy, bg="#95a5a6", fg="white",
                               font=('Arial', 11), padx=20, pady=8)
        cancel_btn.pack(side=tk.RIGHT)

    def create_azure_tab(self, notebook):
        """Crear pestaña de configuración Azure"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🔧 Azure Speech")

        # Scroll frame
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Azure Key
        key_frame = tk.LabelFrame(scrollable_frame, text="Clave de Azure Speech", padx=10, pady=10)
        key_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(key_frame, text="Azure Speech Key:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.azure_key_var = tk.StringVar(value=self.config.get('azure_speech_key', ''))
        self.azure_key_entry = tk.Entry(key_frame, textvariable=self.azure_key_var,
                                        width=60, show="*", font=('Courier', 10))
        self.azure_key_entry.pack(fill=tk.X, pady=(5, 0))

        # Azure Region
        region_frame = tk.LabelFrame(scrollable_frame, text="Región de Azure", padx=10, pady=10)
        region_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(region_frame, text="Región:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.region_var = tk.StringVar(value=self.config.get('azure_region', 'eastus'))
        region_combo = ttk.Combobox(region_frame, textvariable=self.region_var,
                                    values=['eastus', 'westus', 'eastus2', 'westus2',
                                            'westeurope', 'northeurope', 'eastasia',
                                            'southeastasia', 'japaneast', 'australiaeast'])
        region_combo.pack(fill=tk.X, pady=(5, 0))

        # Idioma
        lang_frame = tk.LabelFrame(scrollable_frame, text="Configuración de Idioma", padx=10, pady=10)
        lang_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(lang_frame, text="Idioma de reconocimiento:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.lang_var = tk.StringVar(value=self.config.get('speech_language', 'es-CO'))
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var,
                                  values=['es-CO', 'es-ES', 'es-MX', 'es-AR', 'en-US', 'en-GB'])
        lang_combo.pack(fill=tk.X, pady=(5, 10))

        tk.Label(lang_frame, text="Voz TTS:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.tts_voice_var = tk.StringVar(value=self.config.get('tts_voice', 'es-CO-SalomeNeural'))
        tts_combo = ttk.Combobox(lang_frame, textvariable=self.tts_voice_var,
                                 values=['es-CO-SalomeNeural', 'es-CO-GonzaloNeural',
                                         'es-ES-ElviraNeural', 'es-MX-DaliaNeural'])
        tts_combo.pack(fill=tk.X, pady=(5, 0))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_recognition_tab(self, notebook):
        """Crear pestaña de configuración de reconocimiento"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🎤 Reconocimiento")

        # Frame principal
        main_frame = tk.Frame(frame, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Velocidad de respuesta
        speed_frame = tk.LabelFrame(main_frame, text="⚡ Velocidad de Respuesta", padx=10, pady=10)
        speed_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(speed_frame, text="Tiempo de pausa para procesar (segundos):",
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        pause_frame = tk.Frame(speed_frame)
        pause_frame.pack(fill=tk.X, pady=(5, 10))

        self.pause_var = tk.DoubleVar(value=float(self.config.get('medical_pause_seconds', '2.0')))
        pause_scale = tk.Scale(pause_frame, from_=1.0, to=10.0, resolution=0.5,
                               variable=self.pause_var, orient=tk.HORIZONTAL,
                               font=('Arial', 10))
        pause_scale.pack(fill=tk.X)

        self.pause_label = tk.Label(pause_frame,
                                    text=f"Pausa actual: {self.pause_var.get()}s (Menor = Más rápido)",
                                    font=('Arial', 9), fg="blue")
        self.pause_label.pack(pady=(5, 0))

        def update_pause_label(val):
            self.pause_label.config(text=f"Pausa actual: {float(val)}s (Menor = Más rápido)")

        pause_scale.config(command=update_pause_label)

        # Azure Timeouts (OPTIMIZADOS)
        timeout_frame = tk.LabelFrame(main_frame, text="🚀 Configuración Optimizada Azure", padx=10, pady=10)
        timeout_frame.pack(fill=tk.X, pady=(0, 15))

        # Silencio inicial (reducido para respuesta rápida)
        tk.Label(timeout_frame, text="Silencio inicial (ms):", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.initial_silence_var = tk.IntVar(value=int(self.config.get('azure_initial_silence_ms', '3000')))
        initial_scale = tk.Scale(timeout_frame, from_=1000, to=10000, resolution=500,
                                 variable=self.initial_silence_var, orient=tk.HORIZONTAL)
        initial_scale.pack(fill=tk.X, pady=(5, 10))

        # Silencio final (reducido para respuesta rápida)
        tk.Label(timeout_frame, text="Silencio final (ms):", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.end_silence_var = tk.IntVar(value=int(self.config.get('azure_end_silence_ms', '2000')))
        end_scale = tk.Scale(timeout_frame, from_=500, to=8000, resolution=500,
                             variable=self.end_silence_var, orient=tk.HORIZONTAL)
        end_scale.pack(fill=tk.X, pady=(5, 10))

        # Segmentación (reducido para respuesta rápida)
        tk.Label(timeout_frame, text="Segmentación (ms):", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.segmentation_var = tk.IntVar(value=int(self.config.get('azure_segmentation_ms', '3000')))
        seg_scale = tk.Scale(timeout_frame, from_=1000, to=8000, resolution=500,
                             variable=self.segmentation_var, orient=tk.HORIZONTAL)
        seg_scale.pack(fill=tk.X, pady=(5, 10))

        # Botón de configuración rápida
        quick_btn = tk.Button(timeout_frame, text="⚡ Configuración Rápida (Recomendado)",
                              command=self.apply_fast_config, bg="#e74c3c", fg="white",
                              font=('Arial', 10, 'bold'), padx=10, pady=5)
        quick_btn.pack(pady=10)

        # Funciones médicas
        medical_frame = tk.LabelFrame(main_frame, text="🏥 Funciones Médicas", padx=10, pady=10)
        medical_frame.pack(fill=tk.X, pady=(0, 15))

        self.auto_correct_var = tk.BooleanVar(value=self.config.get('auto_correct_medical', 'true').lower() == 'true')
        tk.Checkbutton(medical_frame, text="Corrección automática de términos médicos",
                       variable=self.auto_correct_var, font=('Arial', 10)).pack(anchor=tk.W, pady=2)

        self.tts_enabled_var = tk.BooleanVar(value=self.config.get('tts_enabled', 'true').lower() == 'true')
        tk.Checkbutton(medical_frame, text="Text-to-Speech habilitado",
                       variable=self.tts_enabled_var, font=('Arial', 10)).pack(anchor=tk.W, pady=2)

    def create_ui_tab(self, notebook):
        """Crear pestaña de configuración de UI"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🎨 Interfaz")

        main_frame = tk.Frame(frame, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Tema
        theme_frame = tk.LabelFrame(main_frame, text="🎨 Tema de Interfaz", padx=10, pady=10)
        theme_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(theme_frame, text="Tema:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.theme_var = tk.StringVar(value=self.config.get('ui_theme', 'light'))
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var,
                                   values=['light', 'dark'])
        theme_combo.pack(fill=tk.X, pady=(5, 10))

        # Idioma de interfaz
        tk.Label(theme_frame, text="Idioma de interfaz:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.ui_lang_var = tk.StringVar(value=self.config.get('ui_language', 'es'))
        ui_lang_combo = ttk.Combobox(theme_frame, textvariable=self.ui_lang_var,
                                     values=['es', 'en'])
        ui_lang_combo.pack(fill=tk.X, pady=(5, 0))

    def create_advanced_tab(self, notebook):
        """Crear pestaña de configuración avanzada"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🔬 Avanzado")

        main_frame = tk.Frame(frame, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Detección de repeticiones
        rep_frame = tk.LabelFrame(main_frame, text="🔄 Detección de Repeticiones", padx=10, pady=10)
        rep_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(rep_frame, text="Umbral de similitud:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.similarity_var = tk.DoubleVar(value=float(self.config.get('similarity_threshold', '0.85')))
        similarity_scale = tk.Scale(rep_frame, from_=0.5, to=1.0, resolution=0.05,
                                    variable=self.similarity_var, orient=tk.HORIZONTAL)
        similarity_scale.pack(fill=tk.X, pady=(5, 0))

        # Estadísticas
        stats_frame = tk.LabelFrame(main_frame, text="📊 Estadísticas", padx=10, pady=10)
        stats_frame.pack(fill=tk.X, pady=(0, 15))

        self.show_stats_var = tk.BooleanVar(value=self.config.get('show_performance_stats', 'true').lower() == 'true')
        tk.Checkbutton(stats_frame, text="Mostrar estadísticas de rendimiento",
                       variable=self.show_stats_var, font=('Arial', 10)).pack(anchor=tk.W, pady=2)

        self.show_corrections_var = tk.BooleanVar(
            value=self.config.get('show_correction_details', 'true').lower() == 'true')
        tk.Checkbutton(stats_frame, text="Mostrar detalles de correcciones",
                       variable=self.show_corrections_var, font=('Arial', 10)).pack(anchor=tk.W, pady=2)

    def apply_fast_config(self):
        """Aplicar configuración rápida optimizada"""
        # Configuración para respuesta ultra-rápida
        self.pause_var.set(1.5)  # Pausa muy corta
        self.initial_silence_var.set(2000)  # 2 segundos inicial
        self.end_silence_var.set(1500)  # 1.5 segundos final
        self.segmentation_var.set(2500)  # 2.5 segundos segmentación

        messagebox.showinfo("✅ Configuración Aplicada",
                            "Configuración optimizada para respuesta rápida aplicada!\n\n" +
                            "• Pausa de procesamiento: 1.5s\n" +
                            "• Silencio inicial: 2s\n" +
                            "• Silencio final: 1.5s\n" +
                            "• Segmentación: 2.5s")

    def save_config(self):
        """Guardar configuración"""
        try:
            # Actualizar configuración
            self.config.update({
                'azure_speech_key': self.azure_key_var.get(),
                'azure_region': self.region_var.get(),
                'speech_language': self.lang_var.get(),
                'tts_voice': self.tts_voice_var.get(),
                'medical_pause_seconds': str(self.pause_var.get()),
                'azure_initial_silence_ms': str(self.initial_silence_var.get()),
                'azure_end_silence_ms': str(self.end_silence_var.get()),
                'azure_segmentation_ms': str(self.segmentation_var.get()),
                'auto_correct_medical': str(self.auto_correct_var.get()).lower(),
                'tts_enabled': str(self.tts_enabled_var.get()).lower(),
                'ui_theme': self.theme_var.get(),
                'ui_language': self.ui_lang_var.get(),
                'similarity_threshold': str(self.similarity_var.get()),
                'show_performance_stats': str(self.show_stats_var.get()).lower(),
                'show_correction_details': str(self.show_corrections_var.get()).lower()
            })

            # Guardar en archivo
            config_file = Path.home() / "voice-bridge-claude" / "config" / "voice_bridge_config.ini"
            config_file.parent.mkdir(parents=True, exist_ok=True)

            config_parser = configparser.ConfigParser()
            config_parser['DEFAULT'] = self.config

            with open(config_file, 'w') as f:
                config_parser.write(f)

            messagebox.showinfo("✅ Configuración Guardada",
                                "Configuración guardada correctamente.\n" +
                                "Reinicia el reconocimiento para aplicar cambios.")

            self.window.destroy()

        except Exception as e:
            messagebox.showerror("❌ Error", f"Error guardando configuración:\n{e}")


class ThemeSystem:
    """Sistema de temas mejorado"""

    def __init__(self):
        self.current_theme = 'light'
        self.current_language = 'es'
        self.detect_fonts()

    def detect_fonts(self):
        """Detectar mejores fuentes disponibles"""
        try:
            root_temp = tk.Tk()
            root_temp.withdraw()
            available = set(font.families())
            root_temp.destroy()

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
                'title': 'Voice Bridge v2.2.3',
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
                'title': 'Voice Bridge v2.2.3',
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
        """Inicializar Voice Bridge v2.2.3 Optimizado"""
        self.setup_logging()
        self.logger.info("=== Voice Bridge v2.2.3 CORREGIDO Iniciando ===")

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

        # Timeouts configurables OPTIMIZADOS
        try:
            # Pausa de procesamiento optimizada (por defecto 2 segundos para respuesta rápida)
            self.medical_pause_seconds = float(self.config.get('medical_pause_seconds', '2.0'))
            if self.medical_pause_seconds <= 0:
                self.medical_pause_seconds = 2.0
        except (ValueError, TypeError):
            self.logger.warning("Valor inválido para medical_pause_seconds, usando default optimizado")
            self.medical_pause_seconds = 2.0

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
        self.log_to_gui("⏳ Configurando Azure Speech (Modo Optimizado)...")
        threading.Thread(target=self.delayed_azure_setup, daemon=True).start()

        self.load_medical_terms()
        self.setup_hotkeys()

        # Información de sesión
        self.session_start = datetime.now()
        self.transcription_count = 0

        self.logger.info("✅ Voice Bridge v2.2.3 CORREGIDO iniciado correctamente (Modo Optimizado)")

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

    def setup_logging(self):
        """Configurar sistema de logging"""
        log_dir = Path.home() / "voice-bridge-claude" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"voice_bridge_v223_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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
        """Cargar configuración con valores optimizados que funcionan"""
        config = configparser.ConfigParser()

        # Valores por defecto basados en versiones que funcionan
        default_config = {
            'azure_key': os.environ.get('AZURE_SPEECH_KEY', ''),
            'azure_region': os.environ.get('AZURE_SPEECH_REGION', 'eastus'),
            'language': 'es-CO',  # o 'es-ES'
            'tts_voice': 'es-CO-SalomeNeural',
            'medical_pause_seconds': '4',

            # Timeouts Azure que funcionan en versiones anteriores
            'azure_initial_silence_ms': '10000',  # 10 segundos para empezar
            'azure_end_silence_ms': '8000',  # 8 segundos para finalizar
            'azure_segmentation_ms': '4000',  # 4 segundos entre palabras

            # Configuraciones adicionales
            'tts_enabled': 'true',
            'auto_correct_medical': 'true',
            'microphone_type': 'ambient'
        }

        config_file = Path.home() / "voice-bridge-claude" / "config" / "voice_bridge_config.ini"
        if config_file.exists():
            config.read(config_file)
            # Asegurar que todos los valores por defecto estén presentes
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
        self.theme_system.current_language = self.config.get('ui_language', 'es')

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

        # Título con indicador de velocidad
        title_label = tk.Label(main_frame,
                               text=texts['title'] + " ⚡ MODO RÁPIDO (CORREGIDO)",
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

        # Estado con indicador de pausa actual
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

        # Indicador de pausa
        pause_info = tk.Label(status_frame,
                              text=f"⚡ Pausa: {self.medical_pause_seconds}s",
                              font=fonts['caption'],
                              bg=colors['bg_surface'],
                              fg=colors['primary'])
        pause_info.pack(side=tk.RIGHT, padx=(10, 0))

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

            if self.azure_ready:
                self.optimize_pipewire_for_dictation()

        except Exception as e:
            self.logger.error(f"Error en configuración diferida de Azure: {e}")
            self.log_to_gui(f"❌ Error configurando Azure: {e}")

    def setup_azure(self):
        """Configurar Azure Speech con modo DICTATION (compatible con PipeWire)"""
        try:
            if not self.config.get('azure_key') or not self.config.get('azure_region'):
                self.log_to_gui("❌ Azure key o región no configurados")
                return False

            # Limpiar reconocedor existente (igual que en versiones que funcionan)
            try:
                if hasattr(self, 'speech_recognizer') and self.speech_recognizer:
                    self.speech_recognizer.stop_continuous_recognition_async().wait()
                    del self.speech_recognizer
                import gc
                gc.collect()
                import time
                time.sleep(0.3)
            except Exception as e:
                self.log_to_gui(f"⚠ Limpieza Azure: {e}")

            # Configurar Speech SDK
            self.speech_config = speechsdk.SpeechConfig(
                subscription=self.config['azure_key'],
                region=self.config['azure_region']
            )

            # Configurar idioma y voz
            language = self.config.get('language', 'es-CO')
            self.speech_config.speech_recognition_language = language
            tts_voice = self.config.get('tts_voice', 'es-CO-SalomeNeural')
            self.speech_config.speech_synthesis_voice_name = tts_voice

            # 🔧 CONFIGURACIÓN CRÍTICA: Usar modo DICTATION (compatible con PipeWire)
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_RecoMode,
                "DICTATION"
            )

            # TIMEOUTS OPTIMIZADOS PARA DICTADO MÉDICO (basado en versiones v21/v201/v203)
            # Tiempo para empezar a hablar - más generoso para dictado médico
            initial_silence = self.config.get('azure_initial_silence_ms', '30000')  # 30 segundos
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
                initial_silence
            )

            # Tiempo de finalización - más largo para dictado médico
            end_silence = self.config.get('azure_end_silence_ms', '20000')  # 20 segundos
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs,
                end_silence
            )

            # Tiempo entre palabras - optimizado para dictado continuo
            segmentation_silence = self.config.get('azure_segmentation_ms', '3000')  # 3 segundos
            self.speech_config.set_property(
                speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs,
                segmentation_silence
            )

            # Configuraciones adicionales que funcionan en las versiones anteriores
            try:
                # Mejorar reconocimiento continuo
                self.speech_config.set_property(
                    speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode,
                    "Continuous"
                )

                # Configuración de estabilidad para resultados parciales
                self.speech_config.set_property(
                    speechsdk.PropertyId.SpeechServiceResponse_StablePartialResultThreshold,
                    "3"
                )

                # Optimización para tipo de micrófono
                mic_type = self.config.get('microphone_type', 'ambient')
                if mic_type in ['headset', 'directional']:
                    # Menor supresión de ruido para headsets/direccionales
                    self.speech_config.set_property(
                        speechsdk.PropertyId.SpeechServiceConnection_EndpointId,
                        "LowNoiseSuppression"
                    )

            except AttributeError:
                # Si no están disponibles las propiedades avanzadas, continuar
                self.log_to_gui("ℹ Usando configuración básica de Azure")

            # Configurar audio (igual que en versiones que funcionan)
            self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

            # Crear reconocedor con la configuración que funciona
            self.speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=self.audio_config
            )

            # Crear sintetizador para TTS
            self.speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config
            )

            # Configurar callbacks (igual que en versiones que funcionan)
            self.setup_speech_callbacks()

            self.azure_ready = True
            self.log_to_gui(f"✅ Azure configurado - Modo DICTATION (PipeWire compatible)")
            self.log_to_gui(f"🗣 Idioma: {language} | Voz: {tts_voice}")
            self.log_to_gui(
                f"⏱ Timeouts: inicial={initial_silence}ms, fin={end_silence}ms, segmentación={segmentation_silence}ms")

            return True

        except Exception as e:
            self.log_to_gui(f"❌ Error configurando Azure: {str(e)}")
            self.azure_ready = False
            return False

    def optimize_pipewire_for_dictation(self):
        """Optimizar PipeWire para dictado médico continuo"""
        try:
            import subprocess
            import os

            # Verificar si PipeWire está activo
            result = subprocess.run(['pgrep', 'pipewire'], capture_output=True)
            if result.returncode != 0:
                self.log_to_gui("ℹ PipeWire no detectado - usando configuración estándar")
                return

            self.log_to_gui("🔧 Optimizando PipeWire para dictado médico...")

            # Crear directorio de configuración si no existe
            config_dir = os.path.expanduser("~/.config/pipewire/pipewire.conf.d")
            os.makedirs(config_dir, exist_ok=True)

            # Configuración optimizada para dictado médico
            config_content = """
    # Configuración optimizada para dictado médico continuo
    context.properties = {
        default.clock.min-quantum = 512
        default.clock.max-quantum = 2048
        default.clock.quantum-limit = 8192
    }

    context.modules = [
        { name = libpipewire-module-rt
            args = {
                nice.level = -11
                rt.prio = 88
                rt.time.soft = 200000
                rt.time.hard = 200000
            }
        }
    ]

    stream.properties = {
        node.suspend-on-idle = false
        session.suspend-timeout-seconds = 0
        resample.quality = 4
        channelmix.normalize = false
        channelmix.mix-lfe = true
    }
    """

            config_file = os.path.join(config_dir, "99-medical-dictation.conf")

            # Solo escribir si no existe o es diferente
            write_config = True
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    existing_content = f.read()
                    if existing_content.strip() == config_content.strip():
                        write_config = False

            if write_config:
                with open(config_file, 'w') as f:
                    f.write(config_content)

                self.log_to_gui("✅ Configuración PipeWire para dictado médico aplicada")

                # Recargar configuración si es posible
                try:
                    subprocess.run(['systemctl', '--user', 'reload', 'pipewire'],
                                   capture_output=True, timeout=5)
                    self.log_to_gui("🔄 PipeWire recargado con nueva configuración")
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    self.log_to_gui("ℹ Reinicia la aplicación para aplicar cambios de PipeWire")

        except Exception as e:
            self.log_to_gui(f"⚠ No se pudo optimizar PipeWire: {e}")

    def setup_speech_callbacks(self):
        """Configurar callbacks de Azure Speech (basado en versiones que funcionan)"""
        if not self.speech_recognizer:
            return

        def on_recognizing(evt):
            """Callback para reconocimiento parcial (igual que en versiones que funcionan)"""
            if evt.result.text and len(evt.result.text.strip()) > 0:
                # Actualizar estado de actividad
                self.last_activity_time = datetime.now()

                # Log del reconocimiento parcial
                partial_text = evt.result.text.strip()
                self.log_to_gui(f"🎯 Reconociendo: {partial_text}")

                # Actualizar buffer médico si es necesario
                if hasattr(self, 'medical_buffer'):
                    # Reset del timer de buffer médico
                    if self.buffer_timer:
                        self.root.after_cancel(self.buffer_timer)

                    # Programar procesamiento del buffer
                    self.buffer_timer = self.root.after(
                        int(self.medical_pause_seconds * 1000),
                        self.process_medical_buffer
                    )

        def on_recognized(evt):
            """Callback para reconocimiento final (igual que en versiones que funcionan)"""
            if evt.result.text and len(evt.result.text.strip()) > 0:
                final_text = evt.result.text.strip()
                self.log_to_gui(f"✅ Reconocido: {final_text}")

                # Agregar al buffer médico (igual que en versiones anteriores)
                if hasattr(self, 'medical_buffer'):
                    self.medical_buffer.append(final_text)
                    self.last_activity_time = datetime.now()

                    # Cancelar timer anterior y programar nuevo
                    if self.buffer_timer:
                        self.root.after_cancel(self.buffer_timer)

                    self.buffer_timer = self.root.after(
                        int(self.medical_pause_seconds * 1000),
                        self.process_medical_buffer
                    )
                else:
                    # Agregar directamente a transcripción si no hay buffer
                    self.add_to_transcription(final_text)

        def on_session_started(evt):
            """Callback cuando inicia la sesión de reconocimiento"""
            self.log_to_gui("🔵 Sesión de reconocimiento iniciada")

        def on_session_stopped(evt):
            """Callback cuando termina la sesión de reconocimiento"""
            self.log_to_gui("🔴 Sesión de reconocimiento detenida")

        def on_canceled(evt):
            """Callback para manejar errores y cancelaciones"""
            if evt.cancellation_details.reason == speechsdk.CancellationReason.Error:
                error_details = evt.cancellation_details.error_details
                self.log_to_gui(f"❌ Error de reconocimiento: {error_details}")

                # Manejo de errores específicos (igual que en versiones que funcionan)
                if "authentication" in error_details.lower():
                    self.log_to_gui("🔑 Error de autenticación - verificar Azure key")
                elif "network" in error_details.lower():
                    self.log_to_gui("🌐 Error de red - verificar conexión")
                elif "microphone" in error_details.lower() or "audio" in error_details.lower():
                    self.log_to_gui("🎤 Error de micrófono - verificar permisos de audio")

                # Intentar reconectar automáticamente después de 2 segundos
                self.root.after(2000, self._attempt_azure_reconnection)

            else:
                self.log_to_gui("ℹ Reconocimiento cancelado")

        # Asignar todos los callbacks
        self.speech_recognizer.recognizing.connect(on_recognizing)
        self.speech_recognizer.recognized.connect(on_recognized)
        self.speech_recognizer.session_started.connect(on_session_started)
        self.speech_recognizer.session_stopped.connect(on_session_stopped)
        self.speech_recognizer.canceled.connect(on_canceled)

        self.log_to_gui("✅ Callbacks de Azure configurados")

    def _attempt_azure_reconnection(self):
        """Intentar reconectar Azure automáticamente (igual que en versiones que funcionan)"""
        if not self.is_listening:
            return

        self.log_to_gui("🔄 Intentando reconectar Azure Speech...")

        # Detener reconocimiento actual
        self.stop_recognition()

        # Esperar un momento y reconectar
        self.root.after(1000, self._do_azure_reconnection)

    def _do_azure_reconnection(self):
        """Realizar la reconexión de Azure"""
        try:
            # Reconfigurar Azure completamente
            if self.setup_azure():
                # Reiniciar reconocimiento si estaba activo
                if self.is_listening:
                    self.start_recognition()
                    self.log_to_gui("✅ Reconexión de Azure exitosa")
                else:
                    self.log_to_gui("✅ Azure reconectado - listo para usar")
            else:
                self.log_to_gui("❌ Falló la reconexión de Azure")
        except Exception as e:
            self.log_to_gui(f"❌ Error en reconexión de Azure: {e}")

    def start_recognition(self):
        """Iniciar reconocimiento (igual que en versiones que funcionan)"""
        try:
            if not self.azure_ready:
                self.log_to_gui("❌ Azure no está configurado correctamente")
                return False

            if not self.speech_recognizer:
                self.log_to_gui("❌ Reconocedor de Azure no está disponible")
                return False

            # Iniciar reconocimiento continuo (igual que en versiones anteriores)
            self.speech_recognizer.start_continuous_recognition_async().wait()
            self.is_listening = True

            # Reset de variables de estado
            self.last_activity_time = datetime.now()
            if hasattr(self, 'medical_buffer'):
                self.medical_buffer.clear()

            self.log_to_gui("🎤 Reconocimiento de voz iniciado - ¡Habla ahora!")

            # Actualizar interfaz
            self.update_ui_state()

            return True

        except Exception as e:
            self.log_to_gui(f"❌ Error iniciando reconocimiento: {str(e)}")
            self.is_listening = False
            self.update_ui_state()
            return False

    def stop_recognition(self):
        """Detener reconocimiento (igual que en versiones que funcionan)"""
        try:
            if self.speech_recognizer and self.is_listening:
                self.speech_recognizer.stop_continuous_recognition_async().wait()

            self.is_listening = False

            # Procesar buffer restante si existe
            if hasattr(self, 'medical_buffer') and self.medical_buffer:
                self.process_medical_buffer()

            # Cancelar timers
            if hasattr(self, 'buffer_timer') and self.buffer_timer:
                self.root.after_cancel(self.buffer_timer)
                self.buffer_timer = None

            self.log_to_gui("🔴 Reconocimiento de voz detenido")

            # Actualizar interfaz
            self.update_ui_state()

        except Exception as e:
            self.log_to_gui(f"⚠ Error deteniendo reconocimiento: {str(e)}")
            self.is_listening = False
            self.update_ui_state()

    def setup_speech_callbacks(self):
        """Configurar callbacks de Azure Speech optimizados"""
        if not self.speech_recognizer:
            return

        try:
            # Resultado final - procesamiento inmediato
            def on_recognized(evt):
                if evt.result.text.strip():
                    self.transcription_queue.put(('final', evt.result.text))

            # Resultado parcial - para feedback visual inmediato
            def on_recognizing(evt):
                if evt.result.text.strip():
                    self.transcription_queue.put(('partial', evt.result.text))

            self.speech_recognizer.recognized.connect(on_recognized)
            self.speech_recognizer.recognizing.connect(on_recognizing)

            # Eventos de sesión
            self.speech_recognizer.session_started.connect(
                lambda evt: self.log_to_gui("🎤 Sesión iniciada - MODO RÁPIDO")
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
        """Iniciar reconocimiento de voz optimizado"""
        if not self.azure_ready:
            self.log_to_gui("❌ Azure Speech no está configurado")
            return

        try:
            if self.speech_recognizer:
                self.speech_recognizer.start_continuous_recognition_async()
                self.is_listening = True
                self.update_ui_state()
                self.log_to_gui("🎤 Reconocimiento iniciado - MODO RÁPIDO ⚡")
                self.logger.info("Reconocimiento de voz iniciado en modo optimizado")

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
                    text=texts['recognizing'] + " ⚡",
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
        """Abrir ventana completa de configuración - CORREGIDO"""
        try:
            # CORRECCIÓN: Pasar dict en lugar de SectionProxy
            config_window = ConfigWindow(self.root, self.config)

            # Esperar a que se cierre la ventana y recargar configuración si es necesario
            def check_config_changes():
                if hasattr(config_window, 'window') and config_window.window.winfo_exists():
                    self.root.after(100, check_config_changes)
                else:
                    # Recargar configuración
                    self.config = self.load_config()
                    self.load_ui_preferences()

                    # Reconfigurar Azure si es necesario
                    if self.azure_ready:
                        self.log_to_gui("🔄 Reconfigurando Azure con nuevos parámetros...")
                        threading.Thread(target=self.delayed_azure_setup, daemon=True).start()

            self.root.after(100, check_config_changes)

        except Exception as e:
            self.log_to_gui(f"❌ Error abriendo configuración: {e}")
            self.logger.error(f"Error en open_config: {e}")

    def process_medical_buffer(self):
        """Procesar buffer médico acumulado - OPTIMIZADO"""
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

            # Agregar a transcripción INMEDIATAMENTE
            self.add_to_transcription(full_text)

        except Exception as e:
            self.logger.error(f"Error procesando buffer médico: {e}")

    def add_to_transcription(self, text):
        """Agregar texto a la transcripción - OPTIMIZADO"""
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
=== SESIÓN VOICE BRIDGE v2.2.3 OPTIMIZADO CORREGIDO ===
Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Duración: {datetime.now() - self.session_start}
Frases totales: {stats['total_phrases']}
Palabras totales: {stats['total_words']}
Caracteres totales: {stats['total_characters']}
Correcciones aplicadas: {stats['corrections_applied']}
Repeticiones detectadas: {stats['repetitions_detected']}
Pausa configurada: {self.medical_pause_seconds}s

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
                    "frecuencia cardiaca": "frecuencia cardíaca",
                    "temperatura corporal": "temperatura corporal",
                    "examen fisico": "examen físico",
                    "historia clinica": "historia clínica"
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
        """Iniciar loops de actualización OPTIMIZADOS"""

        def transcription_loop():
            """Loop para procesar transcripciones - MODO RÁPIDO"""
            while True:
                try:
                    msg_type, text = self.transcription_queue.get(timeout=0.05)  # Timeout más corto

                    if msg_type == 'final' and text.strip():
                        # Agregar a buffer médico
                        self.medical_buffer.append(text.strip())
                        self.last_activity_time = time.time()

                        # Configurar timer para procesar buffer (TIEMPO REDUCIDO)
                        if self.buffer_timer:
                            self.buffer_timer.cancel()

                        self.buffer_timer = threading.Timer(
                            self.medical_pause_seconds,  # Tiempo optimizado
                            self.process_medical_buffer
                        )
                        self.buffer_timer.start()

                    elif msg_type == 'partial' and text.strip():
                        # Mostrar texto parcial para feedback inmediato
                        pass  # Por ahora no mostramos parciales para no saturar

                except queue.Empty:
                    pass
                except Exception as e:
                    self.logger.error(f"Error en transcription_loop: {e}")

        def ui_update_loop():
            """Loop para actualizar UI - OPTIMIZADO"""
            while True:
                try:
                    self.root.after(0, self.update_ui_state)
                    time.sleep(0.5)  # Actualización más frecuente
                except Exception as e:
                    self.logger.error(f"Error en ui_update_loop: {e}")

        # Iniciar threads
        threading.Thread(target=transcription_loop, daemon=True).start()
        threading.Thread(target=ui_update_loop, daemon=True).start()

    def on_closing(self):
        """Manejar cierre de la aplicación"""
        try:
            self.logger.info("Cerrando Voice Bridge v2.2.3...")

            # Detener reconocimiento
            if self.is_listening:
                self.stop_recognition()

            # Procesar buffer pendiente
            if self.medical_buffer:
                self.process_medical_buffer()

            # Detener hotkeys
            if hasattr(self, 'hotkey_listener'):
                self.hotkey_listener.stop()

            self.logger.info("Voice Bridge v2.2.3 cerrado correctamente")

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