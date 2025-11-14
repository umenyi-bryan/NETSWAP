/*
╔═╗╔═╗╔═╗╦  ╦╔═╗╔╦╗╔═╗
╠═╣╠═╝╠═╝║  ║║ ║ ║ ║╣ 
╩ ╩╩  ╩  ╩═╝╩╚═╝ ╩ ╚═╝
NETSWAP Main JavaScript
Created by CHINEDU
*/

class NetSwapUI {
    constructor() {
        this.socket = io();
        this.currentTransfers = new Map();
        this.init();
        
        // Print ASCII welcome
        this.printWelcome();
    }

    init() {
        this.setupSocketListeners();
        this.setupEventHandlers();
    }

    printWelcome() {
        console.log(`
        ╔═══════════════════════════════════════════════╗
        ║              🚀 NETSWAP v2.0 🚀               ║
        ║         Ultimate File Transfer Tool          ║
        ║              Created by CHINEDU              ║
        ╚═══════════════════════════════════════════════╝
        `);
    }

    setupSocketListeners() {
        this.socket.on('connected', (data) => {
            this.log('🟢 CONNECTED TO NETSWAP', 'success');
            this.log(`🌐 Public IP: ${data.public_ip}`, 'info');
        });

        this.socket.on('transfer_started', (data) => {
            const size = this.formatBytes(data.file.size);
            this.log(`🚀 TRANSFER STARTED: ${data.file.name} (${size})`, 'info');
            this.showTransferProgress(data.file, data.direction);
        });

        this.socket.on('transfer_progress', (data) => {
            this.updateProgress(data);
        });

        this.socket.on('transfer_complete', (data) => {
            this.log(`✅ ${data.message}`, 'success');
            this.hideProgress();
        });

        this.socket.on('transfer_error', (data) => {
            this.log(`❌ ERROR: ${data.error}`, 'error');
            this.hideProgress();
        });

        this.socket.on('receiver_started', (data) => {
            this.log(`🎧 RECEIVER STARTED on port ${data.port}`, 'success');
            this.log(`🌐 Share: ${data.public_ip}:${data.port}`, 'info');
        });

        this.socket.on('receiver_connected', (data) => {
            this.log(`🔗 INCOMING CONNECTION: ${data.client}`, 'info');
        });

        this.socket.on('file_uploaded', (data) => {
            this.log(`📁 FILE READY: ${data.file.name}`, 'success');
        });

        this.socket.on('share_code_created', (data) => {
            this.log(`🎯 SHARE CODE: ${data.share_code}`, 'success');
            this.log(`🔢 Use code: ${data.share_code} for port ${data.port}`, 'info');
        });

        this.socket.on('share_code_resolved', (data) => {
            this.log(`🎯 RESOLVED: ${data.share_code} → ${data.target_ip}:${data.target_port}`, 'success');
        });

        this.socket.on('share_code_error', (data) => {
            this.log(`❌ SHARE CODE ERROR: ${data.error}`, 'error');
        });
    }

    setupEventHandlers() {
        // File input change
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    const file = e.target.files[0];
                    this.log(`📄 SELECTED: ${file.name} (${this.formatBytes(file.size)})`, 'info');
                }
            });
        }
    }

    log(message, type = 'info') {
        const logContainer = document.getElementById('transferLog');
        if (!logContainer) return;

        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        logEntry.innerHTML = `<span style="color: var(--neon-purple);">[${timestamp}]</span> ${message}`;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showTransferProgress(file, direction) {
        let progressEl = document.getElementById('transferProgress');
        if (!progressEl) {
            progressEl = document.createElement('div');
            progressEl.id = 'transferProgress';
            progressEl.innerHTML = `
                <div style="margin: 1rem 0; padding: 1rem; border: 1px solid var(--neon-blue); background: rgba(0,0,0,0.5);">
                    <h4 style="color: var(--neon-cyan); margin-bottom: 0.5rem;">
                        <i class="fas fa-rocket"></i> TRANSFER IN PROGRESS
                    </h4>
                    <div style="color: var(--neon-green); margin-bottom: 0.5rem;">
                        <strong>${file.name}</strong> (${this.formatBytes(file.size)})
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 0%"></div>
                    </div>
                    <div class="progress-text" style="color: var(--neon-cyan); text-align: center; margin-top: 0.5rem;">0%</div>
                </div>
            `;
            document.querySelector('.transfer-status').appendChild(progressEl);
        }
    }

    updateProgress(data) {
        const progressFill = document.querySelector('.progress-fill');
        const progressText = document.querySelector('.progress-text');
        
        if (progressFill && progressText) {
            progressFill.style.width = `${data.progress}%`;
            const bytesText = data.sent_bytes ? 
                `${this.formatBytes(data.sent_bytes)} / ${this.formatBytes(data.total_bytes)}` :
                `${this.formatBytes(data.received_bytes)} / ${this.formatBytes(data.total_bytes)}`;
            progressText.textContent = `${Math.round(data.progress)}% - ${bytesText}`;
        }
    }

    hideProgress() {
        const progressEl = document.getElementById('transferProgress');
        if (progressEl) {
            progressEl.style.opacity = '0';
            setTimeout(() => progressEl.remove(), 500);
        }
    }
}

// Global functions for HTML buttons
function sendFile() {
    const fileInput = document.getElementById('fileInput');
    const targetIp = document.getElementById('targetIp').value;
    const targetPort = document.getElementById('targetPort').value;

    if (!fileInput.files.length) {
        netswapUI.log('❌ PLEASE SELECT A FILE', 'error');
        return;
    }

    if (!targetIp) {
        netswapUI.log('❌ PLEASE ENTER TARGET IP', 'error');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    // Upload file first
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            netswapUI.log(`🚀 STARTING TRANSFER to ${targetIp}:${targetPort}`, 'info');
            netswapUI.socket.emit('send_file', {
                ip: targetIp,
                port: parseInt(targetPort),
                file_path: `uploads/${data.file.name}`
            });
        } else {
            netswapUI.log(`❌ UPLOAD FAILED: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        netswapUI.log(`❌ UPLOAD ERROR: ${error}`, 'error');
    });
}

function startReceiver() {
    const port = document.getElementById('listenPort').value || 8888;
    netswapUI.log(`🎧 STARTING RECEIVER on port ${port}`, 'info');
    netswapUI.socket.emit('start_receiver', { port: parseInt(port) });
}

function stopReceiver() {
    netswapUI.log('🛑 STOPPING RECEIVER', 'warning');
    netswapUI.socket.emit('stop_receiver');
}

function createShareCode() {
    const port = document.getElementById('sharePort').value || 8888;
    netswapUI.log(`🎯 GENERATING SHARE CODE for port ${port}`, 'info');
    netswapUI.socket.emit('create_share_code', { port: parseInt(port) });
}

function connectViaShareCode() {
    const shareCode = document.getElementById('inputShareCode').value.trim().toUpperCase();
    if (!shareCode) {
        netswapUI.log('❌ PLEASE ENTER SHARE CODE', 'error');
        return;
    }
    
    netswapUI.log(`🎯 RESOLVING SHARE CODE: ${shareCode}`, 'info');
    netswapUI.socket.emit('connect_via_share_code', { share_code: shareCode });
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.netswapUI = new NetSwapUI();
});
