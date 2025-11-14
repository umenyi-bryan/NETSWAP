#!/usr/bin/env python3
"""
╔═╗╔╦╗╔╗ ╔═╗╔═╗╦ ╦╔═╗╔═╗
║ ║ ║ ╠╩╗╠═╣║  ╠═╣║╣ ║ ║
╚═╝ ╩ ╚═╝╩ ╩╚═╝╩ ╩╚═╝╚═╝
Netswap - Ultimate File Transfer
      Created by CHINEDU
"""

import os
import socket
import threading
import time
import hashlib
import json
import requests
import random
import string
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import logging

# ASCII Banner
def print_banner():
    banner = """
    ╔═══════════════════════════════════════════════╗
    ║              🚀 NETSWAP v2.0 🚀               ║
    ║         Ultimate File Transfer Tool          ║
    ║              Created by CHINEDU              ║
    ║                                               ║
    ║    ███╗   ██╗███████╗████████╗███████╗       ║
    ║    ████╗  ██║██╔════╝╚══██╔══╝██╔════╝       ║
    ║    ██╔██╗ ██║█████╗     ██║   ███████╗       ║
    ║    ██║╚██╗██║██╔══╝     ██║   ╚════██║       ║
    ║    ██║ ╚████║███████╗   ██║   ███████║       ║
    ║    ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚══════╝       ║
    ║           ███████╗██╗    ██╗ █████╗ ██████╗  ║
    ║           ██╔════╝██║    ██║██╔══██╗██╔══██╗ ║
    ║           ███████╗██║ █╗ ██║███████║██████╔╝ ║
    ║           ╚════██║██║███╗██║██╔══██║██╔═══╝  ║
    ║           ███████║╚███╔███╔╝██║  ██║██║      ║
    ║           ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝      ║
    ╚═══════════════════════════════════════════════╝
    """
    print(banner)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('Netswap')

class NetSwapCore:
    def __init__(self):
        self.chunk_size = 8192
        self.timeout = 60
        self.transfers = {}
        self.upload_folder = "uploads"
        self.public_ip = self.get_public_ip()
        
        # Create upload directory
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def get_public_ip(self):
        """Get public IP address"""
        try:
            response = requests.get('https://api.ipify.org', timeout=5)
            return response.text
        except:
            return "Unknown"
    
    def generate_share_code(self):
        """Generate a unique share code"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def calculate_checksum(self, file_path):
        """Calculate MD5 checksum for file verification"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_file_info(self, file_path):
        """Get file size and type information"""
        if not os.path.exists(file_path):
            return None
        
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        
        # File type categorization
        file_types = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
            'audio': ['.mp3', '.wav', '.ogg', '.m4a'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.md']
        }
        
        file_type = 'other'
        for category, extensions in file_types.items():
            if file_ext in extensions:
                file_type = category
                break
        
        return {
            'name': file_name,
            'size': file_size,
            'type': file_type,
            'extension': file_ext,
            'checksum': self.calculate_checksum(file_path)
        }

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'netswap-secret-key-2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
netswap = NetSwapCore()

# Store active connections
active_receivers = {}
share_codes = {}

# Web Routes
@app.route('/')
def index():
    return render_template('index.html', public_ip=netswap.public_ip, creator="CHINEDU")

@app.route('/terminal')
def terminal():
    return render_template('terminal.html', creator="CHINEDU")

@app.route('/files')
def files():
    return render_template('files.html', creator="CHINEDU")

@app.route('/network')
def network():
    return render_template('network.html', public_ip=netswap.public_ip, creator="CHINEDU")

