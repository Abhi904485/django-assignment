# Use a lightweight Python base image
FROM python:3.12-slim

# Set environment variables to prevent pyc files and buffer stdout
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies, including ffmpeg and ffprobe
# Install curl for Poetry installation and clean up after package installation to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to the system PATH
ENV PATH="/root/.local/bin:$PATH"

# Set the working directory in the container
WORKDIR /app

# Copy only pyproject.toml and poetry.lock to leverage Docker layer caching
COPY pyproject.toml poetry.lock ./

# Install Python dependencies via Poetry (no virtualenv creation in Docker)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy the entire application code into the container
COPY . .

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod 777 /app/entrypoint.sh

# Expose the port the app runs on
EXPOSE 8000

# Run the entrypoint script
CMD ["/app/entrypoint.sh"]
