from fastapi import APIRouter, HTTPException
import subprocess
from typing import Dict
import docker
import requests

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
            # Check if Docker is already installed but not running
            if is_docker_installed():
                try:
                    # Try to start Docker service
                    subprocess.run("sudo systemctl start docker", shell=True, check=True)
                    subprocess.run("sudo systemctl enable docker", shell=True, check=True)
                    
                    # Configure Docker daemon
                    docker_daemon_config = {
                        "hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2375"],
                        "log-driver": "json-file",
                        "log-opts": {
                            "max-size": "10m",
                            "max-file": "3"
                        }
                    }
                    
                    # Create daemon.json
                    subprocess.run("sudo mkdir -p /etc/docker", shell=True, check=True)
                    import json
                    with open("/tmp/daemon.json", "w") as f:
                        json.dump(docker_daemon_config, f, indent=4)
                    subprocess.run("sudo mv /tmp/daemon.json /etc/docker/daemon.json", shell=True, check=True)
                    
                    # Create systemd override directory
                    subprocess.run("sudo mkdir -p /etc/systemd/system/docker.service.d", shell=True, check=True)
                    
                    # Create override file
                    override_content = """[Service]
ExecStart=
ExecStart=/usr/bin/dockerd
"""
                    with open("/tmp/override.conf", "w") as f:
                        f.write(override_content)
                    subprocess.run("sudo mv /tmp/override.conf /etc/systemd/system/docker.service.d/override.conf", shell=True, check=True)
                    
                    # Reload systemd and restart Docker
                    subprocess.run("sudo systemctl daemon-reload", shell=True, check=True)
                    subprocess.run("sudo systemctl restart docker", shell=True, check=True)
                    
                    # Verify Docker is running
                    subprocess.run("sudo docker info", shell=True, check=True)
                    
                    return {
                        "status": "reconfigured",
                        "message": "Docker service has been reconfigured and restarted"
                    }
                except subprocess.CalledProcessError as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to configure Docker: {str(e)}"
                    )
            
            # If Docker is not installed, proceed with installation
            subprocess.run("sudo apt-get remove docker docker-engine docker.io containerd runc", shell=True, check=False)
            subprocess.run("sudo apt-get update", shell=True, check=True)
            subprocess.run("sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release", shell=True, check=True)
            
            # Add Docker's official GPG key
            subprocess.run("curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg", shell=True, check=True)
            
            # Set up the repository
            subprocess.run(
                'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null',
                shell=True,
                check=True
            )
            
            # Install Docker Engine
            subprocess.run("sudo apt-get update", shell=True, check=True)
            subprocess.run("sudo apt-get install -y docker-ce docker-ce-cli containerd.io", shell=True, check=True)
            
            # Configure Docker daemon
            docker_daemon_config = {
                "hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2375"],
                "log-driver": "json-file",
                "log-opts": {
                    "max-size": "10m",
                    "max-file": "3"
                }
            }
            
            # Create daemon.json
            subprocess.run("sudo mkdir -p /etc/docker", shell=True, check=True)
            import json
            with open("/tmp/daemon.json", "w") as f:
                json.dump(docker_daemon_config, f, indent=4)
            subprocess.run("sudo mv /tmp/daemon.json /etc/docker/daemon.json", shell=True, check=True)
            
            # Create systemd override directory
            subprocess.run("sudo mkdir -p /etc/systemd/system/docker.service.d", shell=True, check=True)
            
            # Create override file
            override_content = """[Service]
ExecStart=
ExecStart=/usr/bin/dockerd
"""
            with open("/tmp/override.conf", "w") as f:
                f.write(override_content)
            subprocess.run("sudo mv /tmp/override.conf /etc/systemd/system/docker.service.d/override.conf", shell=True, check=True)
            
            # Start and enable Docker
            subprocess.run("sudo systemctl daemon-reload", shell=True, check=True)
            subprocess.run("sudo systemctl start docker", shell=True, check=True)
            subprocess.run("sudo systemctl enable docker", shell=True, check=True)
            
            # Verify Docker is running
            subprocess.run("sudo docker info", shell=True, check=True)
            
            return {
                "status": "success",
                "message": "Docker Engine installed successfully and configured for remote access"
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
        # Try different connection methods without using sudo
        connection_errors = []
        
        # Try environment-based connection first
        try:
            client = docker.from_env()
            client.ping()
        except Exception as e:
            connection_errors.append(f"Environment connection failed: {str(e)}")
            
            # Try direct socket connection
            try:
                client = docker.DockerClient(base_url='unix://var/run/docker.sock')
                client.ping()
            except Exception as e:
                connection_errors.append(f"Socket connection failed: {str(e)}")
                
                # Try TCP connection to host
                try:
                    client = docker.DockerClient(base_url='tcp://host.docker.internal:2375')
                    client.ping()
                except Exception as e:
                    connection_errors.append(f"TCP connection failed: {str(e)}")
                    
                    # Try localhost TCP connection
                    try:
                        client = docker.DockerClient(base_url='tcp://172.17.0.1:2375')
                        client.ping()
                    except Exception as e:
                        connection_errors.append(f"Localhost TCP connection failed: {str(e)}")
                        return {
                            "status": "error",
                            "message": "Failed to connect to Docker daemon. Tried multiple methods:\n" + "\n".join(connection_errors)
                        }
        
        # If we get here, one of the connection methods worked
        info = client.info()
        
        # Get list of containers
        containers = client.containers.list(all=True)
        running_containers = [c for c in containers if c.status == 'running']
        
        return {
            "status": "running",
            "version": info.get("ServerVersion"),
            "containers": {
                "total": len(containers),
                "running": len(running_containers),
                "stopped": len(containers) - len(running_containers)
            },
            "images": len(client.images.list()),
            "api_version": client.api.version()["ApiVersion"],
            "os": info.get("OperatingSystem"),
            "kernel_version": info.get("KernelVersion"),
            "cpu_count": info.get("NCPU"),
            "total_memory": info.get("MemTotal"),
            "docker_root_dir": info.get("DockerRootDir")
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Docker service error: {str(e)}. Please ensure Docker service is running and properly configured."
        }
