FROM python:3.11-slim

RUN useradd --create-home --uid 1000 judge

# Нужен до put_archive(..., "/work") до start(): пустой tmpfs в create ещё не даёт путь.
RUN mkdir -p /work && chown judge:judge /work

WORKDIR /judge
COPY judge.py .
RUN chown judge:judge /judge/judge.py

USER judge
ENTRYPOINT ["python", "/judge/judge.py"]
