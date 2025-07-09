# Troubleshooting Guide - Voice Bridge for Pathology

This guide helps resolve common issues with Voice Bridge, organized by problem type with step-by-step solutions.

## 🚨 Emergency Quick Fixes

### System Won't Start
```bash
# Quick restart sequence
pkill -f voice_bridge_app.py
cd ~/voice-bridge-claude
source ~/.bashrc
./start_voice_bridge_gui.sh
```

### Recognition Stopped Working
```bash
# Emergency reset
[Ctrl+Shift+X]  # Emergency stop
[Ctrl+Shift+V]  # Restart recognition
# Should hear "Reconocimiento iniciado"
```

### Audio Completely Failed
```bash
# Reset audio system
pulseaudio --kill
pulseaudio --start
pactl set-default-source alsa_input.pci-0000_0b_00.4.analog-stereo.2
```

## 🔍 Diagnostic Tools

### System Status Check
```bash
#!/bin/bash
echo "=== Voice Bridge System Diagnostic ==="

# Check Azure connection
echo "1. Azure Connection:"
if [ -n "$AZURE_SPEECH_KEY" ]; then
    echo "   ✅ AZURE_SPEECH_KEY configured"
    # Test connection
    response=$(curl -s -w "%{http_code}" \
      -X POST \
      -H "Ocp-Apim-Subscription-Key: $AZURE_SPEECH_KEY" \
      -H "Content-Length: 0" \
      "https://$AZURE_SPEECH_REGION.api.cognitive.microsoft.com/sts/v1.0/issuetoken" \
      -o /dev/null)
    if [ "$response" = "200" ]; then
        echo "   ✅ Azure connectivity: OK"
    else
        echo "   ❌ Azure connectivity: FAILED (HTTP $response)"
    fi
else
    echo "   ❌ AZURE_SPEECH_KEY not configured"
fi

# Check audio devices
echo ""
echo "2. Audio Devices:"
pactl list sources short | head -5
default_source=$(pactl get-default-source)
echo "   Default source: $default_source"

# Check Python environment
echo ""
echo "3. Python Environment:"
if [ -d ~/voice-bridge-claude/voice-bridge-project/.venv ]; then
    echo "   ✅ Virtual environment exists"
    source ~/voice-bridge-claude/voice-bridge-project/.venv/bin/activate
    python -c "import azure.cognitiveservices.speech; print('   ✅ Azure Speech SDK available')" 2>/dev/null || echo "   ❌ Azure Speech SDK missing"
    python -c "import tkinter; print('   ✅ Tkinter available')" 2>/dev/null || echo "   ❌ Tkinter missing"
else
    echo "   ❌ Virtual environment missing"
fi

# Check medical dictionaries
echo ""
echo "4. Medical Dictionaries:"
if [ -f ~/voice-bridge-claude/config/diccionarios/patologia_molecular.txt ]; then
    count=$(grep -c '^[^#]' ~/voice-bridge-claude/config/diccionarios/patologia_molecular.txt)
    echo "   ✅ Pathology dictionary: $count terms"
else
    echo "   ❌ Pathology dictionary missing"
fi

if [ -f ~/voice-bridge-claude/config/diccionarios/frases_completas.txt ]; then
    count=$(grep -c '^[^#]' ~/voice-bridge-claude/config/diccionarios/frases_completas.txt)
    echo "   ✅ Complete phrases: $count phrases"
else
    echo "   ❌ Complete phrases dictionary missing"
fi

# Check system integration
echo ""
echo "5. System Integration:"
if [ -f ~/.local/share/applications/voice-bridge-pathology.desktop ]; then
    echo "   ✅ Application launcher exists"
else
    echo "   ❌ Application launcher missing"
fi

if [ -f ~/.local/share/pixmaps/voice-bridge-pathology.png ]; then
    echo "   ✅ Application icon exists"
else
    echo "   ❌ Application icon missing"
fi

echo ""
echo "=== Diagnostic Complete ==="
```

