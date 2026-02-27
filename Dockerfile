FROM python:3.12.10-alpine3.22@sha256:4bbf5ef9ce4b273299d394de268ad6018e10a9375d7efc7c2ce9501a6eb6b86c AS builder

# Install uv directly from its official image
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

    # Omit development dependencies
ENV UV_NO_DEV=1

# Set the working directory inside the container
WORKDIR /app
    
# Copy dependency files first.
# This allows Docker to cache the installed packages layer.
# If you change your code but not your dependencies, this step will be skipped.
COPY pyproject.toml uv.lock ./


RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Install dependencies into the system python environment.
RUN uv sync --frozen --no-dev

# Copy the rest of the application code
COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked


# It is important to use the image that matches the builder, as the path to the
# Python executable must be the same, e.g., using `python:3.13-slim-bookworm`
# will fail.
FROM python:3.12.10-alpine3.22@sha256:4bbf5ef9ce4b273299d394de268ad6018e10a9375d7efc7c2ce9501a6eb6b86c


# Setup a non-root user
RUN addgroup -S -g 1000 nonroot && \
    adduser -S -u 1000 -G nonroot nonroot

# Copy the application from the builder
COPY --from=builder --chown=nonroot:nonroot /app /app

# Use the non-root user to run our application
USER nonroot

# This makes 'gunicorn' and 'flask' available globally in the container
ENV PATH="/app/.venv/bin:$PATH"

# Use `/app` as the working directory
WORKDIR /app

# Expose the port the app runs on
EXPOSE 5000

# Run the production server
# -w 4: Run 4 worker processes
# -b 0.0.0.0:5000: Listen on all interfaces on port 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "application:app"]