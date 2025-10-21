from flask import Flask, jsonify, Response
import requests

app = Flask(__name__)

# Ganti dengan API key kamu
API_KEY = "5d43621b934243dbbfdd5bbbf1a8bf0b"

# Pair forex utama
PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD",
    "NZD/USD", "USD/CHF", "USD/CAD"
]

def get_chart_data(symbol):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=30&apikey={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if "values" not in data:
            print(f"[ERROR] Data invalid for {symbol}: {data}")
            return []
        values = data["values"][::-1]  # urutkan agar dari lama ke baru
        ohlc = [
            {
                "x": v["datetime"],
                "o": float(v["open"]),
                "h": float(v["high"]),
                "l": float(v["low"]),
                "c": float(v["close"])
            }
            for v in values
        ]
        return ohlc
    except Exception as e:
        print(f"[ERROR] Failed {symbol}: {e}")
        return []

@app.route("/chart")
def chart():
    try:
        fx = {p.replace("/", ""): get_chart_data(p) for p in PAIRS}
        return jsonify(fx)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/")
def home():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Prop Firm AI Bridge - Live Forex Candlestick</title>
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/chartjs-chart-financial"></script>
      <style>
        body{font-family:system-ui,Arial;background:#000;color:#eee;margin:0;padding:20px}
        h1{text-align:center;color:#00ff9d;margin-bottom:10px}
        #time{text-align:center;color:#ccc;font-size:13px;margin-bottom:10px}
        .chart-container{max-width:640px;margin:25px auto;background:#111;
          padding:15px;border-radius:10px;box-shadow:0 0 6px #000}
        canvas{width:100%;height:320px;}
        .error{color:#ff4d4d;text-align:center;margin-top:10px}
      </style>
    </head>
    <body>
      <h1>✅ Prop Firm AI Bridge (Live Candlestick FX)</h1>
      <div id="time">Loading...</div>
      <div id="charts"></div>
      <div id="err" class="error"></div>
      <script>
        const PAIRS=["EURUSD","GBPUSD","USDJPY","AUDUSD","NZDUSD","USDCHF","USDCAD"];
        const COLORS=["#00ff9d","#ffcc00","#ff3d71","#00bfff","#00ffaa","#ff8c00","#bbbbff"];
        const charts={};

        function createChart(pair,color){
          const div=document.createElement('div');
          div.className='chart-container';
          div.innerHTML=`<h3>${pair}</h3><canvas id='c-${pair}'></canvas>`;
          document.getElementById("charts").appendChild(div);
          const ctx=document.getElementById(`c-${pair}`);
          return new Chart(ctx,{
            type:'candlestick',
            data:{datasets:[{label:pair,borderColor:color,data:[]}]},
            options:{
              plugins:{legend:{display:false}},
              scales:{x:{display:false},y:{display:true,ticks:{color:'#999'}}},
              animation:false
            }
          });
        }

        PAIRS.forEach((p,i)=>charts[p]=createChart(p,COLORS[i]));

        async function load(){
          try{
            const r=await fetch('/chart');
            const d=await r.json();
            const now=new Date().toLocaleTimeString();
            document.getElementById('time').textContent='Last update: '+now;
            let anyValid=false;
            PAIRS.forEach(p=>{
              const data=d[p];
              if(!data||!data.length)return;
              charts[p].data.datasets[0].data=data.map(v=>({
                x:v.x,o:v.o,h:v.h,l:v.l,c:v.c
              }));
              charts[p].update();
              anyValid=true;
            });
            if(!anyValid){
              document.getElementById('err').textContent="⚠️ No valid data (check API key or symbol format)";
            }else{
              document.getElementById('err').textContent="";
            }
          }catch(e){
            document.getElementById('err').textContent='❌ Error: '+e;
          }
        }

        load();
        setInterval(load,60000);
      </script>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