### Log Analysis
```bash
# Real-time log monitoring
tail -f ~/voice-bridge-claude/logs/voice_bridge_$(date +%Y%m%d).log

# Search for specific errors
grep -i error ~/voice-bridge-claude/logs/voice_bridge_*.log
grep -i "azure" ~/voice-bridge-claude/logs/voice_bridge_*.log
grep -i "recognition" ~/voice-bridge-claude/logs/voice_bridge_*.log
```

## 🔧 Installation Issues

### Python Environment Problems

#### Virtual Environment Won't Create
```bash
# Problem: python3 -m venv .venv fails
# Solution:
sudo apt update
sudo apt install python3-venv python3-pip python3-dev

# Recreate environment
cd ~/voice-bridge-claude/voice-bridge-project
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
```

#### Azure Speech SDK Installation Fails
```bash
# Problem: pip install azure-cognitiveservices-speech fails
# Solution:
source .venv/bin/activate

# Install build dependencies
sudo apt install build-essential libssl-dev libffi-dev

# Try alternative installation
pip install --no-cache-dir azure-cognitiveservices-speech

# If still fails, use specific version
pip install azure-cognitiveservices-speech==1.35.0
```

#### Import Errors
```bash
# Problem: ModuleNotFoundError
# Solution: Verify environment activation
cd ~/voice-bridge-claude/voice-bridge-project
source .venv/bin/activate
python -c "import sys; print(sys.prefix)"
# Should show path to .venv

# Reinstall problematic modules
pip uninstall azure-cognitiveservices-speech
pip install azure-cognitiveservices-speech
```

### System Dependencies Issues

#### Missing System Packages
```bash
# Problem: wmctrl or xdotool not found
# Solution:
sudo apt update
sudo apt install wmctrl xdotool xclip

# Verify installation
which wmctrl xdotool
wmctrl -l  # Should list windows
```

#### Audio System Problems
```bash
# Problem: PulseAudio/PipeWire not configured
# Solution:
sudo apt install pulseaudio pavucontrol alsa-utils

# Start PulseAudio if needed
pulseaudio --start

# Check audio system
systemctl --user status pulseaudio
pactl info
```

## ⚡ Configuration Issues

### Azure Speech Services

#### Authentication Errors (HTTP 401)
```bash
# Problem: Azure key rejected
# Diagnosis:
echo "Key length: $(echo $AZURE_SPEECH_KEY | wc -c)"
# Should be 65 characters (64 + newline)

echo "Region: $AZURE_SPEECH_REGION"
# Should be "eastus" or valid Azure region

# Solution: Verify and update credentials
nano ~/.bashrc
# Check: export AZURE_SPEECH_KEY="correct_key_here"
source ~/.bashrc

# Test manually
curl -H "Ocp-Apim-Subscription-Key: $AZURE_SPEECH_KEY" \
  "https://$AZURE_SPEECH_REGION.api.cognitive.microsoft.com/sts/v1.0/issuetoken"
```

#### Connection Timeout (HTTP timeout)
```bash
# Problem: Network connectivity
# Diagnosis:
ping -c 3 azure.microsoft.com
nslookup $AZURE_SPEECH_REGION.api.cognitive.microsoft.com

# Solution: Check firewall/proxy
sudo ufw status
# If firewall active, allow HTTPS
sudo ufw allow out 443

# Test with verbose curl
curl -v "https://$AZURE_SPEECH_REGION.api.cognitive.microsoft.com/"
```

#### Wrong Region Error (HTTP 403)
```bash
# Problem: Incorrect region configuration
# Solution: Verify Azure portal region
# Azure Portal → Your Speech Service → Overview → Location
# Update ~/.bashrc with correct region
export AZURE_SPEECH_REGION="correct_region"
source ~/.bashrc
```

### Audio Configuration

#### Microphone Not Detected
```bash
# Problem: No audio input
# Diagnosis:
pactl list sources short
# Should show audio sources

arecord -l
# Should list recording devices

# Solution: Configure default microphone
pactl set-default-source [your_microphone_id]

# Example:
pactl set-default-source alsa_input.pci-0000_0b_00.4.analog-stereo.2

# Test recording
arecord -f cd -t wav -d 5 test.wav
aplay test.wav
```

