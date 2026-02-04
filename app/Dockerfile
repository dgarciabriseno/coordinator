# Builder stage - has all build tools
FROM condaforge/mambaforge AS builder

WORKDIR /build
COPY requirements.txt .

# This is where pip will be after the conda environment is created
ENV PIP=/opt/conda/envs/coordinator/bin/pip

# Create conda environment and install dependencies
RUN mamba create -n coordinator -y python=3.13.5 gcc \
    && cd /tmp \
    && git clone https://github.com/sunpy/sunpy.git \
    && cd sunpy \
    && git fetch origin pull/8500/head:pr-8500 \
    && git checkout pr-8500 \
    && mamba run -n coordinator pip install --no-cache-dir . \
    && cd /build \
    && mamba run -n coordinator pip install --no-cache-dir -r requirements.txt \
    && rm -rf /tmp/sunpy

# Final stage - minimal runtime image
FROM condaforge/mambaforge

RUN apt update && apt install -y curl

# Create and switch to non-root user
RUN useradd -m -s /bin/bash nonroot
WORKDIR /home/nonroot/app

# Copy conda environment from builder (keep same path)
COPY --from=builder /opt/conda/envs/coordinator /opt/conda/envs/coordinator

# copy application files to the container
COPY --chown=nonroot:nonroot . .

USER nonroot

# This is where pip will be after the conda environment is created
# can't conda activate in dockerfile
ENV PIP=/opt/conda/envs/coordinator/bin/pip

HEALTHCHECK --interval=2s --timeout=10s \
    CMD curl --silent --fail "http://127.0.0.1/health-check"

ENTRYPOINT ["/opt/conda/envs/coordinator/bin/python"]

CMD ["-m", "fastapi", "run", "--workers", "4", "--port", "80", "main.py"]
