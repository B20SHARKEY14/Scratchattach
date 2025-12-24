FROM python:3.12-slim

WORKDIR /app

# Install minimal build deps for some wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md requirements.txt .

RUN python3 -m pip install --upgrade pip setuptools wheel
# Install runtime deps (from requirements.txt)
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Install the package
RUN python3 -m pip install --no-cache-dir .

ENTRYPOINT ["scratchattach"]
