from flask import Flask, jsonify, Response
import requests, json, time

app = Flask(__name__)

# --- Ambil data realtime dari exchangerate.host (gratis, tanpa API key) ---
def get_fx():
    url = "https://api.exchangerate.host/latest?base=USD"
    r = requests.get(url, timeout=10)
    data = r.json().get("rates", {})
    fx = {
        "EURUSD": round(1 / data["EUR"], 5),
        "GBPUSD": round(1 / data["GBP"], 5),
        "USDJPY": round(data["JPY"], 3),
        "AUDUSD": round(1 / data["AUD"], 5),
        "NZDUSD": round(1 / data["NZD"], 5),
        "USDCHF": round(data["CHF"], 5),
        "USDCAD": round(data["CAD"], 5),
    }
    return fx

@app.route("/chart")
def chart():
    # selalu ambil data terbaru saat endpoint dipanggil
    try:
        return jsonify(get_fx())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Dashboard sederhana + auto refresh 60 detik
@app.route("/")
def home():
    html = """
    <!doctype html>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
      body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;padding:18px}
      h1{font-size:18px;margin:0 0 8px}
      #t{opacity:.7;font-size:12px;margin-bottom:12px}
      table{border-collapse:collapse;width:100%;max-width:420px}
      th,td{border:1px solid #eee;padding:8px;text-align:left}
      tr:nth-child(even){background:#fafafa}
      .ok{color:#0a0}
    </style>
    <h1>✅ Prop Firm AI Bridge (FX)</h1>
    <div id="t">memuat…</div>
    <table id="tb"><thead><tr><th>Pair</th><th>Price</th></tr></thead><tbody></tbody></table>

    <script>
      async function load(){
        const t = document.getElementById('t');
        try {
          const r = await fetch('/chart',{cache:'no-store'});
          const d = await r.json();
          const tb = document.querySelector('#tb tbody');
          tb.innerHTML='';
          Object.entries(d).forEach(([k,v])=>{
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${k}</td><td>${v}</td>`;
            tb.appendChild(tr);
          });
          t.textContent = 'Last update: ' + new Date().toLocaleString();
          t.className='ok';
        } catch(e){
          t.textContent = 'Error: ' + e;
          t.className='';
        }
      }
      load();                       // muat saat pertama kali
      setInterval(load, 60000);     // auto-refresh tiap 60 detik
    </script>
    """
    return Response(html, mimetype="text/html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

