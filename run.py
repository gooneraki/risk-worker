#!/usr/bin/env python3
"""
Simple run script for Risk Worker
Usage: 
  python run.py                 # Ask local vs docker, then run
  python run.py --local         # Force local mode
  python run.py --docker        # Force docker mode
"""
import subprocess
import sys
import os
import time
import socket
from dotenv import load_dotenv


def check_service(host, port, timeout=1):
    """Check if a service is running on host:port"""
    try:
        with socket.create_connection((host, port), timeout):
            return True
    except (socket.error, socket.timeout):
        return False


def check_docker_env():
    """Check if .env.production exists for docker mode"""
    if os.path.exists('.env.production'):
        return True
    else:
        print("❌ .env.production file not found")
        print("📖 Please see environment.example for configuration template")
        return False


def start_docker_services():
    """Start all services via Docker Compose"""
    print("🐳 Starting all docker services...")
    try:
        subprocess.run(['docker-compose', 'up', '--build', '-d'], check=True)

        # Wait for services
        print("⏳ Waiting for services...")
        for _ in range(30):
            if check_service('localhost', 5432) and \
                check_service('localhost', 6379) and \
                    check_service('localhost', 8000):
                print("✅ All services ready!")
                return True
            time.sleep(1)

        print("⚠️ Services started but may not be ready yet")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to start docker services")
        return False


def run_app():
    """Run the uvicorn server locally"""
    # Load .env.local if it exists, otherwise exit
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
    """Main function"""
    # Check for flags
    force_local = '--local' in sys.argv
    force_docker = '--docker' in sys.argv

    # Determine mode
    if force_local:
        mode = 'local'
    elif force_docker:
        mode = 'docker'
    else:
        # Simple binary question
        print("🚀 Risk Worker")
        print("Run locally (SQLite) or with Docker (PostgreSQL)?")
        choice = input("Enter 'local' or 'docker': ").strip().lower()

        if choice in ['local', 'l']:
            mode = 'local'
        elif choice in ['docker', 'd']:
            mode = 'docker'
        else:
            print("Invalid choice. Defaulting to local mode.")
            mode = 'local'

    # Execute based on mode
    if mode == 'local':
        print("📍 Local mode selected")
        run_app()
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

        # Follow logs from all services
        try:
            subprocess.run(['docker-compose', 'logs', '-f'], check=True)
        except KeyboardInterrupt:
            print("\n🛑 Stopping all services...")
            subprocess.run(['docker-compose', 'down'], check=True)
            print("👋 All services stopped!")


if __name__ == "__main__":
    main()
