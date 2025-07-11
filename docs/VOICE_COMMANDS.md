# Voice Commands Reference Guide

## 🎤 Overview

Voice Bridge v2 introduces a comprehensive voice command system that allows hands-free control of the application. Commands are recognized in Spanish (Colombian variant) and can be used during normal recognition or dictation mode.

## 📋 Command Categories

### 1. Dictation Control Commands

These commands control the continuous dictation mode:

| Command | Variations | Action |
|---------|------------|--------|
| **"inicio dictado"** | "iniciar dictado", "empezar dictado", "claude inicio dictado" | Starts continuous dictation mode |
| **"fin dictado"** | "finalizar dictado", "terminar dictado", "parar dictado", "claude fin dictado" | Ends dictation and shows preview |
| **"cancelar dictado"** | "cancelar", "borrar dictado", "claude cancelar" | Cancels current dictation without saving |
| **"enviar a claude"** | "enviar dictado", "claude enviar" | Sends buffered text to Claude |

### 2. System Control Commands

General system control commands:

| Command | Variations | Action |
|---------|------------|--------|
| **"repetir última"** | "repetir ultimo", "claude repetir" | Repeats last transcription via TTS |
| **"estado del sistema"** | "claude estado", "como estás" | Speaks current system status |
| **"limpiar transcripciones"** | "borrar todo", "limpiar todo" | Clears transcription area |
| **"guardar transcripciones"** | "guardar todo", "guardar archivo" | Saves transcriptions to file |

### 3. Navigation Commands (Future)

Planned commands for case navigation:

| Command | Action |
|---------|--------|
| **"caso siguiente"** | Navigate to next case |
| **"caso anterior"** | Navigate to previous case |
| **"caso número [X]"** | Jump to specific case number |

## 🎯 How Commands Work

### Command Detection

1. **Confidence Scoring**: Each command is evaluated with a confidence score (0-1)
2. **Threshold**: Commands require >70% confidence to execute
3. **Context Awareness**: Commands are detected even within longer phrases
4. **Visual Feedback**: Blue flash indicator when command is recognized

### Command Priority

Commands are processed with the following priority:
1. Emergency commands (stop, cancel)
2. Dictation control commands
3. System commands
4. Navigation commands

### During Dictation Mode

When in dictation mode:
- Commands are still recognized and processed
- "fin dictado" takes immediate priority
- Other text is added to the dictation buffer

## 💡 Usage Tips

### Best Practices

1. **Clear Pronunciation**: Speak commands clearly and distinctly
2. **Natural Pause**: Add a slight pause after commands
3. **Avoid Mixing**: Don't mix commands with dictation in the same phrase
4. **Wait for Feedback**: Watch for the blue flash confirmation

### Command Examples

**Starting a dictation session:**
```
"inicio dictado" 
[pause]
"Observo mucosa gástrica con signos de inflamación..."
```

**Ending with specific command:**
```
"...compatible con gastritis crónica activa fin dictado"
```

**Canceling a dictation:**
```
"cancelar dictado"
[System responds: "Dictado cancelado"]
```

## 🔧 Customization

### Adding Custom Commands

To add custom commands, edit the `command_mappings` dictionary in `voice_bridge_app.py`:

```python
command_mappings = {
    ("mi comando", "mi comando alternativo"): self.my_custom_function,
    # Add more commands here
}
```

### Adjusting Confidence Threshold

In `config/voice_bridge_config_v2.ini`:
```ini
command_confidence_threshold = 0.7  # Default 70%
```

Lower values = more sensitive (more false positives)
Higher values = less sensitive (might miss commands)

## 🌍 Language Support

### Current Support
- Spanish (Colombian) - es-CO
- Commands optimized for medical terminology

### Planned Support
- English commands
- Portuguese (Brazilian)
- Other Spanish variants

## 🐛 Troubleshooting

### Commands Not Recognized

1. **Check microphone levels**
   - Ensure input volume is adequate
   - Test with system recorder

2. **Pronunciation issues**
   - Speak more slowly
   - Enunciate clearly
   - Add pauses around commands

3. **Background noise**
   - Reduce ambient noise
   - Use directional microphone
   - Adjust confidence threshold

### False Command Detection

If normal dictation is being interpreted as commands:
1. Increase `command_confidence_threshold`
2. Use command prefixes like "claude"
3. Pause before actual commands

### Command Delays

If commands take too long to execute:
1. Check system performance
2. Reduce logging level
3. Disable unnecessary features

## 📊 Command Statistics

Voice Bridge tracks command usage for optimization:
- Most used commands
- Recognition success rate
- Average confidence scores
- Common misrecognitions

View statistics in logs:
```bash
grep "Comando ejecutado" ~/voice-bridge-claude/logs/voice_bridge_v2_*.log
```

## 🔮 Future Enhancements

Planned improvements for voice commands:
- Multi-language support
- Custom command macros
- Voice shortcuts for templates
- Command chaining
- Contextual commands based on workflow

---

*Last updated: January 2025*
*Voice Bridge v2.0*