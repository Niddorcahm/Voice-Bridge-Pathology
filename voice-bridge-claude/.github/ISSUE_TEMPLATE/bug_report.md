---
name: Bug Report
about: Create a report to help us improve Voice Bridge Pathology
title: '[BUG] '
labels: 'bug'
assignees: ''

---

## Bug Description
A clear and concise description of what the bug is.

## To Reproduce
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
A clear and concise description of what you expected to happen.

## Actual Behavior
A clear and concise description of what actually happened.

## Screenshots/Logs
If applicable, add screenshots or log excerpts to help explain your problem.

```
[Paste relevant log entries here]
```

## Environment Information
**Please complete the following information:**

### System Environment
- OS: [e.g. Ubuntu 20.04, Windows 10]
- Python Version: [e.g. 3.10.5]
- Voice Bridge Version: [e.g. 1.0.0]
- Installation Method: [e.g. manual, Docker, UV]

### Azure Configuration
- Azure Speech Region: [e.g. eastus]
- Speech Language: [e.g. es-CO]
- TTS Voice: [e.g. es-CO-SalomeNeural]

### Medical Environment
- Medical Setting: [e.g. Hospital, Clinic, Research]
- Primary Use Case: [e.g. Pathology Reports, General Dictation]
- HIPAA Requirements: [Yes/No]

### Hardware
- Microphone Type: [e.g. Built-in, USB Headset, Professional Mic]
- Audio System: [e.g. PulseAudio, ALSA]
- RAM: [e.g. 8GB]
- CPU: [e.g. Intel i5-8250U]

## Configuration Files
**Please provide relevant configuration (remove sensitive information like API keys):**

### Voice Bridge Configuration
```ini
[Paste relevant sections from voice_bridge_config.ini - REMOVE AZURE_SPEECH_KEY]
```

### Environment Variables
```bash
# List relevant environment variables (HIDE sensitive values)
AZURE_SPEECH_REGION=eastus
SPEECH_LANGUAGE=es-CO
# etc.
```

## Medical Dictionary Information
- Primary Dictionary Terms: [approximate count]
- Custom Terms Added: [Yes/No, approximate count]
- Dictionary Language: [e.g. Spanish Colombian]

## Error Messages
**Complete error messages and stack traces:**

```
[Paste complete error messages here]
```

## Steps Already Tried
List any troubleshooting steps you've already attempted:
- [ ] Checked Azure connectivity with test_azure_connection.sh
- [ ] Verified configuration file syntax
- [ ] Tested with different microphone
- [ ] Reviewed application logs
- [ ] Checked system dependencies
- [ ] Restarted Voice Bridge
- [ ] Other: [describe]

## Impact Assessment
**Please check all that apply:**
- [ ] Prevents application from starting
- [ ] Affects speech recognition accuracy
- [ ] Causes crashes during operation
- [ ] Impacts Claude Desktop integration
- [ ] Affects medical dictionary functionality
- [ ] Security or privacy concern
- [ ] Performance degradation
- [ ] Documentation issue

## Medical Context (if applicable)
**For medical usage issues:**
- Specialty: [e.g. Pathology, General Medicine]
- Typical session length: [e.g. 30 minutes, 2 hours]
- Types of medical terms: [e.g. Histopathology, Clinical diagnostics]
- Compliance requirements: [e.g. HIPAA, local regulations]

## Urgency Level
- [ ] Critical - Prevents medical work
- [ ] High - Significantly impacts productivity
- [ ] Medium - Workaround available
- [ ] Low - Minor inconvenience

## Additional Context
Add any other context about the problem here, including:
- When the issue started occurring
- Whether it worked previously
- Any recent system changes
- Network environment (hospital, clinic, home)
- Other applications running simultaneously

## Privacy Notice
Please ensure you have removed all sensitive information including:
- Patient names or identifiers
- Azure API keys
- Personal information
- Proprietary medical data
- Network configuration details

---

**For Voice Bridge Development Team:**
- [ ] Bug confirmed and reproduced
- [ ] Assigned to team member
- [ ] Priority level set
- [ ] Medical review needed (if applicable)
- [ ] Security review needed (if applicable)
