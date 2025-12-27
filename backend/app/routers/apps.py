from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Application
from app.schemas import AppCreate, AppResponse, AppListResponse
from app.services import claude_service, docker_service
from app.config import settings

router = APIRouter(prefix="/api/apps", tags=["apps"])


def get_next_available_port(db: Session) -> int:
    """Find the next available port."""
    used_ports = db.query(Application.port).filter(Application.port.isnot(None)).all()
    used_ports = {p[0] for p in used_ports}
    
    for port in range(settings.port_range_start, settings.port_range_end + 1):
        if port not in used_ports:
            return port
    
    raise HTTPException(status_code=503, detail="No available ports")


@router.get("", response_model=list[AppListResponse])
def list_apps(db: Session = Depends(get_db)):
    """List all applications."""
    return db.query(Application).order_by(Application.created_at.desc()).all()


@router.get("/{app_id}", response_model=AppResponse)
def get_app(app_id: UUID, db: Session = Depends(get_db)):
    """Get application details."""
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.post("", response_model=AppResponse)
def create_app(data: AppCreate, db: Session = Depends(get_db)):
    """Create a new application."""
    app = Application(
        name=data.name,
        description=data.description,
        status="created"
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


@router.delete("/{app_id}")
def delete_app(app_id: UUID, db: Session = Depends(get_db)):
    """Delete an application."""
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Cleanup Docker resources
    docker_service.cleanup_app(str(app_id), app.container_id)
    
    db.delete(app)
    db.commit()
    return {"status": "deleted"}


@router.post("/{app_id}/generate", response_model=AppResponse)
async def generate_app(app_id: UUID, db: Session = Depends(get_db)):
    """Generate Wasp code for the application using Claude."""
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if app.status not in ["created", "error"]:
        raise HTTPException(status_code=400, detail="App already generated")
    
    app.status = "generating"
    db.commit()
    
    try:
        # Generate code with Claude
        result = await claude_service.generate_wasp_app(app.name, app.description)
        
        app.wasp_schema = result["main_wasp"]
        app.prisma_schema = result["schema_prisma"]
        app.source_files = result["src_files"]
        app.port = get_next_available_port(db)
        
        # Create files on disk
        docker_service.create_app_files(
            str(app_id),
            app.wasp_schema,
            app.prisma_schema,
            app.source_files
        )
        
        app.status = "ready"
        app.error_message = None
        
    except Exception as e:
        app.status = "error"
        app.error_message = str(e)
    
    db.commit()
    db.refresh(app)
    return app


@router.post("/{app_id}/start", response_model=AppResponse)
def start_app(app_id: UUID, db: Session = Depends(get_db)):
    """Start the application container."""
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if app.status not in ["ready", "stopped"]:
        raise HTTPException(status_code=400, detail=f"Cannot start app in {app.status} status")
    
    try:
        # Build if not built yet
        docker_service.build_container(str(app_id))
        
        # Start container
        container_id = docker_service.start_container(str(app_id), app.port)
        app.container_id = container_id
        app.status = "running"
        app.error_message = None
        
    except Exception as e:
        app.status = "error"
        app.error_message = str(e)
    
    db.commit()
    db.refresh(app)
    return app


@router.post("/{app_id}/stop", response_model=AppResponse)
def stop_app(app_id: UUID, db: Session = Depends(get_db)):
    """Stop the application container."""
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if app.status != "running":
        raise HTTPException(status_code=400, detail="App is not running")
    
    try:
        docker_service.stop_container(app.container_id)
        app.status = "stopped"
        
    except Exception as e:
        app.status = "error"
        app.error_message = str(e)
    
    db.commit()
    db.refresh(app)
    return app


@router.get("/{app_id}/logs")
def get_logs(app_id: UUID, db: Session = Depends(get_db)):
    """Get application container logs."""
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if not app.container_id:
        return {"logs": "No container running"}
    
    logs = docker_service.get_container_logs(app.container_id)
    return {"logs": logs}

