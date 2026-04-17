from flask import Flask, request, jsonify, Response, stream_with_context
import requests
import threading
from radio_core import FMReceiver

app = Flask(__name__)

receiver = FMReceiver(freq=104.8e6, rf_gain=30, volume=1.0)


def start_receiver():
    receiver.start()


threading.Thread(target=start_receiver, daemon=True).start()


@app.route("/status", methods=["GET"])
def status():
    try:
        return jsonify(receiver.get_status())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/stream")
def stream():
    try:
        upstream = requests.get(
            "http://127.0.0.1:8080",
            stream=True,
            timeout=(3, 10)
        )
        upstream.raise_for_status()
    except requests.RequestException as e:
        return Response(
            f"Audio stream unavailable: {e}\n",
            status=503,
            content_type="text/plain; charset=utf-8"
        )

    def generate():
        try:
            for chunk in upstream.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk
        except GeneratorExit:
            pass
        except Exception:
            pass
        finally:
            upstream.close()

    return Response(
        stream_with_context(generate()),
        content_type="audio/mpeg"
    )


@app.route("/set_freq", methods=["POST"])
def set_freq():
    try:
        data = request.get_json(force=True)
        freq_mhz = float(data["freq_mhz"])
        receiver.set_station_freq(freq_mhz * 1e6)
        return jsonify({
            "ok": True,
            "freq_mhz": freq_mhz
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/set_volume", methods=["POST"])
def set_volume():
    try:
        data = request.get_json(force=True)
        volume = float(data["volume"])
        receiver.set_audio_volume(volume)
        return jsonify({
            "ok": True,
            "volume": volume
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>SDR Radio Control</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f6f8;
            color: #222;
            text-align: center;
            margin: 0;
            padding: 30px;
        }

        .card {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 18px rgba(0,0,0,0.08);
        }

        h1 {
            margin-top: 0;
        }

        .section {
            margin: 24px 0;
        }

        button {
            margin: 6px;
            padding: 12px 18px;
            border: none;
            border-radius: 10px;
            background: #2563eb;
            color: white;
            cursor: pointer;
            font-size: 15px;
        }

        button:hover {
            background: #1d4ed8;
        }

        input[type="range"] {
            width: 280px;
        }

        .status {
            background: #f8fafc;
            border-radius: 12px;
            padding: 16px;
            margin-top: 16px;
        }

        .small {
            color: #666;
            font-size: 14px;
        }

        audio {
            width: 100%;
            margin-top: 12px;
        }

        .stations-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 14px;
            margin-top: 12px;
        }

        .station-card {
            background: #f8fafc;
            border-radius: 12px;
            padding: 12px;
        }

        .station-name {
            margin-top: 8px;
            font-size: 14px;
            color: #444;
        }

        input[type="text"], input[type="number"] {
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #ccc;
            font-size: 15px;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>📻 Удалённый SDR-приёмник</h1>

        <div class="section">
            <h2>Прослушивание</h2>
            <p class="small">Нажми «Запустить радио». Если поток завис, нажми «Переподключить».</p>

            <audio id="player" controls preload="none"></audio>

            <br><br>

            <button onclick="startRadio()">▶ Запустить радио</button>
            <button onclick="stopRadio()">⏹ Остановить</button>
            <button onclick="reloadStream()">🔄 Переподключить</button>
        </div>

        <div class="section">
            <h2>Популярные станции</h2>
            <div class="stations-grid">
                <div class="station-card">
                    <button onclick="setFreq(88.3)">88.3</button>
                    <div class="station-name">Комсомольская правда</div>
                </div>
                <div class="station-card">
                    <button onclick="setFreq(88.7)">88.7</button>
                    <div class="station-name">Авторадио</div>
                </div>
                <div class="station-card">
                    <button onclick="setFreq(89.6)">89.6</button>
                    <div class="station-name">Русское Радио</div>
                </div>
                <div class="station-card">
                    <button onclick="setFreq(90.6)">90.6</button>
                    <div class="station-name">Радио Маяк</div>
                </div>
                <div class="station-card">
                    <button onclick="setFreq(103.3)">103.3</button>
                    <div class="station-name">Comedy Radio</div>
                </div>
                <div class="station-card">
                    <button onclick="setFreq(104.3)">104.3</button>
                    <div class="station-name">Дорожное радио</div>
                </div>
                <div class="station-card">
                    <button onclick="setFreq(106.2)">106.2</button>
                    <div class="station-name">Радио Дача</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Ручной ввод частоты</h2>
            <input type="text" id="freqInput" value="104.8">
            <button onclick="applyFreq()">Применить</button>
        </div>

        <div class="section">
            <h2>Громкость радиоприёмника</h2>
            <input type="range" min="0.5" max="10" step="0.5" value="5" id="radioVolume"
                   oninput="radioVolLabel.innerText=this.value"
                   onchange="setVolume(this.value)">
            <div>Текущее значение: <span id="radioVolLabel">5</span></div>
        </div>

        <div class="section">
            <h2>Громкость в браузере</h2>
            <input type="range" min="0" max="1" step="0.05" value="1" id="playerVolume"
                   oninput="setPlayerVolume(this.value)">
            <div>Локальная громкость браузера</div>
        </div>

        <div class="status">
            <h2>Статус</h2>
            <div id="status">Загрузка...</div>
        </div>
    </div>

    <script>
        async function setFreq(freq) {
            await fetch('/set_freq', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({freq_mhz: freq})
            });
            document.getElementById('freqInput').value = freq;
            updateStatus();
        }

        async function applyFreq() {
            let freqText = document.getElementById('freqInput').value.trim();
            freqText = freqText.replace(',', '.');
            const freq = parseFloat(freqText);

            if (!isNaN(freq)) {
                await setFreq(freq);
                document.getElementById('freqInput').value = freq.toFixed(1);
            }
        }

        async function setVolume(vol) {
            await fetch('/set_volume', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({volume: parseFloat(vol)})
            });
            updateStatus();
        }

        function setPlayerVolume(vol) {
            const player = document.getElementById('player');
            player.volume = parseFloat(vol);
        }

        function startRadio() {
            const player = document.getElementById('player');
            player.pause();
            player.removeAttribute('src');
            player.load();

            setTimeout(() => {
                player.src = "/stream?t=" + Date.now();
                player.load();
                player.play().catch(err => console.log("Play error:", err));
            }, 700);
        }

        function stopRadio() {
            const player = document.getElementById('player');
            player.pause();
            player.removeAttribute('src');
            player.load();
        }

        function reloadStream() {
            stopRadio();
            setTimeout(() => {
                startRadio();
            }, 1000);
        }

        async function updateStatus() {
            try {
                const response = await fetch('/status?t=' + Date.now());
                const data = await response.json();
                document.getElementById('status').innerHTML =
                    'Частота: ' + data.freq_mhz + ' MHz<br>' +
                    'RF Gain: ' + data.rf_gain + '<br>' +
                    'Громкость приёмника: ' + data.volume;
                document.getElementById('radioVolume').value = data.volume;
                document.getElementById('radioVolLabel').innerText = data.volume;
                document.getElementById('freqInput').value = data.freq_mhz;
            } catch (e) {
                document.getElementById('status').innerText = 'Ошибка получения статуса';
            }
        }

        updateStatus();
        setInterval(updateStatus, 2000);
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
