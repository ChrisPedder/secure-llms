FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir boto3

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir .

CMD ["python", "-m", "src.run", "--data-path", "s3://placeholder/creditcard.csv"]