#### No Sound Output (TTS)
```bash
# Problem: TTS not audible
# Diagnosis:
pactl list sinks short
speaker-test -t wav -c 2 -l 1

# Solution: Configure default speaker
pactl set-default-sink [your_speaker_id]

# Test TTS manually
echo "test speech" | festival --tts
# Or use espeak
espeak "test speech"
```

#### Audio Permissions
```bash
# Problem: Permission denied accessing audio
# Solution: Add user to audio group
sudo usermod -a -G audio $USER
# Logout and login again

# Verify group membership
groups $USER | grep audio
```

## 🎤 Recognition Issues

### Medical Terms Not Recognized

#### Missing from Dictionary
```bash
# Problem: "pleomorfismo" recognized as "empleomorfismo"
# Solution: Verify dictionary loading
grep -i "pleomorfismo" ~/voice-bridge-claude/config/diccionarios/*.txt

# If missing, add term
~/voice-bridge-claude/scripts/agregar_termino_medico.sh "pleomorfismo nuclear" patologia_molecular

# Restart Voice Bridge to reload
```

#### Dictionary Not Loading
```bash
# Problem: Log shows "0 términos cargados"
# Diagnosis:
ls -la ~/voice-bridge-claude/config/diccionarios/
# Check file permissions and existence

# Check file content
head -20 ~/voice-bridge-claude/config/diccionarios/patologia_molecular.txt

# Solution: Recreate dictionary files
# See INSTALL.md for dictionary creation commands
```

#### Phrases Being Cut
```bash
# Problem: Long medical phrases split into segments
# Solution: Check timeout configuration
grep -A 10 "medical_mode.*true" ~/voice-bridge-claude/voice-bridge-project/voice_bridge_app.py

# Verify timeout settings in logs
grep -i "timeout" ~/voice-bridge-claude/logs/voice_bridge_*.log

# If needed, increase timeouts in code:
# SpeechServiceConnection_EndSilenceTimeoutMs = "3000"
# Speech_SegmentationSilenceTimeoutMs = "1500"
```

### Low Recognition Confidence

#### Poor Audio Quality
```bash
# Problem: Recognition confidence consistently low
# Solution: Optimize audio settings
pactl set-source-volume @DEFAULT_SOURCE@ 85%
pactl set-source-mute @DEFAULT_SOURCE@ false

# Check for noise suppression
pactl load-module module-echo-cancel

# Adjust microphone position
# Optimal: 6-12 inches from mouth, avoid breathing directly on mic
```

#### Background Noise
```bash
# Problem: Recognition degraded by noise
# Solution: Environmental optimization
# - Close unnecessary audio applications
# - Move away from noise sources (fans, air conditioning)
# - Use noise-canceling microphone if available

# Software noise reduction
pactl load-module module-echo-cancel aec_method=webrtc
```

### Hotkey Issues

#### Global Hotkeys Not Working
```bash
# Problem: Ctrl+Shift+V/S not responding
# Diagnosis:
ps aux | grep voice_bridge
# Should show running process

# Check for key conflicts
# System Settings → Keyboard → Shortcuts
# Look for conflicting Ctrl+Shift+V assignments

# Solution: Restart with elevated permissions
pkill -f voice_bridge_app.py
cd ~/voice-bridge-claude
./start_voice_bridge_gui.sh
```

#### Permissions for Global Hotkeys
```bash
# Problem: pynput permission denied
# Solution: Add user to input group
sudo usermod -a -G input $USER
# Logout and login

# Alternative: Run with sudo (not recommended for production)
sudo ./start_voice_bridge_gui.sh
```

## 🖥️ System Integration Issues

### Application Icon Not Appearing

