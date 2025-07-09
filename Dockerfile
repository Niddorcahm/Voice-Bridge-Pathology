# Voice Bridge Pathology - Docker Configuration
# Multi-stage build for optimized production container

# ==========================================
# Build Stage
# ==========================================
FROM python:3.10-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive
ARG PYTHON_VERSION=3.10

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    pkg-config \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Install UV for fast package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Create build directory
WORKDIR /build

# Copy dependency files
COPY requirements.txt pyproject.toml ./

# Create virtual environment and install dependencies
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install -r requirements.txt

# ==========================================
# Runtime Stage
# ==========================================
FROM python:3.10-slim as runtime

# Set runtime arguments
ARG DEBIAN_FRONTEND=noninteractive
ARG USER_ID=1000
ARG GROUP_ID=1000

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Audio system dependencies
    pulseaudio \
    alsa-utils \
    portaudio19-dev \
    # GUI dependencies (for tkinter)
    python3-tk \
    xvfb \
    # System automation tools
    wmctrl \
    xdotool \
    # Network and security tools
    curl \
    ca-certificates \
    # Process management
    supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -g ${GROUP_ID} voicebridge \
    && useradd -m -u ${USER_ID} -g ${GROUP_ID} -s /bin/bash voicebridge \
    && usermod -aG audio voicebridge

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set up application directory
WORKDIR /app

# Copy application files
COPY voice_bridge_app.py ./
COPY examples/ examples/
COPY scripts/ scripts/
COPY config/ config/

# Create necessary directories with correct permissions
RUN mkdir -p \
    /app/logs \
    /app/audit-logs \
    /app/backups \
    /app/config/diccionarios \
    && chown -R voicebridge:voicebridge /app

# Copy configuration files
COPY examples/voice_bridge_config_example.ini /app/config/voice_bridge_config.ini

# Create default medical dictionaries
RUN echo "# Docker Medical Dictionary - Pathology" > /app/config/diccionarios/patologia_molecular.txt \
    && echo "carcinoma basocelular" >> /app/config/diccionarios/patologia_molecular.txt \
    && echo "adenocarcinoma" >> /app/config/diccionarios/patologia_molecular.txt \
    && echo "pleomorfismo nuclear" >> /app/config/diccionarios/patologia_molecular.txt \
    && echo "células atípicas" >> /app/config/diccionarios/patologia_molecular.txt \
    && echo "gastritis crónica" >> /app/config/diccionarios/patologia_molecular.txt \
    && echo "metaplasia intestinal" >> /app/config/diccionarios/patologia_molecular.txt \
    && echo "" >> /app/config/diccionarios/patologia_molecular.txt

RUN echo "# Docker Medical Dictionary - Complete Phrases" > /app/config/diccionarios/frases_completas.txt \
    && echo "compatible con neoplasia maligna" >> /app/config/diccionarios/frases_completas.txt \
    && echo "negativo para malignidad" >> /app/config/diccionarios/frases_completas.txt \
    && echo "células atípicas escasas" >> /app/config/diccionarios/frases_completas.txt \
    && echo "infiltrado inflamatorio crónico" >> /app/config/diccionarios/frases_completas.txt \
    && echo "gastritis crónica moderada" >> /app/config/diccionarios/frases_completas.txt

# Set up supervisor configuration for process management
COPY docker/supervisord.conf /etc/supervisor/conf.d/voice-bridge.conf

# Create entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set permissions
RUN chown -R voicebridge:voicebridge /app \
    && chmod 755 /app/scripts/*.sh \
    && chmod 600 /app/config/voice_bridge_config.ini

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import azure.cognitiveservices.speech; print('OK')" || exit 1

# Security: Use non-root user
USER voicebridge

# Environment variables
ENV PYTHONPATH=/app
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV DISPLAY=:99

# Expose ports (if needed for future web interface)
EXPOSE 8080

# Volume mounts for persistent data
VOLUME ["/app/config", "/app/logs", "/app/audit-logs", "/app/backups"]

# Default command
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "voice_bridge_app.py"]

# ==========================================
# Build Metadata
# ==========================================
LABEL maintainer="Voice Bridge Development Team <voice-bridge@medical-ai.org>"
LABEL version="1.0.0"
LABEL description="Medical voice recognition system for pathology professionals"
LABEL org.opencontainers.image.title="Voice Bridge Pathology"
LABEL org.opencontainers.image.description="Medical voice recognition system with Azure Speech Services integration"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.vendor="Voice Bridge Medical AI"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/voice-bridge/voice-bridge-pathology"
LABEL org.opencontainers.image.documentation="https://github.com/voice-bridge/voice-bridge-pathology/blob/main/README.md"

# Security labels
LABEL security.non-root="true"
LABEL security.privileged="false"
LABEL security.capabilities="CAP_SYS_ADMIN"
LABEL medical.hipaa-ready="true"
LABEL medical.compliance="configurable"
