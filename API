# Voice Bridge Pathology - API Documentation

## Overview

Voice Bridge Pathology utiliza Azure Cognitive Services para reconocimiento de voz y proporciona una API interna para integración con sistemas de patología. Este documento describe las interfaces y métodos disponibles.

## Core Classes

### VoiceBridgePathology

Clase principal que maneja todo el flujo de reconocimiento de voz y transcripción.

#### Initialization

```python
app = VoiceBridgePathology()
```

#### Key Methods

##### Recognition Control

```python
# Iniciar reconocimiento de voz
app.start_recognition()

# Detener reconocimiento de voz  
app.stop_recognition()

# Parada de emergencia
app.emergency_stop()
```

##### Configuration Management

```python
# Cargar configuración
config = app.load_config()

# Aplicar términos médicos al reconocedor
app.apply_medical_terms_to_recognizer()

# Configurar Azure Speech Services
app.setup_azure_speech()
```

##### Text Processing

```python
# Enviar texto a Claude Desktop
app.send_text_to_claude(text)

# Extraer términos médicos clave
key_terms = app.extract_key_medical_terms(text)

# Procesar comandos de voz
processed = app.process_voice_commands(text)
```

##### Audio Output

```python
# Síntesis de texto a voz
app.speak_text("Mensaje a pronunciar")
```

## Configuration Parameters

### Azure Speech Services

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `azure_speech_key` | string | - | Clave de suscripción Azure |
| `azure_region` | string | eastus | Región de Azure |
| `speech_language` | string | es-CO | Idioma de reconocimiento |
| `tts_voice` | string | es-CO-SalomeNeural | Voz para síntesis |

### Application Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `medical_mode` | boolean | true | Modo médico especializado |
| `confidence_threshold` | float | 0.7 | Umbral de confianza mínimo |
| `auto_send_to_claude` | boolean | true | Envío automático a Claude |
| `tts_enabled` | boolean | true | Habilitación de TTS |

### Hotkeys

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hotkey_start` | string | ctrl+shift+v | Tecla para iniciar |
| `hotkey_stop` | string | ctrl+shift+s | Tecla para detener |
| `hotkey_emergency` | string | ctrl+shift+x | Tecla de emergencia |

## Event Callbacks

### Speech Recognition Events

```python
def on_recognized(evt):
    """Llamado cuando se completa el reconocimiento"""
    text = evt.result.text
    confidence = extract_confidence(evt.result)
    # Procesar texto final

def on_recognizing(evt):
    """Llamado durante el reconocimiento (texto parcial)"""
    partial_text = evt.result.text
    # Actualizar interfaz con texto parcial

def on_error(evt):
    """Llamado cuando ocurre un error"""
    error_details = evt.result.error_details
    # Manejar error
```

## Medical Terminology Integration

### Dictionary Structure

Los diccionarios médicos se organizan por prioridad:

1. **frases_completas.txt** - Frases completas (máxima prioridad)
2. **patologia_molecular.txt** - Terminología especializada

### Adding Medical Terms

```bash
# Agregar término individual
./agregar_termino_medico.sh "carcinoma adenoescamoso" patologia_molecular

# Agregar frase completa
./agregar_termino_medico.sh "compatible con neoplasia maligna" frases_completas
```

### Term Processing

```python
# Cargar términos médicos
app.load_medical_terms()

# Aplicar al reconocedor con prioridad
app.apply_medical_terms_to_recognizer()
```

## Integration with Claude Desktop

### Window Detection

```python
# Buscar ventana de Claude usando wmctrl
result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
```

### Text Input Automation

```python
# Activar ventana de Claude
subprocess.run(['wmctrl', '-i', '-a', window_id])

