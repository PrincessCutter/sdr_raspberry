#!/bin/bash

echo "🚀 STARTING RADIO SYSTEM..."

pkill -f fm2_rx.py
pkill -f ffmpeg
pkill -f radio_webserver.py

sleep 2

rm -f server.log ffmpeg.log

echo "🎧 Starting audio stream..."
(
while true; do
    ffmpeg -fflags nobuffer -flags low_delay \
    -f s16le -ar 48000 -ac 1 \
    -i "udp://127.0.0.1:1235?fifo_size=1000000&overrun_nonfatal=1" \
    -codec:a libmp3lame -b:a 128k \
    -content_type audio/mpeg \
    -f mp3 -listen 1 http://0.0.0.0:8080 >> ffmpeg.log 2>&1
    echo "ffmpeg restarted at $(date)" >> ffmpeg.log
    sleep 1
done
) &
sleep 3

echo "🖥 Starting WEB server..."
python3 radio_webserver.py > server.log 2>&1 &

sleep 3

echo ""
echo "=============================="
echo "📻 RADIO READY!"
echo "🌍 WEB: http://192.168.0.132:5000"
echo "=============================="
