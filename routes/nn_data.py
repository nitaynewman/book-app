from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import json
import os
import shutil
from pathlib import Path

router = APIRouter(
    prefix='/data',
    tags=['data']
)

# Configure paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VIDEO_DIR = BASE_DIR / "static" / "videos"

# JSON file paths
PYTHON_JSON = DATA_DIR / "python.json"
REACT_JSON = DATA_DIR / "react.json"
JS_JSON = DATA_DIR / "js.json"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

# Pydantic models for request validation
class ProjectItem(BaseModel):
    id: int
    title: str
    git_url: str
    video: str
    url: Optional[str] = ""
    paragraph: str

# Helper functions to read JSON files
def read_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file_path.name}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Invalid JSON file: {file_path.name}")

def write_json_file(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing to file: {str(e)}")

# GET endpoint - Retrieve all Python projects
@router.get("/python")
async def get_python_projects():
    """
    Retrieve all Python projects
    """
    try:
        projects = read_json_file(PYTHON_JSON)
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET endpoint - Retrieve Python projects by category
@router.get("/python/{category}")
async def get_python_category(category: str):
    """
    Retrieve Python projects by category (AI, API, Flask, etc.)
    """
    projects = read_json_file(PYTHON_JSON)
    
    if category not in projects:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
    
    return {category: projects[category]}

# GET endpoint - Retrieve all React projects
@router.get("/react")
async def get_react_projects():
    """
    Retrieve all React projects
    """
    try:
        projects = read_json_file(REACT_JSON)
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET endpoint - Retrieve React projects (React_Apps)
@router.get("/react/React_Apps")
async def get_react_apps():
    """
    Retrieve React Apps
    """
    projects = read_json_file(REACT_JSON)
    return projects

# GET endpoint - Retrieve all JS projects
@router.get("/js")
async def get_js_projects():
    """
    Retrieve all JavaScript projects
    """
    try:
        projects = read_json_file(JS_JSON)
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET endpoint - Retrieve JS projects (Js_App)
@router.get("/js/Js_App")
async def get_js_apps():
    """
    Retrieve JS Apps
    """
    projects = read_json_file(JS_JSON)
    return projects

# GET endpoint - Debug video directory
@router.get("/debug/videos")
async def debug_videos():
    """
    Debug endpoint to check video directory structure
    """
    import os
    
    debug_info = {
        "base_dir": str(BASE_DIR),
        "video_dir": str(VIDEO_DIR),
        "video_dir_exists": VIDEO_DIR.exists(),
        "files": []
    }
    
    if VIDEO_DIR.exists():
        for root, dirs, files in os.walk(VIDEO_DIR):
            for file in files:
                if file.endswith('.mp4'):
                    full_path = Path(root) / file
                    relative_path = full_path.relative_to(VIDEO_DIR)
                    debug_info["files"].append(str(relative_path))
    
    return debug_info

# GET endpoint - Serve video files
@router.get("/videos/{video_path:path}")
async def get_video(video_path: str):
    """
    Serve video files from the video directory with proper range support
    Example: /data/videos/game/pong.mp4
    """
    from fastapi import Request
    from fastapi.responses import StreamingResponse
    import os
    
    video_path = video_path.lstrip('/')
    file_path = VIDEO_DIR / video_path
    
    # Detailed error logging
    if not file_path.exists():
        parent_dir = file_path.parent
        available_files = []
        if parent_dir.exists():
            available_files = [f.name for f in parent_dir.iterdir() if f.is_file()]
        
        raise HTTPException(
            status_code=404, 
            detail={
                "error": "Video not found",
                "requested_path": video_path,
                "full_path": str(file_path),
                "parent_dir_exists": parent_dir.exists(),
                "available_files": available_files[:10]
            }
        )
    
    # For video streaming, use FileResponse which handles range requests
    return FileResponse(
        file_path,
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600"
        }
    )

# POST endpoint - Add new Python project
@router.post("/python/{category}")
async def add_python_project(
    category: str,
    project_id: int = Form(...),
    title: str = Form(...),
    git_url: str = Form(...),
    paragraph: str = Form(...),
    url: Optional[str] = Form(""),
    video: Optional[UploadFile] = File(None)
):
    """
    Add a new Python project to a specific category
    """
    projects = read_json_file(PYTHON_JSON)
    
    if category not in projects:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    
    # Check if project ID already exists
    existing_ids = [p.get('id') for p in projects[category]]
    if project_id in existing_ids:
        raise HTTPException(status_code=400, detail=f"Project with ID {project_id} already exists")
    
    video_path = ""
    if video:
        # Save video file
        video_filename = f"python_{category.lower().replace(' ', '_')}_{project_id}_{video.filename}"
        video_file_path = VIDEO_DIR / video_filename
        
        try:
            with open(video_file_path, "wb") as buffer:
                shutil.copyfileobj(video.file, buffer)
            video_path = f"videos/{video_filename}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving video: {str(e)}")
    
    # Create project data
    new_project = {
        "id": project_id,
        "title": title,
        "git_url": git_url,
        "video": video_path,
        "url": url,
        "paragraph": paragraph
    }
    
    projects[category].append(new_project)
    write_json_file(PYTHON_JSON, projects)
    
    return {
        "message": "Python project added successfully",
        "project": new_project
    }