# Enviar texto usando xdotool
subprocess.run(['xdotool', 'type', text])
subprocess.run(['xdotool', 'key', 'Return'])
```

## Logging and Debugging

### Log Levels

- **INFO**: Operaciones normales
- **WARNING**: Situaciones anómalas no críticas
- **ERROR**: Errores que requieren atención

### Log Locations

```
~/voice-bridge-claude/logs/
├── voice_bridge_YYYYMMDD.log
└── transcripciones_patologia_YYYYMMDD_HHMMSS.txt
```

### Debug Methods

```python
# Logging a GUI
app.log_to_gui("Mensaje de debug")

# Logging a archivo
app.logger.info("Información importante")
app.logger.error("Error crítico")
```

## Error Handling

### Common Error Scenarios

1. **Azure Authentication Failed**
   ```python
   # HTTP 401 - Verificar AZURE_SPEECH_KEY
   # HTTP 403 - Verificar cuotas y permisos
   ```

2. **Audio Device Issues**
   ```python
   # Verificar acceso a micrófono
   # Comprobar configuración de audio
   ```

3. **Claude Desktop Not Found**
   ```python
   # Verificar que Claude esté abierto
   # Comprobar título exacto de ventana
   ```

### Exception Handling

```python
try:
    app.start_recognition()
except Exception as e:
    app.logger.error(f"Error iniciando reconocimiento: {e}")
    app.log_to_gui(f"❌ Error: {e}")
```

## Performance Optimization

### Azure Speech Settings

```python
# Reducir latencia
speech_config.set_property(
    speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
    "5000"
)

# Optimizar para conversación médica
speech_config.set_property(
    speechsdk.PropertyId.SpeechServiceConnection_RecoMode,
    "CONVERSATION"
)
```

### Memory Management

```python
# Limitar líneas en log GUI
if lines > 100:
    self.log_text.delete(1.0, "10.0")

# Procesar transcripciones en queue
self.transcription_queue.put(transcription_data)
```

## Extension Points

### Custom Medical Dictionaries

```python
def load_custom_dictionary(self, dictionary_path):
    """Cargar diccionario personalizado"""
    with open(dictionary_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                self.medical_terms.append(line.strip().lower())
```

### Custom Voice Commands

```python
def process_custom_commands(self, text):
    """Procesar comandos específicos del usuario"""
    text_lower = text.lower()
    
    if "comando personalizado" in text_lower:
        # Implementar funcionalidad específica
        return True
    
    return False
```

### Integration Hooks

```python
def on_transcription_complete(self, text, confidence):
    """Hook llamado después de cada transcripción"""
    # Implementar lógica personalizada
    pass

def before_send_to_claude(self, text):
    """Hook llamado antes de enviar a Claude"""
    # Modificar texto si es necesario
    return text
```

## Testing

### Unit Tests

```python
import unittest
from voice_bridge_app import VoiceBridgePathology

class TestVoiceBridge(unittest.TestCase):
    def setUp(self):
        self.app = VoiceBridgePathology()
    
    def test_medical_terms_loading(self):
        self.app.load_medical_terms()
        self.assertGreater(len(self.app.medical_terms), 0)
```

### Integration Tests

```bash
# Test de conectividad Azure
./test_azure_connection.sh

# Test de términos médicos
python test_medical_terms.py
```

## Security Considerations

### Data Privacy

- Las transcripciones se procesan localmente cuando es posible
- Azure Speech Services procesa audio según sus políticas de privacidad
- Los logs pueden contener información médica sensible

### Network Security

- Usar conexiones HTTPS para Azure
- Implementar firewalls apropiados
- Considerar VPNs para entornos médicos

### Access Control

- Restringir acceso a archivos de configuración
- Proteger claves de Azure Speech
- Implementar autenticación en entornos multiusuario

## Version Compatibility

### Python Requirements

- Python 3.8+
- Azure Cognitive Services Speech SDK 1.34.0+
- tkinter (incluido en Python estándar)

### System Requirements

- Linux Ubuntu 20.04+ (recomendado)
- Windows 10+ (compatible)
- macOS 10.15+ (compatible con limitaciones)

### Claude Desktop Compatibility

- Claude Desktop versión estable más reciente
- Funcionalidad completa en Linux
- Funcionalidad limitada en otros sistemas
