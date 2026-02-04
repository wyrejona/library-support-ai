#!/usr/bin/env python3
"""
Quick script to kill processes using ports 8000-8001 and restart UVicorn
"""

import os
import sys
import subprocess
import time
import psutil
import socket

def kill_port_processes():
    """Kill processes using ports 8000 and 8001"""
    print("🔍 Checking for processes using ports 8000-8001...")
    
    ports = [8000, 8001]
    killed = []
    
    for port in ports:
        try:
            # Try to connect to check if port is in use
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result == 0:  # Port is in use
                print(f"⚠️  Port {port} is in use. Finding and killing process...")
                
                # Find process using the port
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        for conn in proc.connections(kind='inet'):
                            if conn.laddr.port == port:
                                print(f"   Found: PID={proc.info['pid']}, Name={proc.info['name']}")
                                proc.terminate()
                                try:
                                    proc.wait(timeout=3)
                                except:
                                    proc.kill()
                                killed.append((port, proc.info['pid']))
                                print(f"   ✅ Killed process on port {port}")
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Alternative method using lsof (Linux/macOS)
                if not killed or port not in [p for p, _ in killed]:
                    try:
                        result = subprocess.run(
                            ['lsof', '-ti', f':{port}'],
                            capture_output=True,
                            text=True
                        )
                        if result.stdout.strip():
                            pids = result.stdout.strip().split('\n')
                            for pid in pids:
                                if pid:
                                    os.kill(int(pid), 9)
                                    killed.append((port, int(pid)))
                                    print(f"   ✅ Killed PID {pid} on port {port}")
                    except:
                        pass
            else:
                print(f"✅ Port {port} is available")
                
        except Exception as e:
            print(f"❌ Error checking port {port}: {e}")
    
    # Wait a moment for ports to be freed
    if killed:
        print(f"\n⏳ Waiting for ports to be freed...")
        time.sleep(2)
    
    return killed

def check_port_free(port):
    """Check if a port is free"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result != 0  # True if port is free
    except:
        return False

def start_uvicorn():
    """Start the UVicorn server"""
    print("\n🚀 Starting UVicorn server...")
    
    # Try port 8001 first, fall back to 8000
    for port in [8001, 8000, 8002, 8003]:
        if check_port_free(port):
            print(f"   Using port {port}")
            
            # Build the command
            command = [
                "python", "-m", "uvicorn", "app.main:app",
                "--host", "0.0.0.0",
                "--port", str(port),
                "--reload"
            ]
            
            print(f"   Command: {' '.join(command)}")
            
            try:
                # Start the process
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                print(f"   ✅ Server started with PID: {process.pid}")
                print(f"   🌐 Access at: http://0.0.0.0:{port}")
                print(f"   📍 Local URL: http://localhost:{port}")
                
                # Print initial output
                print("\n📋 Server output:")
                print("=" * 50)
                
                # Read and display output for a few seconds
                for _ in range(10):
                    try:
                        line = process.stdout.readline()
                        if line:
                            print(line.strip())
                        if "Application startup complete" in line or "Uvicorn running on" in line:
                            print("\n✅ Server started successfully!")
                            break
                    except:
                        break
                    time.sleep(0.5)
                
                print("=" * 50)
                print("\n⚠️  Press Ctrl+C to stop the server")
                
                # Keep the process running
                try:
                    process.wait()
                except KeyboardInterrupt:
                    print("\n\n🛑 Stopping server...")
                    process.terminate()
                    process.wait()
                    print("✅ Server stopped")
                
                return True
                
            except Exception as e:
                print(f"❌ Failed to start server: {e}")
                return False
    
    print("❌ All ports (8000-8003) are in use!")
    return False

def main():
    """Main function"""
    print("=" * 60)
    print("🛠️  UVICORN PORT CONFLICT RESOLVER")
    print("=" * 60)
    
    # Check if psutil is installed
    try:
        import psutil
    except ImportError:
        print("❌ psutil is not installed!")
        print("💡 Install it with: pip install psutil")
        return 1
    
    # Step 1: Kill processes using ports
    killed = kill_port_processes()
    
    if killed:
        print(f"\n📊 Summary: Killed {len(killed)} process(es)")
        for port, pid in killed:
            print(f"   - Port {port}: PID {pid}")
    
    # Step 2: Start UVicorn
    print("\n" + "=" * 60)
    success = start_uvicorn()
    
    if not success:
        print("\n❌ Failed to start UVicorn server")
        print("💡 Possible solutions:")
        print("   1. Check if another service is using the ports")
        print("   2. Try: sudo netstat -tulpn | grep :800")
        print("   3. Manually kill processes: sudo kill -9 <PID>")
        print("   4. Use a different port by modifying the script")
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Script interrupted by user")
        sys.exit(130)