#### Desktop Entry Problems
```bash
# Problem: Icon not in applications menu
# Diagnosis:
ls -la ~/.local/share/applications/voice-bridge*
desktop-file-validate ~/.local/share/applications/voice-bridge-pathology.desktop

# Solution: Recreate desktop entry
cat > ~/.local/share/applications/voice-bridge-pathology.desktop << 'EOF'
[Desktop Entry]
Name=Voice Bridge
Exec=/home/$(whoami)/voice-bridge-claude/start_voice_bridge_gui.sh
Icon=voice-bridge-pathology
Type=Application
Terminal=false
Categories=AudioVideo;
Comment=Reconocimiento de voz para patología molecular
EOF

chmod +x ~/.local/share/applications/voice-bridge-pathology.desktop
update-desktop-database ~/.local/share/applications/
```

#### Icon File Missing
```bash
# Problem: Icon not displaying
# Solution: Create or restore icon
ls -la ~/.local/share/pixmaps/voice-bridge*

# If missing, create simple icon
convert -size 128x128 xc:blue -pointsize 16 -fill white -gravity center \
  -annotate +0+0 "Voice\nBridge" ~/.local/share/pixmaps/voice-bridge-pathology.png

# Or copy from system icons
cp /usr/share/pixmaps/audio-input-microphone.png ~/.local/share/pixmaps/voice-bridge-pathology.png
```

### Claude Desktop Integration

#### Window Not Found
```bash
# Problem: "Claude Desktop window not found"
# Diagnosis:
wmctrl -l | grep -i claude
# Should show Claude window

# Check Claude Desktop running
ps aux | grep claude

# Solution: Ensure Claude Desktop is open and titled "Claude"
# Restart Claude Desktop if necessary
```

#### Text Not Sending
```bash
# Problem: Text not appearing in Claude
# Diagnosis:
which xdotool wmctrl
# Both should be installed

# Test window automation
xdotool search --name "Claude" windowactivate
xdotool type "test message"

# Solution: Install missing tools
sudo apt install xdotool wmctrl

# Check Claude window title exactly matches "Claude"
wmctrl -l | grep Claude
# Should show exactly "Claude", not "Claude Desktop" or similar
```

#### Clipboard Integration Fallback
```bash
# Problem: Direct sending fails
# Solution: Use clipboard method
# Add to voice_bridge_app.py:

def send_via_clipboard(self, text):
    """Alternative sending method via clipboard"""
    import subprocess
    # Copy to clipboard
    subprocess.run(['xclip', '-selection', 'clipboard'], 
                   input=text, text=True)
    # Activate Claude window
    subprocess.run(['wmctrl', '-a', 'Claude'])
    # Paste
    subprocess.run(['xdotool', 'key', 'ctrl+v'])
```

## 📱 GUI Issues

### Window Won't Open

#### Tkinter Problems
```bash
# Problem: GUI doesn't appear
# Diagnosis:
python3 -c "import tkinter; print('Tkinter OK')"

# Solution: Install GUI dependencies
sudo apt install python3-tk python3-pil python3-pil.imagetk

# For virtual environment
source ~/voice-bridge-claude/voice-bridge-project/.venv/bin/activate
pip install pillow
```

#### Display Issues
```bash
# Problem: GUI appears corrupted or missing elements
# Solution: Check display environment
echo $DISPLAY
# Should show :0 or similar

# For remote/SSH sessions
export DISPLAY=:0
# Or use X11 forwarding: ssh -X user@host
```

### GUI Elements Not Responding

#### Button Clicks Not Working
```bash
# Problem: Buttons don't respond
# Diagnosis: Check for Python errors
python3 ~/voice-bridge-claude/voice-bridge-project/voice_bridge_app.py
# Run directly to see error messages

# Check for threading issues in logs
grep -i "thread\|gui" ~/voice-bridge-claude/logs/voice_bridge_*.log
```

#### Text Areas Not Updating
```bash
# Problem: Transcriptions not appearing
# Diagnosis: Check queue processing
# Look for queue-related errors in logs
grep -i "queue\|transcription" ~/voice-bridge-claude/logs/voice_bridge_*.log

# Solution: Restart application
pkill -f voice_bridge_app.py
./start_voice_bridge_gui.sh
```

