# --- STAGE 1: Builder ---
# We use a specific SHA to ensure the build is deterministic and reproducible.
FROM python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db AS builder

# Install uv (extremely fast Python package manager) by copying the binary from the official image
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /bin/uv

# UV Configuration:
# 1. Compile to bytecode for faster startup
# 2. Use 'copy' mode to avoid hardlink issues in some Docker filesystems
# 3. Disable python downloads to force use of the base image's Python
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_NO_DEV=1

WORKDIR /app

# Copy only dependency definitions to leverage Docker's layer caching.
# If these files don't change, Docker skips the expensive 'uv sync' step.
COPY pyproject.toml uv.lock ./

# Install dependencies using a cache mount for the uv cache directory.
# We use a bind mount for the lockfiles to avoid creating extra layers.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy the actual application source code
COPY . /app

# Final sync to install the project itself into the virtual environment
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev


# --- STAGE 2: Runtime ---
# We use the exact same base image to ensure binary compatibility with Alpine's musl C library.
FROM python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db

# Security: Create a non-privileged user to run the application.
# Alpine uses 'addgroup' and 'adduser' syntax.
# Setup a non-root user
RUN groupadd --system --gid 1000 nonroot \
 && useradd --system --gid 1000 --uid 1000 --create-home nonroot

# Copy only the necessary files from the builder (app + .venv).
# This keeps the final image size small (~81MB vs ~351MB).
COPY --from=builder --chown=nonroot:nonroot /app /app

# Use the non-root user for all subsequent operations
USER nonroot

# Environment Setup:
# 1. Add the virtual environment's bin folder to the PATH
# 2. Ensure Python logs are sent straight to the terminal without buffering
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Expose the application port
EXPOSE 5000

# Run the application using Gunicorn.
# -w 4: 4 worker processes for concurrency
# -b 0.0.0.0: Listen on all network interfaces
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "application:app"]