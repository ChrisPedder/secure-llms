FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir .

CMD ["python", "-m", "src.run", "--rounds", "5", "--clients", "3"]
