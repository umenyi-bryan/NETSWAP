#!/usr/bin/env python3
"""
╔═╗╔╦╗╔╗ ╔═╗╔═╗╦ ╦╔═╗╔═╗
║ ║ ║ ╠╩╗╠═╣║  ╠═╣║╣ ║ ║
╚═╝ ╩ ╚═╝╩ ╩╚═╝╩ ╩╚═╝╚═╝
NETSWAP CLI Tool
Created by CHINEDU
"""

import argparse
import socket
import os
import hashlib
import json
import requests

def print_banner():
    banner = """
    ╔═══════════════════════════════════════════════╗
    ║              🚀 NETSWAP CLI 🚀                ║
    ║         Ultimate File Transfer Tool          ║
    ║              Created by CHINEDU              ║
    ╚═══════════════════════════════════════════════╝
    """
    print(banner)

class NetSwapCLI:
    def __init__(self):
        self.chunk_size = 8192
        self.timeout = 30
        self.public_ip = self.get_public_ip()
    
    def get_public_ip(self):
        try:
            response = requests.get('https://api.ipify.org', timeout=5)
            return response.text
        except:
            return "Unknown"
    
    def send_file(self, file_path, target_ip, target_port):
        if not os.path.exists(file_path):
            print("❌ File not found:", file_path)
            return False
        
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        
        print(f"📤 Sending: {file_name} ({self.format_bytes(file_size)})")
        print(f"🎯 Target: {target_ip}:{target_port}")
        print(f"🌐 Your Public IP: {self.public_ip}")
        
        try:
            checksum = self.calculate_checksum(file_path)
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect((target_ip, target_port))
                
                # Send metadata
                metadata = {
                    'action': 'file_transfer',
                    'file_name': file_name,
                    'file_size': file_size,
                    'checksum': checksum
                }
                sock.send(json.dumps(metadata).encode() + b'\n')
                
                # Wait for ready
                response = sock.recv(1024).decode().strip()
                if response != 'READY':
                    print("❌ Receiver not ready")
                    return False
                
                # Send file
                sent_bytes = 0
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(self.chunk_size)
                        if not chunk:
                            break
                        sock.send(chunk)
                        sent_bytes += len(chunk)
                        progress = (sent_bytes / file_size) * 100
                        print(f"\r📊 Progress: {progress:.1f}%", end='', flush=True)
                
                print("\n✅ File sent! Waiting for verification...")
                
                # Verify
                verification = sock.recv(1024).decode().strip()
                if verification == 'SUCCESS':
                    print("🎉 Transfer completed successfully!")
                    return True
                else:
                    print("❌ Transfer verification failed")
                    return False
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def receive_file(self, port, save_dir='.', public_mode=False):
        if public_mode:
            print(f"🌐 Public Mode: Others can connect via your public IP")
            print(f"📡 Your Public IP: {self.public_ip}")
            print(f"🎯 Share: {self.public_ip}:{port}")
            print("💡 Make sure port forwarding is enabled on your router!")
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind(('0.0.0.0', port))
                server_socket.listen(1)
                server_socket.settimeout(self.timeout)
                
                print(f"📡 Listening on port {port}...")
                print("⏳ Waiting for incoming connection...")
                
                client_socket, client_address = server_socket.accept()
                client_socket.settimeout(self.timeout)
                
                print(f"🔗 Connected: {client_address[0]}:{client_address[1]}")
                
                # Receive metadata
                metadata = b""
                while b'\n' not in metadata:
                    chunk = client_socket.recv(1024)
                    metadata += chunk
                
                metadata = json.loads(metadata.decode().strip())
                file_name = metadata['file_name']
                file_size = metadata['file_size']
                expected_checksum = metadata['checksum']
                
                save_path = os.path.join(save_dir, file_name)
                
                # Handle duplicates
                counter = 1
                original_path = save_path
                while os.path.exists(save_path):
                    name, ext = os.path.splitext(original_path)
                    save_path = f"{name}_{counter}{ext}"
                    counter += 1
                
                print(f"📥 Receiving: {file_name} ({self.format_bytes(file_size)})")
                print(f"💾 Saving as: {save_path}")
                
                # Send ready
                client_socket.send(b'READY\n')
                
                # Receive file
                received_bytes = 0
                hash_md5 = hashlib.md5()
                
                with open(save_path, 'wb') as f:
                    while received_bytes < file_size:
                        chunk = client_socket.recv(min(self.chunk_size, file_size - received_bytes))
                        if not chunk:
                            break
                        f.write(chunk)
                        hash_md5.update(chunk)
                        received_bytes += len(chunk)
                        progress = (received_bytes / file_size) * 100
                        print(f"\r📊 Progress: {progress:.1f}%", end='', flush=True)
                
                print("\n✅ File received! Verifying...")
                
                # Verify checksum
                actual_checksum = hash_md5.hexdigest()
                if actual_checksum == expected_checksum:
                    client_socket.send(b'SUCCESS\n')
                    print("🎉 File verified successfully!")
                    return True
                else:
                    client_socket.send(b'FAILED\n')
                    os.remove(save_path)
                    print("❌ File verification failed - deleted corrupted file")
                    return False
                    
        except socket.timeout:
            print("⏰ Connection timeout - no incoming connections")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def calculate_checksum(self, file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def format_bytes(self, bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description='NETSWAP CLI - File Transfer Tool by CHINEDU')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Send command
    send_parser = subparsers.add_parser('send', help='Send a file')
    send_parser.add_argument('file', help='File to send')
    send_parser.add_argument('ip', help='Target IP address')
    send_parser.add_argument('port', type=int, help='Target port')
    
    # Receive command
    receive_parser = subparsers.add_parser('receive', help='Receive files')
    receive_parser.add_argument('port', type=int, help='Port to listen on')
    receive_parser.add_argument('--dir', default='.', help='Directory to save files')
    receive_parser.add_argument('--public', action='store_true', help='Enable internet mode')
    
    # Network info command
    info_parser = subparsers.add_parser('info', help='Show network information')
    
    args = parser.parse_args()
    netswap = NetSwapCLI()
    
    if args.command == 'send':
        netswap.send_file(args.file, args.ip, args.port)
    elif args.command == 'receive':
        netswap.receive_file(args.port, args.dir, args.public)
    elif args.command == 'info':
        print(f"🌐 Public IP: {netswap.public_ip}")
        print("💡 For internet transfers:")
        print("  1. Use 'receive --public' to enable public mode")
        print("  2. Configure port forwarding on your router")
        print("  3. Share your public IP and port with sender")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
