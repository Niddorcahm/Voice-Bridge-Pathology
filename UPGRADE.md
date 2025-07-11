# Upgrading to Voice Bridge v2.0

This guide walks you through upgrading from Voice Bridge v1.x to v2.0.

## 🚀 What's New in v2.0

- **Continuous Dictation Mode**: Dictate without interruptions
- **Voice Commands**: Full hands-free control
- **Auto-timeout System**: 8-second silence detection
- **Medical Corrections**: Automatic term fixes
- **Enhanced GUI**: Buffer display and status indicators

## 📋 Pre-Upgrade Checklist

- [ ] Voice Bridge v1.x is working
- [ ] Azure Speech SDK installed
- [ ] Python 3.8+ available
- [ ] 500MB free disk space
- [ ] Current configuration backed up

## 🔧 Upgrade Methods

### Method 1: Automatic Upgrade Script

```bash
cd voice-bridge-pathology
chmod +x scripts/upgrade_to_v2.sh
./scripts/upgrade_to_v2.sh
```

The script will:
1. Backup your v1 installation
2. Create v2 configuration
3. Check dependencies
4. Update launcher scripts

### Method 2: Manual Upgrade

#### Step 1: Backup Current Installation
```bash
cp -r ~/voice-bridge-claude ~/voice-bridge-claude-v1-backup
```

#### Step 2: Update Configuration
```bash
cd ~/voice-bridge-claude/config
cp voice_bridge_config.ini voice_bridge_config_v2.ini
```

Add these lines to `voice_bridge_config_v2.ini`:
```ini
# Voice Bridge v2 Settings
dictation_mode = continuous
anti_coupling = true
auto_correct_medical = true
dictation_timeout_seconds = 8
timeout_warning_seconds = 3
timeout_audio_warning = true
```

#### Step 3: Update Dependencies
```bash
source .venv/bin/activate
pip install --upgrade azure-cognitiveservices-speech
pip install -r requirements.txt
```

#### Step 4: Replace Application File
- Download the new `voice_bridge_app.py` v2
- Replace the existing file
- Keep the v1 backup

#### Step 5: Test the Upgrade
```bash
python voice_bridge_app.py
```

## 🔄 Configuration Migration

### Essential Settings to Review

1. **Azure Credentials**
   ```ini
   azure_speech_key = YOUR_KEY
   azure_region = YOUR_REGION
   ```

2. **New v2 Settings**
   ```ini
   dictation_mode = continuous
   dictation_timeout_seconds = 8
   auto_correct_medical = true
   ```

3. **Hotkeys** (new one added)
   ```ini
   hotkey_dictation = ctrl+shift+d
   ```

### Settings That Changed Defaults

| Setting | v1 Default | v2 Default | Notes |
|---------|------------|------------|-------|
| `auto_send_to_claude` | true | false | Now shows preview first |
| `confidence_threshold` | 0.7 | 0.5 | More permissive |
| `tts_enabled` | false | true | Voice feedback enabled |

## 🧪 Testing Your Upgrade

### Basic Functionality Test
1. Start Voice Bridge v2
2. Press `Ctrl+Shift+V` to start recognition
3. Say "prueba de reconocimiento"
4. Verify text appears

### Dictation Mode Test
1. Say "inicio dictado"
2. Speak several sentences
3. Wait 8 seconds
4. Verify auto-finalization

### Command Test
1. During dictation, say "fin dictado"
2. Verify command is recognized
3. Check preview appears

## ⚠️ Breaking Changes

### API Changes
- Configuration file: now `voice_bridge_config_v2.ini`
- Some Azure properties require SDK 1.35.0+
- New GUI elements require tkinter 8.6+

### Behavioral Changes
- Dictation doesn't auto-send by default
- Commands can interrupt dictation
- TTS is enabled by default

## 🐛 Troubleshooting

### Issue: PropertyId Errors
```
AttributeError: 'PropertyId' has no attribute 'RequestPunctuationMode'
```

**Solution**: Update Azure Speech SDK:
```bash
pip install --upgrade azure-cognitiveservices-speech
```

### Issue: Commands Not Working
- Check `command_confidence_threshold` (default 0.7)
- Ensure dictation mode is active
- Speak commands clearly

### Issue: Old Configuration
- Make sure using `voice_bridge_config_v2.ini`
- Not `voice_bridge_config.ini`

## 📜 Rollback Instructions

If you need to rollback to v1:

1. **Restore backup**:
   ```bash
   cp backup_v1_*/voice_bridge_app.py .
   cp backup_v1_*/config/voice_bridge_config.ini config/
   ```

2. **Use v1 launcher**:
   ```bash
   ./start_voice_bridge.sh  # Instead of v2
   ```

3. **Remove v2 config**:
   ```bash
   rm config/voice_bridge_config_v2.ini
   ```

## 🎯 Next Steps

After upgrading:

1. **Read the new documentation**:
   - [Voice Commands Guide](docs/VOICE_COMMANDS.md)
   - [Dictation Mode Guide](docs/DICTATION_MODE.md)

2. **Customize your setup**:
   - Adjust timeouts for your workflow
   - Add custom medical terms
   - Configure hotkeys

3. **Practice new features**:
   - Master voice commands
   - Get comfortable with dictation mode
   - Optimize your workflow

## 💬 Getting Help

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review logs in `~/voice-bridge-claude/logs/`
- Open an issue on GitHub
- Join our discussions

---

*Upgrade guide for Voice Bridge v2.0*
*Last updated: January 2025*