## 🔊 TTS Issues

### No Voice Confirmations

#### TTS Not Enabled
```bash
# Problem: No voice feedback
# Solution: Enable TTS in GUI
# Check "Respuestas por voz (TTS)" checkbox

# Verify in configuration
grep "tts_enabled" ~/voice-bridge-claude/config/voice_bridge_config.ini
# Should show: tts_enabled = true
```

#### Azure TTS Problems
```bash
# Problem: TTS configuration errors
# Diagnosis: Check TTS voice setting
echo $TTS_VOICE
# Should be: es-CO-SalomeNeural

# Test TTS manually
curl -X POST \
  -H "Ocp-Apim-Subscription-Key: $AZURE_SPEECH_KEY" \
  -H "Content-Type: application/ssml+xml" \
  -d '<speak version="1.0" xml:lang="es-CO">Prueba de síntesis de voz</speak>' \
  "https://$AZURE_SPEECH_REGION.tts.speech.microsoft.com/cognitiveservices/v1"
```

#### Audio Output Issues
```bash
# Problem: TTS generates but no sound
# Solution: Check audio output
pactl list sinks short
pactl set-default-sink [your_speaker]

# Test system audio
speaker-test -t wav -c 2 -l 1

# Verify volume levels
pactl get-sink-volume @DEFAULT_SINK@
pactl set-sink-volume @DEFAULT_SINK@ 85%
```

## 🚀 Performance Issues

### High CPU Usage

#### Python Process Optimization
```bash
# Problem: voice_bridge_app.py using high CPU
# Diagnosis:
top -p $(pgrep -f voice_bridge_app.py)
htop  # Monitor real-time usage

# Solution: Restart application
pkill -f voice_bridge_app.py
./start_voice_bridge_gui.sh

# Check for infinite loops in logs
grep -A 5 -B 5 "ERROR\|Exception" ~/voice-bridge-claude/logs/voice_bridge_*.log
```

#### Audio Processing Optimization
```bash
# Problem: High audio processing load
# Solution: Optimize audio settings
# Reduce audio quality if needed
export PULSE_LATENCY_MSEC=50  # Increase latency to reduce CPU

# Check audio sample rate
pactl list sources | grep -A 10 "Source #"
# Use standard rates: 44100 or 48000 Hz
```

### Memory Issues

#### Memory Leaks
```bash
# Problem: Increasing memory usage over time
# Diagnosis:
ps aux | grep voice_bridge | awk '{print $6}'  # Memory usage in KB

# Solution: Regular restarts
# Add to cron for automatic restart
crontab -e
# Add: 0 */4 * * * pkill -f voice_bridge_app.py && sleep 5 && /home/$(whoami)/voice-bridge-claude/start_voice_bridge_gui.sh
```

#### Low Memory Systems
```bash
# Problem: System with <4GB RAM
# Solution: Optimize settings
# Reduce dictionary size temporarily
head -50 ~/voice-bridge-claude/config/diccionarios/patologia_molecular.txt > temp.txt
mv temp.txt ~/voice-bridge-claude/config/diccionarios/patologia_molecular.txt

# Close unnecessary applications during use
```

## 🔄 Recovery Procedures

### Complete System Reset

#### Nuclear Option - Full Reinstall
```bash
#!/bin/bash
echo "=== Voice Bridge Complete Reset ==="

# Backup user data
mkdir -p ~/voice-bridge-backup
cp -r ~/voice-bridge-claude/logs ~/voice-bridge-backup/
cp -r ~/voice-bridge-claude/config ~/voice-bridge-backup/

# Remove everything
rm -rf ~/voice-bridge-claude
rm -f ~/.local/share/applications/voice-bridge*
rm -f ~/.local/share/pixmaps/voice-bridge*

# Reinstall from scratch
# Follow INSTALL.md completely

echo "✅ Reset complete - reinstall required"
```

