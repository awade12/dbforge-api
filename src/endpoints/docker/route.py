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
    import platform
    system = platform.system().lower()
    
    if system == "darwin":
        try:
            # Check if Homebrew is installed
            subprocess.run(["brew", "--version"], capture_output=True, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            raise HTTPException(
                status_code=500,
                detail="Homebrew is required to install Docker on macOS. Please install it first: https://brew.sh"
            )
            
        try:
            # Install Docker Desktop for Mac using Homebrew
            subprocess.run("brew install --cask docker", shell=True, check=True)
            
            return {
                "status": "success", 
                "message": "Docker Desktop has been installed. Please launch Docker Desktop from your Applications folder."
            }
        except subprocess.CalledProcessError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to install Docker: {str(e)}"
            )
    elif system == "linux":
        try:
            # Remove any old versions
            subprocess.run("sudo apt-get remove docker docker-engine docker.io containerd runc", shell=True, check=False)
            
            # Update package index and install dependencies
            subprocess.run("sudo apt-get update", shell=True, check=True)
            subprocess.run("sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release", shell=True, check=True)
            
            subprocess.run("curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg", shell=True, check=True)
            
            subprocess.run(
                'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null',
                shell=True,
                check=True
            )
            
            subprocess.run("sudo apt-get update", shell=True, check=True)
            subprocess.run("sudo apt-get install -y docker-ce docker-ce-cli containerd.io", shell=True, check=True)
            
            # Start and enable Docker service
            subprocess.run("sudo systemctl start docker", shell=True, check=True)
            subprocess.run("sudo systemctl enable docker", shell=True, check=True)
            
            # Configure Docker to listen on TCP port
            docker_daemon_config = {
                "hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2375"]
            }
            
            # Create daemon.json if it doesn't exist
            subprocess.run("sudo mkdir -p /etc/docker", shell=True, check=True)
            import json
            with open("/tmp/daemon.json", "w") as f:
                json.dump(docker_daemon_config, f, indent=4)
            subprocess.run("sudo mv /tmp/daemon.json /etc/docker/daemon.json", shell=True, check=True)
            
            # Restart Docker service to apply changes
            subprocess.run("sudo systemctl restart docker", shell=True, check=True)
            
            return {
                "status": "success",
                "message": "Docker Engine installed successfully and configured for remote access on port 2375"
            }
        except subprocess.CalledProcessError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to install Docker: {str(e)}"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported operating system: {system}"
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
        # Try different connection methods
        try:
            # Try local socket first
            client = docker.from_env()
            info = client.info()
        except docker.errors.DockerException:
            try:
                # Try TCP connection
                client = docker.DockerClient(base_url='tcp://localhost:2375')
                info = client.info()
            except docker.errors.DockerException:
                # Try Unix socket explicitly
                client = docker.DockerClient(base_url='unix://var/run/docker.sock')
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
            "message": f"Docker service error: {str(e)}. Please ensure Docker service is running and properly configured."
        }
