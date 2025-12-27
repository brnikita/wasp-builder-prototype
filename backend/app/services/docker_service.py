import os
import shutil
import docker
from pathlib import Path
from app.config import settings

client = docker.from_env()

WASP_DOCKERFILE = """FROM node:22-slim

# Install dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    git \\
    procps \\
    && rm -rf /var/lib/apt/lists/*

# Install Wasp
RUN curl -sSL https://get.wasp.sh/installer.sh | sh

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy project files
COPY . .

# Run migration and start Wasp
CMD ["sh", "-c", "echo '--- Wasp Version ---' && wasp version && echo '--- Directory Content ---' && ls -la && echo '--- Running Migration ---' && wasp db migrate-dev --name init 2>&1 || true && echo '--- Starting Wasp ---' && wasp start"]
"""


def get_app_path(app_id: str) -> Path:
    """Get the path for a generated app."""
    return Path(settings.generated_apps_path) / app_id


def create_app_files(app_id: str, wasp_schema: str, prisma_schema: str, source_files: dict) -> Path:
    """Create the Wasp app files on disk."""
    app_path = get_app_path(app_id)
    app_path.mkdir(parents=True, exist_ok=True)
    
    # Write .wasproot (required for Wasp to recognize the project)
    (app_path / ".wasproot").write_text("")
    
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
        # Strip leading src/ if present (LLM sometimes includes it)
        clean_path = file_path.lstrip("src/").lstrip("src\\")
        full_path = src_path / clean_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    
    # Create package.json (required by Wasp 0.20.0 with exact dependencies)
    package_json = """{
  "name": "wasp-app",
  "version": "1.0.0",
  "private": true,
  "workspaces": [".wasp/build/*", ".wasp/out/*"],
  "dependencies": {
    "wasp": "file:.wasp/out/sdk/wasp",
    "react": "^19.2.1",
    "react-dom": "^19.2.1",
    "react-router-dom": "^6.26.2"
  },
  "devDependencies": {
    "vite": "^7.0.6",
    "prisma": "5.19.1"
  }
}"""
    (app_path / "package.json").write_text(package_json)
    
    # Create public directory (Wasp watches this)
    (app_path / "public").mkdir(exist_ok=True)
    (app_path / "public" / ".gitkeep").write_text("")
    
    # Create tsconfig.json (required by Wasp 0.20.0 with exact values)
    tsconfig = """{
  "compilerOptions": {
    "target": "esnext",
    "module": "esnext",
    "moduleResolution": "bundler",
    "moduleDetection": "force",
    "isolatedModules": true,
    "jsx": "preserve",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": ".wasp/out/user",
    "composite": true
  },
  "include": ["src"]
}"""
    (app_path / "tsconfig.json").write_text(tsconfig)
    
    return app_path


def build_container(app_id: str) -> str:
    """Build Docker container for the app."""
    app_path = get_app_path(app_id)
    image_name = f"wasp-app-{app_id}"
    
    client.images.build(path=str(app_path), tag=image_name, rm=True)
    return image_name


def create_app_database(app_id: str):
    """Create a database for the app if it doesn't exist."""
    import subprocess
    db_name = f"app_{app_id.replace('-', '_')}"
    
    # Create database using psql via docker exec
    try:
        result = subprocess.run(
            ["docker", "exec", "wasp-builder-prototype-db-1", "psql", "-U", "wasp_builder", "-d", "wasp_builder", "-c", 
             f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"],
            capture_output=True, text=True, timeout=10
        )
        
        if "(0 rows)" in result.stdout:
            # Database doesn't exist, create it
            subprocess.run(
                ["docker", "exec", "wasp-builder-prototype-db-1", "psql", "-U", "wasp_builder", "-d", "wasp_builder", "-c",
                 f"CREATE DATABASE {db_name}"],
                capture_output=True, text=True, timeout=10
            )
    except Exception as e:
        print(f"Warning: Could not create database: {e}")
    
    return db_name


def start_container(app_id: str, port: int) -> str:
    """Start the app container."""
    image_name = f"wasp-app-{app_id}"
    container_name = f"wasp-container-{app_id}"
    
    # Create database for this app
    db_name = create_app_database(app_id)
    
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
        network="wasp-builder-prototype_default",
        log_config={"type": "json-file", "config": {"max-size": "10m", "max-file": "3"}},
        environment={
            "DATABASE_URL": f"postgresql://wasp_builder:wasp_builder_pass@db:5432/{db_name}",
            "SKIP_DB_STUDIO": "true"
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
    except docker.errors.APIError as e:
        if "configured logging driver does not support reading" in str(e):
            return "Logs unavailable: Docker logging driver doesn't support reading. Configure 'json-file' driver in Docker Desktop settings."
        return f"Error reading logs: {e}"


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

