#!/usr/bin/env python3
"""
Risk Worker launcher
Usage: 
  python run.py                 # Interactive mode
  python run.py --local         # Force local (SQLite + FakeRedis)
  python run.py --docker        # Force docker (PostgreSQL + Redis)
"""
import subprocess
import sys
import os
import time
import socket
from dotenv import load_dotenv


def check_service(host, port, timeout=1):
    """Check if service is running on host:port"""
    try:
        with socket.create_connection((host, port), timeout):
            return True
    except (socket.error, socket.timeout):
        return False


def check_docker_env():
    """Verify .env.production exists for docker mode"""
    if os.path.exists('.env.production'):
        return True
    else:
        print("❌ .env.production file not found")
        print("📖 Please see environment.example for configuration template")
        return False


def start_docker_services():
    """Start Docker Compose services"""
    print("🐳 Starting docker services...")
    try:
        subprocess.run(['docker-compose', 'up', '--build', '-d'], check=True)

        # Wait for services to be ready
        print("⏳ Waiting for services...")
        for _ in range(30):
            if (check_service('localhost', 5432) and
                check_service('localhost', 6379) and
                    check_service('localhost', 8000)):
                print("✅ All services ready!")
                return True
            time.sleep(1)

        print("⚠️ Services started but may not be ready yet")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to start docker services")
        return False


def run_local():
    """Run application locally with SQLite"""
    if os.path.exists('.env.local'):
        load_dotenv('.env.local')
    else:
        print("❌ .env.local not found. Please create it for local development.")
        sys.exit(1)

    api_host = os.getenv('API_HOST', '127.0.0.1')
    api_port = os.getenv('API_PORT', '8000')

    print(f"🚀 Starting server on {api_host}:{api_port}")

    # Ensure directories exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", api_host,
            "--port", api_port,
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")


def main():
    """Main entry point"""
    force_local = '--local' in sys.argv
    force_docker = '--docker' in sys.argv

    if force_local:
        mode = 'local'
    elif force_docker:
        mode = 'docker'
    else:
        print("🚀 Risk Worker")
        print("Run locally (SQLite) or with Docker (PostgreSQL)?")
        choice = input("Enter 'local' or 'docker': ").strip().lower()
        mode = 'local' if choice in ['local', 'l'] else 'docker'

    if mode == 'local':
        print("📍 Local mode selected")
        run_local()
    else:
        print("📍 Docker mode selected")
        if not check_docker_env():
            sys.exit(1)
        if not start_docker_services():
            print("❌ Failed to start services. Try local mode instead.")
            sys.exit(1)

        print("✅ All services running in Docker!")
        print("🌐 Access: http://localhost:8000")
        print("📋 Showing live logs (Press Ctrl+C to stop all services)...")
        print()

        try:
            subprocess.run(['docker-compose', 'logs', '-f'], check=True)
        except KeyboardInterrupt:
            print("\n🛑 Stopping all services...")
            subprocess.run(['docker-compose', 'down'], check=True)
            print("👋 All services stopped!")


if __name__ == "__main__":
    main()