#### Partial Reset - Keep Configuration
```bash
#!/bin/bash
echo "=== Voice Bridge Partial Reset ==="

# Stop all processes
pkill -f voice_bridge_app.py

# Reset Python environment only
cd ~/voice-bridge-claude/voice-bridge-project
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install azure-cognitiveservices-speech pyautogui pynput

# Restart
cd ~/voice-bridge-claude
./start_voice_bridge_gui.sh
```

### Configuration Recovery

#### Restore Default Configuration
```bash
# Backup current config
cp ~/voice-bridge-claude/config/voice_bridge_config.ini ~/voice-bridge-claude/config/voice_bridge_config.ini.backup

# Restore defaults
cat > ~/voice-bridge-claude/config/voice_bridge_config.ini << 'EOF'
[DEFAULT]
azure_speech_key = 
azure_region = eastus
speech_language = es-CO
tts_voice = es-CO-SalomeNeural
hotkey_start = ctrl+shift+v
hotkey_stop = ctrl+shift+s
hotkey_emergency = ctrl+shift+x
auto_send_to_claude = true
claude_window_title = Claude
medical_mode = true
confidence_threshold = 0.2
tts_enabled = true
claude_activation_delay = 0.2
EOF

# Restore Azure key
nano ~/voice-bridge-claude/config/voice_bridge_config.ini
# Add your Azure key
```

## 📞 Getting Help

### Log Collection for Support
```bash
#!/bin/bash
echo "=== Voice Bridge Support Information ==="

# System information
echo "System: $(lsb_release -d | cut -f2)"
echo "Python: $(python3 --version)"
echo "User: $USER"
echo "Date: $(date)"
echo ""

# Configuration status
echo "Azure configured: $([ -n "$AZURE_SPEECH_KEY" ] && echo "Yes" || echo "No")"
echo "Region: $AZURE_SPEECH_REGION"
echo "TTS Voice: $TTS_VOICE"
echo ""

# File status
echo "Files status:"
echo "- Config: $([ -f ~/voice-bridge-claude/config/voice_bridge_config.ini ] && echo "✅" || echo "❌")"
echo "- App: $([ -f ~/voice-bridge-claude/voice-bridge-project/voice_bridge_app.py ] && echo "✅" || echo "❌")"
echo "- Dictionaries: $(ls ~/voice-bridge-claude/config/diccionarios/*.txt 2>/dev/null | wc -l) files"
echo ""

# Recent errors
echo "Recent errors:"
tail -20 ~/voice-bridge-claude/logs/voice_bridge_*.log | grep -i error | tail -5
```

### Community Support
- **GitHub Issues**: Report bugs with log output
- **Discussions**: Community help and tips
- **Medical Community**: Pathology-specific terminology questions

### Emergency Contacts
- **Critical Issues**: Create GitHub issue with "urgent" label
- **Medical Workflow**: Include specialty and use case details
- **Technical Problems**: Include full diagnostic output

---

## 📋 Quick Reference

### Common Error Codes
- **HTTP 401**: Azure authentication failed - check key
- **HTTP 403**: Permissions or quota issues - check Azure portal
- **HTTP 404**: Wrong region or endpoint - verify configuration
- **Audio Error**: Microphone issues - check pactl commands
- **Import Error**: Python dependencies - check virtual environment

### Essential Commands
```bash
# Restart Voice Bridge
pkill -f voice_bridge_app.py && ./start_voice_bridge_gui.sh

# Test Azure
curl -H "Ocp-Apim-Subscription-Key: $AZURE_SPEECH_KEY" \
  "https://$AZURE_SPEECH_REGION.api.cognitive.microsoft.com/sts/v1.0/issuetoken"

# Check audio
pactl list sources short

# View logs
tail -f ~/voice-bridge-claude/logs/voice_bridge_*.log

# Add medical term
~/voice-bridge-claude/scripts/agregar_termino_medico.sh "term" patologia_molecular
```

Most issues can be resolved by restarting the application and verifying Azure connectivity. For persistent problems, collect diagnostic information and consult the community or create a GitHub issue.

---

**Remember**: Voice Bridge is designed for medical professionals. When reporting issues, include information about your specific pathology workflow to help improve the system for the medical community.