# WikiRace has no dependencies beyond the Python standard library, so this is
# about as small and as boring as an image gets - no build step, no wheels,
# nothing to keep patched but the base itself.
FROM python:3.12-slim

# Unbuffered, or the logs only appear when the buffer fills - which on a quiet
# game could be hours, and makes `docker logs` look broken.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    WIKIRACE_HOST=1 \
    WIKIRACE_NO_BROWSER=1 \
    WIKIRACE_NO_DISCOVERY=1 \
    WIKIRACE_DATA=/data \
    WIKIRACE_PORT=8420

WORKDIR /app
COPY wikirace.py ui.html ./

# The standings live here; mount a volume over it or they go when the
# container does.
RUN mkdir -p /data && chown -R 1000:1000 /data /app
VOLUME ["/data"]

# Not root. TrueNAS lets you pick the user; 1000 is a sane default that
# matches the usual first user on a NAS dataset.
USER 1000:1000

EXPOSE 8420

# Asks the one endpoint that answers without the join code.
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,os,sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('WIKIRACE_PORT','8420')+'/healthz', timeout=4).status==200 else 1)"

# exec form, so the process is PID 1 and gets the SIGTERM docker sends it -
# which is what makes the standings survive a restart.
ENTRYPOINT ["python", "wikirace.py"]
