FROM astral/uv:python3.13-bookworm-slim

WORKDIR /app

# Copy from the context
COPY pyproject.toml uv.lock ./

# Install the project's dependencies
RUN uv sync --frozen --no-dev

COPY src ./src

# Expose port and run
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
