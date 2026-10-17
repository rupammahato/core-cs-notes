ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE} AS wheels
WORKDIR /build
COPY requirements.lock.txt .
RUN python -m pip wheel --no-cache-dir --wheel-dir /wheelhouse -r requirements.lock.txt
COPY . /context-audit
RUN python -c "from pathlib import Path; p=Path('/context-audit'); assert (p/'app.py').exists(); assert not (p/'.env').exists(); assert not (p/'secrets').exists(); Path('/build-only.txt').write_text('builder artifact')"

FROM ${PYTHON_IMAGE} AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app && chown app:app /app
COPY --from=wheels /wheelhouse /wheelhouse
COPY requirements.lock.txt .
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheelhouse -r requirements.lock.txt && rm -rf /wheelhouse
COPY --chown=app:app app.py healthcheck.py ./
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=1s --timeout=3s --start-period=5s --retries=3 CMD ["python", "healthcheck.py"]
CMD ["python", "app.py"]