# POST endpoint - Add new React project
@router.post("/react")
async def add_react_project(
    project_id: int = Form(...),
    title: str = Form(...),
    git_url: str = Form(...),
    paragraph: str = Form(...),
    url: Optional[str] = Form(""),
    video: Optional[UploadFile] = File(None)
):
    """
    Add a new React project
    """
    projects = read_json_file(REACT_JSON)
    
    # Check if project ID already exists
    existing_ids = [p.get('id') for p in projects['React_Apps']]
    if project_id in existing_ids:
        raise HTTPException(status_code=400, detail=f"Project with ID {project_id} already exists")
    
    video_path = ""
    if video:
        video_filename = f"react_{project_id}_{video.filename}"
        video_file_path = VIDEO_DIR / video_filename
        
        try:
            with open(video_file_path, "wb") as buffer:
                shutil.copyfileobj(video.file, buffer)
            video_path = f"videos/{video_filename}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving video: {str(e)}")
    
    new_project = {
        "id": project_id,
        "title": title,
        "git_url": git_url,
        "video": video_path,
        "url": url,
        "paragraph": paragraph
    }
    
    projects['React_Apps'].append(new_project)
    write_json_file(REACT_JSON, projects)
    
    return {
        "message": "React project added successfully",
        "project": new_project
    }

# POST endpoint - Add new JS project
@router.post("/js")
async def add_js_project(
    project_id: int = Form(...),
    title: str = Form(...),
    git_url: str = Form(...),
    paragraph: str = Form(...),
    url: Optional[str] = Form(""),
    video: Optional[UploadFile] = File(None)
):
    """
    Add a new JavaScript project
    """
    projects = read_json_file(JS_JSON)
    
    # Check if project ID already exists
    existing_ids = [p.get('id') for p in projects['Js_App']]
    if project_id in existing_ids:
        raise HTTPException(status_code=400, detail=f"Project with ID {project_id} already exists")
    
    video_path = ""
    if video:
        video_filename = f"js_{project_id}_{video.filename}"
        video_file_path = VIDEO_DIR / video_filename
        
        try:
            with open(video_file_path, "wb") as buffer:
                shutil.copyfileobj(video.file, buffer)
            video_path = f"videos/{video_filename}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving video: {str(e)}")
    
    new_project = {
        "id": project_id,
        "title": title,
        "git_url": git_url,
        "video": video_path,
        "url": url,
        "paragraph": paragraph
    }
    
    projects['Js_App'].append(new_project)
    write_json_file(JS_JSON, projects)
    
    return {
        "message": "JS project added successfully",
        "project": new_project
    }

# DELETE endpoints for each project type
@router.delete("/python/{category}/{project_id}")
async def delete_python_project(category: str, project_id: int):
    """
    Delete a Python project and its associated video
    """
    projects = read_json_file(PYTHON_JSON)
    
    if category not in projects:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
    
    project = None
    for idx, p in enumerate(projects[category]):
        if p.get('id') == project_id:
            project = projects[category].pop(idx)
            break
    
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    
    # Delete video file if exists
    if project.get('video'):
        video_path = VIDEO_DIR / project['video'].replace('videos/', '')
        if video_path.exists():
            video_path.unlink()
    
    write_json_file(PYTHON_JSON, projects)
    
    return {
        "message": "Python project deleted successfully",
        "project": project
    }

@router.delete("/react/{project_id}")
async def delete_react_project(project_id: int):
    """
    Delete a React project and its associated video
    """
    projects = read_json_file(REACT_JSON)
    
    project = None
    for idx, p in enumerate(projects['React_Apps']):
        if p.get('id') == project_id:
            project = projects['React_Apps'].pop(idx)
            break
    
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    
    if project.get('video'):
        video_path = VIDEO_DIR / project['video'].replace('videos/', '')
        if video_path.exists():
            video_path.unlink()
    
    write_json_file(REACT_JSON, projects)
    
    return {
        "message": "React project deleted successfully",
        "project": project
    }

@router.delete("/js/{project_id}")
async def delete_js_project(project_id: int):
    """
    Delete a JS project and its associated video
    """
    projects = read_json_file(JS_JSON)
    
    project = None
    for idx, p in enumerate(projects['Js_App']):
        if p.get('id') == project_id:
            project = projects['Js_App'].pop(idx)
            break
    
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    
    if project.get('video'):
        video_path = VIDEO_DIR / project['video'].replace('videos/', '')
        if video_path.exists():
            video_path.unlink()
    
    write_json_file(JS_JSON, projects)
    
    return {
        "message": "JS project deleted successfully",
        "project": project
    }