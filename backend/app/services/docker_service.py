import os
import shutil
import docker
from pathlib import Path
from app.config import settings

client = docker.from_env()

WASP_DOCKERFILE = """FROM node:18-slim

# Install dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Install Wasp
RUN curl -sSL https://get.wasp.sh/installer.sh | sh

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy project files
COPY . .

# Install dependencies and start
CMD ["sh", "-c", "wasp db migrate-dev && wasp start"]
"""


def get_app_path(app_id: str) -> Path:
    """Get the path for a generated app."""
    return Path(settings.generated_apps_path) / app_id


def create_app_files(app_id: str, wasp_schema: str, prisma_schema: str, source_files: dict) -> Path:
    """Create the Wasp app files on disk."""
    app_path = get_app_path(app_id)
    app_path.mkdir(parents=True, exist_ok=True)
    
    # Write main.wasp
    (app_path / "main.wasp").write_text(wasp_schema)
    
    # Write schema.prisma
    (app_path / "schema.prisma").write_text(prisma_schema)
    
    # Write Dockerfile
    (app_path / "Dockerfile").write_text(WASP_DOCKERFILE)
    
    # Write source files
    src_path = app_path / "src"
    src_path.mkdir(exist_ok=True)
    
    for file_path, content in source_files.items():
        full_path = src_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    
    # Create package.json
    package_json = """{
  "name": "wasp-app",
  "dependencies": {}
}"""
    (app_path / "package.json").write_text(package_json)
    
    return app_path


def build_container(app_id: str) -> str:
    """Build Docker container for the app."""
    app_path = get_app_path(app_id)
    image_name = f"wasp-app-{app_id}"
    
    client.images.build(path=str(app_path), tag=image_name, rm=True)
    return image_name


def start_container(app_id: str, port: int) -> str:
    """Start the app container."""
    image_name = f"wasp-app-{app_id}"
    container_name = f"wasp-container-{app_id}"
    
    # Remove existing container if any
    try:
        old_container = client.containers.get(container_name)
        old_container.remove(force=True)
    except docker.errors.NotFound:
        pass
    
    container = client.containers.run(
        image_name,
        name=container_name,
        ports={"3000/tcp": port},
        detach=True,
        environment={
            "DATABASE_URL": f"postgresql://wasp_builder:wasp_builder_pass@host.docker.internal:5432/wasp_app_{app_id}"
        }
    )
    
    return container.id


def stop_container(container_id: str):
    """Stop the app container."""
    try:
        container = client.containers.get(container_id)
        container.stop(timeout=10)
    except docker.errors.NotFound:
        pass


def remove_container(container_id: str):
    """Remove the app container."""
    try:
        container = client.containers.get(container_id)
        container.remove(force=True)
    except docker.errors.NotFound:
        pass


def get_container_logs(container_id: str, tail: int = 100) -> str:
    """Get container logs."""
    try:
        container = client.containers.get(container_id)
        return container.logs(tail=tail).decode("utf-8")
    except docker.errors.NotFound:
        return "Container not found"


def cleanup_app(app_id: str, container_id: str | None):
    """Remove container and files for an app."""
    if container_id:
        remove_container(container_id)
    
    # Remove image
    try:
        client.images.remove(f"wasp-app-{app_id}", force=True)
    except docker.errors.ImageNotFound:
        pass
    
    # Remove files
    app_path = get_app_path(app_id)
    if app_path.exists():
        shutil.rmtree(app_path)

