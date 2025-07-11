# Continuous Dictation Mode Guide

## Overview

Voice Bridge v2 introduces continuous dictation mode for uninterrupted medical dictation. Perfect for pathology reports where hands-free operation is essential.

## Key Features

- **Uninterrupted Dictation**: 100+ words continuously
- **Smart Timeout**: 8-second auto-finalization
- **Real-time Buffer**: See text as you speak
- **Voice Commands**: Full control without keyboard

## How to Use

### Starting Dictation
1. Press `Ctrl+Shift+V` (start recognition)
2. Say **"inicio dictado"**
3. Begin speaking naturally

### During Dictation
- Speak continuously
- 8-second timeout with countdown
- Commands still work
- Buffer shows last segments

### Ending Dictation
- **Manual**: Say "fin dictado"
- **Automatic**: 8 seconds silence
- **Cancel**: Say "cancelar dictado"

## Configuration

```ini
# In voice_bridge_config_v2.ini
dictation_timeout_seconds = 8
timeout_warning_seconds = 3
auto_correct_medical = true
```

## Tips
- Speak clearly and consistently
- Prepare your thoughts first
- Use commands for control
- Adjust timeout as needed

## Examples

**Gastric Biopsy**:
"inicio dictado... Fragmentos de mucosa gástrica con gastritis crónica... fin dictado"

**Skin Sample**:
"inicio dictado... Piel con carcinoma basocelular... [8 sec silence auto-ends]"