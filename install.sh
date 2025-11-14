#!/bin/bash
echo ""
echo "    ╔═══════════════════════════════════════════════╗"
echo "    ║              🚀 NETSWAP v2.0 🚀               ║"
echo "    ║         Ultimate File Transfer Tool          ║"
echo "    ║              Created by CHINEDU              ║"
echo "    ╚═══════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed. Please install Python3 first."
    exit 1
fi

# Install required packages
echo "📦 Installing dependencies..."
pip install flask flask-socketio eventlet pillow requests

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p static/css static/js static/images templates uploads

echo ""
echo "✅ INSTALLATION COMPLETE!"
echo ""
echo "🎯 QUICK START:"
echo "   python app.py"
echo ""
echo "🌐 ACCESS POINTS:"
echo "   Web UI:      http://localhost:5000"
echo "   Terminal:    http://localhost:5000/terminal" 
echo "   Network:     http://localhost:5000/network"
echo "   About:       http://localhost:5000/about"
echo ""
echo "🚀 KEY FEATURES:"
echo "   ✓ Transfer any file size"
echo "   ✓ Works locally and over internet"
echo "   ✓ Beautiful neon ASCII design"
echo "   ✓ File integrity verification"
echo "   ✓ Share code system"
echo ""
echo "🎉 Enjoy NETSWAP - Created with passion by CHINEDU!"
echo ""