@app.route('/about')
def about():
    return render_template('about.html', creator="CHINEDU")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        file_info = netswap.get_file_info(file_path)
        socketio.emit('file_uploaded', {
            'file': file_info,
            'timestamp': time.time()
        })
        
        return jsonify({'success': True, 'file': file_info})
    
    return jsonify({'error': 'Upload failed'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Socket Events
@socketio.on('connect')
def handle_connect():
    logger.info(f"🟢 Client connected: {request.sid}")
    emit('connected', {
        'message': 'Connected to NETSWAP - Created by CHINEDU',
        'public_ip': netswap.public_ip
    })

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"🔴 Client disconnected: {request.sid}")
    # Clean up share codes or receivers
    for code, data in list(share_codes.items()):
        if data.get('sid') == request.sid:
            del share_codes[code]
    
    if request.sid in active_receivers:
        del active_receivers[request.sid]

@socketio.on('create_share_code')
def handle_create_share_code(data):
    port = data.get('port', 8888)
    share_code = netswap.generate_share_code()
    
    share_codes[share_code] = {
        'sid': request.sid,
        'port': port,
        'created_at': time.time(),
        'public_ip': netswap.public_ip
    }
    
    # Auto-cleanup after 1 hour
    threading.Timer(3600, lambda: share_codes.pop(share_code, None)).start()
    
    emit('share_code_created', {
        'share_code': share_code,
        'port': port,
        'public_ip': netswap.public_ip
    })

@socketio.on('connect_via_share_code')
def handle_connect_share_code(data):
    share_code = data.get('share_code')
    
    if share_code not in share_codes:
        emit('share_code_error', {'error': 'Invalid share code'})
        return
    
    receiver_info = share_codes[share_code]
    target_ip = receiver_info['public_ip']
    target_port = receiver_info['port']
    
    emit('share_code_resolved', {
        'target_ip': target_ip,
        'target_port': target_port,
        'share_code': share_code
    })

# File Transfer Functions
def send_file_direct(ip, port, file_path, sid):
    try:
        if not os.path.exists(file_path):
            socketio.emit('transfer_error', 
                         {'error': f'File not found: {file_path}'}, 
                         room=sid)
            return False
        
        file_info = netswap.get_file_info(file_path)
        file_size = file_info['size']
        
        socketio.emit('transfer_started', {
            'file': file_info,
            'direction': 'outgoing',
            'target': f"{ip}:{port}",
            'method': 'direct'
        }, room=sid)
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(30)
            sock.connect((ip, port))
            
            # Send metadata
            metadata = {
                'action': 'file_transfer',
                'file_name': file_info['name'],
                'file_size': file_size,
                'file_type': file_info['type'],
                'checksum': file_info['checksum']
            }
            sock.send(json.dumps(metadata).encode() + b'\n')
            
            # Wait for ready signal
            response = sock.recv(1024).decode().strip()
            if response != 'READY':
                socketio.emit('transfer_error', 
                             {'error': 'Receiver not ready'}, 
                             room=sid)
                return False
            
            # Send file data
            sent_bytes = 0
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(netswap.chunk_size)
                    if not chunk:
                        break
                    sock.send(chunk)
                    sent_bytes += len(chunk)
                    progress = (sent_bytes / file_size) * 100
                    
                    socketio.emit('transfer_progress', {
                        'progress': progress,
                        'sent_bytes': sent_bytes,
                        'total_bytes': file_size,
                        'method': 'direct'
                    }, room=sid)
            
            # Wait for verification
            verification = sock.recv(1024).decode().strip()
            if verification == 'SUCCESS':
                socketio.emit('transfer_complete', {
                    'message': '✅ Transfer completed successfully!'
                }, room=sid)
                return True
            else:
                socketio.emit('transfer_error', {
                    'error': '❌ File verification failed'
                }, room=sid)
                return False
                
    except Exception as e:
        raise e

@socketio.on('send_file')
def handle_send_file(data):
    target_ip = data.get('ip')
    target_port = data.get('port')
    file_path = data.get('file_path')
    
    if not all([target_ip, target_port, file_path]):
        emit('transfer_error', {'error': 'Missing required parameters'})
        return
    
    # Start transfer in background thread
    thread = threading.Thread(
        target=send_file_direct,
        args=(target_ip, target_port, file_path, request.sid)
    )
    thread.daemon = True
    thread.start()

def start_receiver(port, sid):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('0.0.0.0', port))
            server_socket.listen(1)
            server_socket.settimeout(netswap.timeout)
            
            active_receivers[sid] = {
                'socket': server_socket,
                'port': port,
                'running': True
            }
            
            socketio.emit('receiver_started', {
                'port': port,
                'message': f'🎧 Listening on port {port}',
                'public_ip': netswap.public_ip
            }, room=sid)
            
            while active_receivers.get(sid, {}).get('running', False):
                try:
                    client_socket, client_address = server_socket.accept()
                    client_socket.settimeout(netswap.timeout)
                    
                    # Handle connection in separate thread
                    client_thread = threading.Thread(
                        target=handle_client_connection,
                        args=(client_socket, client_address, sid)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if active_receivers.get(sid, {}).get('running', False):
                        logger.error(f"Receiver error: {e}")
                        break
            
            # Cleanup
            if sid in active_receivers:
                del active_receivers[sid]
                
    except Exception as e:
        socketio.emit('receiver_error', 
                     {'error': f'Receiver error: {str(e)}'}, 
                     room=sid)

def handle_client_connection(client_socket, client_address, sid):
    try:
        socketio.emit('receiver_connected', {
            'client': f"{client_address[0]}:{client_address[1]}"
        }, room=sid)
        
        # Receive metadata
        metadata = b""
        while b'\n' not in metadata:
            chunk = client_socket.recv(1024)
            if not chunk:
                break
            metadata += chunk
        
        metadata = json.loads(metadata.decode().strip())
        
        file_name = metadata['file_name']
        file_size = metadata['file_size']
        expected_checksum = metadata['checksum']
        
        # Save file
        save_path = os.path.join(netswap.upload_folder, file_name)
        
        # Handle duplicate files
        counter = 1
        original_path = save_path
        while os.path.exists(save_path):
            name, ext = os.path.splitext(original_path)
            save_path = f"{name}_{counter}{ext}"
            counter += 1
        
        socketio.emit('transfer_started', {
            'file': metadata,
            'direction': 'incoming',
            'from': f"{client_address[0]}:{client_address[1]}",
            'method': 'direct'
        }, room=sid)
        
        # Send ready signal
        client_socket.send(b'READY\n')
        
        # Receive file data
        received_bytes = 0
        hash_md5 = hashlib.md5()
        
        with open(save_path, 'wb') as f:
            while received_bytes < file_size:
                chunk = client_socket.recv(
                    min(netswap.chunk_size, file_size - received_bytes)
                )
                if not chunk:
                    break
                f.write(chunk)
                hash_md5.update(chunk)
                received_bytes += len(chunk)
                
                progress = (received_bytes / file_size) * 100
                socketio.emit('transfer_progress', {
                    'progress': progress,
                    'received_bytes': received_bytes,
                    'total_bytes': file_size,
                    'method': 'direct'
                }, room=sid)
        
        # Verify checksum
        actual_checksum = hash_md5.hexdigest()
        if actual_checksum == expected_checksum:
            client_socket.send(b'SUCCESS\n')
            socketio.emit('transfer_complete', {
                'message': f'✅ File received: {os.path.basename(save_path)}',
                'file_path': save_path
            }, room=sid)
        else:
            client_socket.send(b'FAILED\n')
            os.remove(save_path)
            socketio.emit('transfer_error', {
                'error': '❌ File verification failed - transfer corrupted'
            }, room=sid)
            
    except Exception as e:
        logger.error(f"Client connection error: {e}")
        socketio.emit('transfer_error', 
                     {'error': f'Transfer error: {str(e)}'}, 
                     room=sid)
    finally:
        client_socket.close()

@socketio.on('start_receiver')
def handle_start_receiver(data):
    port = data.get('port', 8888)
    thread = threading.Thread(target=start_receiver, args=(port, request.sid))
    thread.daemon = True
    thread.start()

@socketio.on('stop_receiver')
def handle_stop_receiver():
    if request.sid in active_receivers:
        active_receivers[request.sid]['running'] = False
        emit('receiver_stopped', {'message': '🛑 Receiver stopped'})

if __name__ == '__main__':
    print_banner()
    logger.info("🚀 Starting NETSWAP Server...")
    logger.info("🌐 Web UI: http://localhost:5000")
    logger.info("📡 Public IP: %s", netswap.public_ip)
    logger.info("👨‍💻 Created by: CHINEDU")
    logger.info("💡 For internet transfers, ensure port forwarding is configured!")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

