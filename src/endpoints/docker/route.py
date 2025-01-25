from fastapi import APIRouter, HTTPException
import subprocess
from typing import Dict
import docker

docker_router = APIRouter()

def is_docker_installed() -> bool:
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def install_docker() -> Dict:
    try:
        subprocess.run("sudo apt-get update", shell=True, check=True)
        subprocess.run("sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common", shell=True, check=True)
        
        subprocess.run("curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -", shell=True, check=True)
        
        subprocess.run('sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"', shell=True, check=True)
        
        subprocess.run("sudo apt-get update", shell=True, check=True)
        subprocess.run("sudo apt-get install -y docker-ce docker-ce-cli containerd.io", shell=True, check=True)
        
        subprocess.run("sudo systemctl start docker", shell=True, check=True)
        subprocess.run("sudo systemctl enable docker", shell=True, check=True)
        
        return {"status": "success", "message": "Docker Engine installed successfully"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to install Docker: {str(e)}"
        )

@docker_router.post("/docker/install")
def install_docker_route() -> Dict:
    if is_docker_installed():
        return {"status": "already_installed", "message": "Docker Engine is already installed"}
    return install_docker()

@docker_router.get("/docker")
def docker_status() -> Dict:
    if not is_docker_installed():
        return {
            "status": "not_installed",
            "message": "Docker Engine is not installed. Use POST /docker/install to install Docker."
        }
    
    try:
        client = docker.from_env()
        info = client.info()
        return {
            "status": "running",
            "version": info.get("ServerVersion"),
            "containers": {
                "total": info.get("Containers", 0),
                "running": info.get("ContainersRunning", 0),
                "stopped": info.get("ContainersStopped", 0)
            },
            "images": info.get("Images", 0)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Docker service error: {str(e)}"
        }
