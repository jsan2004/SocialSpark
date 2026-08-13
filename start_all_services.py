#!/usr/bin/env python3
import subprocess
import time
import sys
import os

def start_service(service_name, port, script_path):
    """Start a microservice"""
    print(f"Starting {service_name} on port {port}...")
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    
    process = subprocess.Popen(
        [sys.executable, os.path.basename(script_path)],
        cwd=os.path.dirname(script_path),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    return process

def main():
    print("Starting Social Network Microservices...")
    
    services = [
        ("User Service", 5001, "user_service/app.py"),
        ("Post Service", 5002, "post_service/app.py"),
        ("Follow Service", 5003, "friend_service/app.py"),
        ("API Gateway", 5004, "api_gateway/app.py"),
        ("Notification Service", 5005, "notification_service/app.py"),
        ("Frontend Service", 5000, "frontend/app.py")
    ]
    
    processes = []
    
    try:
        # Start all services
        for service_name, port, script_path in services:
            process = start_service(service_name, port, script_path)
            processes.append((service_name, port, process))
            time.sleep(2)  # Give each service time to start
        
        print("\nAll services started successfully!")
        print("Frontend available at: http://localhost:5000")
        print("API Gateway available at: http://localhost:5004")
        
        # Monitor all processes
        while True:
            for service_name, port, process in processes:
                if process.poll() is not None:
                    print(f"\n{service_name} (port {port}) has stopped!")
                    # Read any remaining output
                    output, _ = process.communicate()
                    if output:
                        print(f"{service_name} output:\n{output}")
                    sys.exit(1)
            
            # Print output from all services
            for service_name, port, process in processes:
                try:
                    line = process.stdout.readline()
                    if line:
                        print(f"[{service_name}:{port}] {line.strip()}")
                except:
                    pass
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nShutting down all services...")
        for service_name, port, process in processes:
            process.terminate()
        print("All services stopped.")

if __name__ == "__main__":
    main()