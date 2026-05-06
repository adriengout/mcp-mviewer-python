FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

RUN useradd -m -u 1000 mcp

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=mcp:mcp . .

USER mcp

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import socket; s=socket.socket(); s.settimeout(4); s.connect(('localhost', 8000)); s.close()"

CMD ["python", "main.py"]