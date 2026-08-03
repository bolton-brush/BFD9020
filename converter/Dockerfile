FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libopenblas-dev \
        libblas-dev \
        liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        --extra-index-url https://download.pytorch.org/whl/cpu \
    torch \
    torchvision \
    torchaudio \
    "numpy>=1.26.0,<2.0.0" \
    "pandas<2.1.0" \
    "fastai<2.8" \
    scikit-image \
    imageio \
    safetensors \
    onnx \
    onnxruntime

# Copy the migration engine execution routine into the container shell
COPY convert_models.py .

# Trigger the conversion process over the mounted workspace directory target
CMD ["python", "convert_models.py"]
