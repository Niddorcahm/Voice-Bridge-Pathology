# Voice Bridge v2.0 - Medical Speech Recognition System

<p align="center">
  <img src="assets/voice-bridge-logo.png" alt="Voice Bridge Logo" width="200"/>
</p>

<p align="center">
  <strong>Professional voice recognition system specialized for medical dictation</strong>
  <br>
  <em>Optimized for pathology and continuous hands-free operation</em>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## 🎯 Overview

Voice Bridge v2 is a specialized speech recognition system designed for medical professionals, particularly pathologists who need to dictate observations while working with microscopes. It provides continuous dictation capabilities, voice commands, and seamless integration with AI assistants.

### Key Features

- 🎤 **Continuous Dictation Mode**: Dictate 100+ words without interruption
- 🗣️ **Voice Commands**: Full hands-free control
- ⏱️ **Smart Timeout**: Automatic finalization after 8 seconds of silence
- 🔊 **Anti-Coupling System**: TTS without feedback loops
- 🏥 **Medical Optimization**: Pre-configured medical terminology
- 🌍 **Multi-Language**: Optimized for Spanish (Colombian variant)

## 🚀 What's New in v2.0

- **Continuous dictation** with voice-controlled workflow
- **Automatic timeout** system with visual countdown
- **Medical term auto-correction** for common misrecognitions
- **Enhanced GUI** with dictation buffer display
- **Improved Azure Speech** configuration for long phrases

[See full changelog](CHANGELOG_v2.md)

## 📋 Requirements

### System Requirements
- Ubuntu 20.04+ (or compatible Linux distribution)
- Python 3.8+
- Microphone with good quality
- 4GB RAM minimum
- Internet connection for Azure Speech Services

### Software Dependencies
- Azure Cognitive Services Speech SDK 1.35.0+
- Python packages: pyautogui, pynput, pyyaml, tkinter
- Linux tools: wmctrl, xdotool, pulseaudio-utils

### Azure Account
- Active Azure subscription
- Speech Services resource
- Valid API key and region

## 🔧 Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/voice-bridge-pathology.git
cd voice-bridge-pathology

# Run installation script
chmod +x install.sh
./install.sh
```

### Manual Installation

1. **Set up Python environment**:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. **Install system dependencies**:
```bash
sudo apt install -y wmctrl xdotool xclip pulseaudio-utils
```

3. **Configure Azure credentials**:
```bash
export AZURE_SPEECH_KEY="your_key_here"
export AZURE_SPEECH_REGION="your_region"
```

4. **Run the application**:
```bash
python voice_bridge_app.py
```

## 📖 Usage

### Basic Workflow

1. **Start Voice Bridge**
   - Launch from applications menu or run `./start_voice_bridge.sh`

2. **Begin Recognition**
   - Press `Ctrl+Shift+V` or click "Start Recognition"

3. **Dictation Mode**
   - Say "inicio dictado" to start continuous mode
   - Speak naturally without pauses
   - System auto-finalizes after 8 seconds of silence
   - Or say "fin dictado" to stop manually

### Voice Commands

| Command | Action |
|---------|--------|
| "inicio dictado" | Start continuous dictation |
| "fin dictado" | End dictation and show preview |
| "cancelar dictado" | Cancel without saving |
| "enviar a claude" | Send to AI assistant |
| "repetir última" | Repeat last segment |
| "estado del sistema" | System status |

### Keyboard Shortcuts

- `Ctrl+Shift+V`: Start/Resume recognition
- `Ctrl+Shift+S`: Stop recognition
- `Ctrl+Shift+D`: Toggle dictation mode

## ⚙️ Configuration

### Configuration File

Edit `config/voice_bridge_config_v2.ini`:

```ini
[DEFAULT]
# Azure Settings
azure_speech_key = YOUR_KEY_HERE
azure_region = eastus
speech_language = es-CO
tts_voice = es-CO-SalomeNeural

# Behavior
dictation_timeout_seconds = 8
auto_correct_medical = true
anti_coupling = true

# Integration
auto_send_to_claude = false
claude_window_title = Claude
```

### Medical Dictionary

Add custom medical terms to improve recognition:

```bash
# Add to pathology dictionary
echo "your medical term" >> config/diccionarios/patologia_molecular.txt

# Add complete phrases
echo "common medical phrase" >> config/diccionarios/frases_completas.txt
```

## 🏥 Medical Optimizations

### Pre-configured Terms

The system includes 95+ medical terms commonly used in pathology:
- Diagnostic terms (carcinoma, adenoma, etc.)
- Techniques (immunohistochemistry, H&E staining)
- Classifications (Vienna, OLGA, OLGIM)
- Anatomical terms

### Auto-Corrections

Common misrecognitions are automatically corrected:
- "cloud" → "Claude"
- "basal cellular" → "basocelular"
- "nuclear polymorphism" → "pleomorfismo nuclear"

## 🔍 Troubleshooting

### Dictation Gets Cut Off
- Check timeout settings in configuration
- Ensure you're in DICTATION mode
- Increase `dictation_timeout_seconds`

### Commands Not Recognized
- Speak clearly with slight pause after command
- Check microphone levels
- Review logs for recognition confidence

### Audio Feedback Loop
- Enable `anti_coupling` in configuration
- Use headphones instead of speakers
- Reduce system volume

[See full troubleshooting guide](TROUBLESHOOTING.md)

## 📊 Performance

- **Accuracy**: ~95% with medical dictionary
- **Latency**: <200ms command response
- **Memory**: ~150MB RAM usage
- **CPU**: <5% during idle, 15-20% during recognition

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas for Contribution
- Additional language support
- Medical dictionary expansions
- GUI improvements
- Performance optimizations

## 📄 License

This project is licensed under the MIT License - see [LICENSE.md](LICENSE.md) for details.

## 🙏 Acknowledgments

- Medical professionals who provided terminology and testing
- Azure Cognitive Services team
- Open source speech recognition community

## 📮 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/voice-bridge-pathology/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/voice-bridge-pathology/discussions)
- **Email**: support@voicebridge.example.com

---

<p align="center">
  Made with ❤️ for the medical community
  <br>
  <a href="https://github.com/yourusername/voice-bridge-pathology">GitHub</a> •
  <a href="https://voicebridge.example.com">Website</a> •
  <a href="https://docs.voicebridge.example.com">Documentation</a>
</p>
