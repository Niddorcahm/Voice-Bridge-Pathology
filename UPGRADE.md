# Upgrading to Voice Bridge v2.0

This guide will help you upgrade from Voice Bridge v1.x to v2.0.

## 🚨 Before You Begin

### Important Notes
- Voice Bridge v2.0 introduces breaking changes in configuration
- Backup your current installation before upgrading
- The upgrade process takes approximately 10-15 minutes

### Prerequisites
- Voice Bridge v1.x installed and working
- Azure Speech SDK 1.35.0 or higher
- Active internet connection

## 📋 Pre-Upgrade Checklist

- [ ] Backup your current configuration
- [ ] Save any custom dictionaries
- [ ] Note your Azure credentials
- [ ] Close Voice Bridge if running
- [ ] Have your terminal ready

## 🔄 Upgrade Steps

### Step 1: Backup Current Installation

```bash
# Create backup directory
mkdir -p ~/voice-bridge-backups
cd ~/voice-bridge-claude

# Backup entire installation
tar -czf ~/voice-bridge-backups/voice-bridge-v1-$(date +%Y%m%d).tar.gz .

# Verify backup
ls -la ~/voice-bridge-backups/
```

### Step 2: Update Python Dependencies

```bash
# Activate virtual environment
cd ~/voice-bridge-claude/voice-bridge-project
source .venv/bin/activate

# Upgrade Azure Speech SDK
pip install --upgrade azure-cognitiveservices-speech>=1.35.0

# Verify version
pip show azure-cognitiveservices-speech | grep Version
# Should show: Version: 1.35.0 or higher
```

### Step 3: Download v2.0 Files

#### Option A: Using Git
```bash
cd ~/voice-bridge-claude
git pull origin v2.0.0
```

#### Option B: Manual Download
```bash
# Download v2 application file
cd ~/voice-bridge-claude/voice-bridge-project
wget https://raw.githubusercontent.com/yourusername/voice-bridge-pathology/v2.0.0/voice_bridge_app.py -O voice_bridge_app_v2.py

# Backup v1
mv voice_bridge_app.py voice_bridge_app_v1_backup.py
mv voice_bridge_app_v2.py voice_bridge_app.py
```

### Step 4: Migrate Configuration

```bash
cd ~/voice-bridge-claude/config

# Copy v1 config to v2
cp voice_bridge_config.ini voice_bridge_config_v2.ini

# Edit v2 config
nano voice_bridge_config_v2.ini
```

Add these new sections to your config file:

```ini
# New v2 options (add at the end)
dictation_mode = continuous
anti_coupling = true
auto_correct_medical = true
dictation_timeout_seconds = 8
timeout_warning_seconds = 3
timeout_audio_warning = true
```

### Step 5: Update Launcher Scripts

```bash
cd ~/voice-bridge-claude

# Create v2 launcher
cat > start_voice_bridge_v2.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source voice-bridge-project/.venv/bin/activate
export CONFIG_FILE="config/voice_bridge_config_v2.ini"
python voice-bridge-project/voice_bridge_app.py
EOF

chmod +x start_voice_bridge_v2.sh
```

### Step 6: Update Desktop Entry

```bash
# Update desktop file for v2
sed -i 's/start_voice_bridge.sh/start_voice_bridge_v2.sh/g' ~/.local/share/applications/voice-bridge-pathology.desktop
sed -i 's/Voice Bridge/Voice Bridge v2/g' ~/.local/share/applications/voice-bridge-pathology.desktop

# Refresh desktop database
update-desktop-database ~/.local/share/applications/
```

### Step 7: Test the Upgrade

```bash
# Run v2 from terminal first
cd ~/voice-bridge-claude
./start_voice_bridge_v2.sh

# Check for errors in log
tail -f logs/voice_bridge_v2_$(date +%Y%m%d).log
```

## 🔍 Verifying the Upgrade

### Quick Functionality Test

1. **Start Voice Bridge v2**
   - Should show "Voice Bridge v2.0" in title
   - New dictation buffer area visible
   - Timeout progress bar present

2. **Test Voice Commands**
   ```
   Say: "inicio dictado"
   Response: Status changes to "🔴 DICTADO ACTIVO"
   
   Say: "fin dictado"
   Response: Preview window appears
   ```

3. **Test Timeout**
   - Start dictation
   - Stay silent for 8 seconds
   - Should auto-finalize with countdown

### Configuration Verification

```bash
# Check config is loaded
grep "v2" ~/voice-bridge-claude/logs/voice_bridge_v2_*.log

# Verify new options
grep "dictation_mode" ~/voice-bridge-claude/config/voice_bridge_config_v2.ini
```

## 🔧 Troubleshooting Common Issues

### Issue: PropertyId Errors

If you see errors about `PropertyId` attributes:

```python
# Error: AttributeError: type object 'PropertyId' has no attribute 'SpeechServiceResponse_RequestPunctuationMode'
```

**Solution**: Your Azure SDK is outdated. Run:
```bash
pip install --upgrade azure-cognitiveservices-speech==1.35.0
```

### Issue: Configuration Not Loading

If v2 features aren't working:

1. Check config file name is correct
2. Verify new options are present
3. Restart Voice Bridge

### Issue: Commands Not Working

If voice commands aren't recognized:

1. Check you're in v2 (title bar shows v2)
2. Speak commands clearly with pause
3. Check log for command detection

## 🔄 Rolling Back to v1

If you need to revert to v1:

```bash
cd ~/voice-bridge-claude

# Restore v1 files
cd voice-bridge-project
mv voice_bridge_app.py voice_bridge_app_v2_failed.py
mv voice_bridge_app_v1_backup.py voice_bridge_app.py

# Use v1 launcher
cd ..
./start_voice_bridge.sh  # Original v1 launcher
```

## 📊 What's Different in v2

### User Interface
- New dictation buffer display (yellow area)
- Timeout progress bar
- Enhanced status indicator
- Command flash notifications

### Behavior Changes
- `auto_send_to_claude` defaults to false
- Dictation mode requires voice activation
- 8-second timeout is automatic
- TTS confirmations are queued

### New Features to Try
1. Long dictations (100+ words)
2. Voice command workflow
3. Auto-corrections
4. Timeout countdown

## 🎉 Upgrade Complete!

Congratulations! You've successfully upgraded to Voice Bridge v2.0.

### Next Steps
- Read the [v2 Usage Guide](USAGE.md)
- Configure your preferred settings
- Test with real medical dictations
- Report any issues on GitHub

### Getting Help
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [CHANGELOG_v2.md](CHANGELOG_v2.md)
- Open an issue on GitHub

---

*Thank you for upgrading to Voice Bridge v2.0!*