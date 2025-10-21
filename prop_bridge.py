from flask import Flask, jsonify, Response
import requests, datetime

app = Flask(__name__)

API_KEY = "5d43621b934243dbbfdd5bbbf1a8bf0b"
PAIRS = [
    "EUR/USD","GBP/USD","USD/JPY","AUD/USD",
    "NZD/USD","USD/CHF","USD/CAD"
]

def get_price(symbol):
    """Ambil harga terakhir untuk pair"""
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={API_KEY}"
    r = requests.get(url, timeout=10)
    data = r.json()
    return data.get("price", "N/A")

def get_chart_data(symbol):
    """Ambil data candlestick 1-menit"""
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=50&apikey={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if "values" not in data:
            print(f"[ERROR] {symbol} invalid: {data}")
            return []
        values = data["values"][::-1]
        ohlc = [
            {"x": v["datetime"],
             "o": float(v["open"]),
             "h": float(v["high"]),
             "l": float(v["low"]),
             "c": float(v["close"])}
            for v in values
        ]
        return ohlc
    except Exception as e:
        print(f"[ERROR] {symbol}: {e}")
        return []

@app.route("/chart")
def chart():
    try:
        fx = {}
        for p in PAIRS:
            symbol = p.replace("/","")
            fx[symbol] = {
                "chart": get_chart_data(p),
                "price": get_price(p)
            }
        return jsonify({
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "pairs": fx
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/")
def home():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Prop Firm AI Bridge - Live Forex Dashboard</title>
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/chartjs-chart-financial"></script>
      <style>
        body{font-family:system-ui,Arial;background:#000;color:#eee;margin:0;padding:10px}
        h1{text-align:center;color:#00ff9d;margin-bottom:4px}
        #time{text-align:center;color:#ccc;font-size:13px;margin-bottom:8px}
        table{width:90%;margin:0 auto;border-collapse:collapse;margin-bottom:15px}
        th,td{padding:8px;text-align:center;border-bottom:1px solid #333}
        th{color:#00ff9d}
        .chart-box{max-width:640px;margin:25px auto;background:#111;
          padding:15px;border-radius:10px;box-shadow:0 0 6px #000}
        canvas{width:100%;height:320px;}
      </style>
    </head>
    <body>
      <h1>✅ Prop Firm AI Bridge (Live Candlestick FX)</h1>
      <div id="time">Loading...</div>
      <table id="prices">
        <thead><tr><th>Pair</th><th>Price</th></tr></thead>
        <tbody></tbody>
      </table>
      <div id="charts"></div>

      <script>
        const PAIRS=["EURUSD","GBPUSD","USDJPY","AUDUSD","NZDUSD","USDCHF","USDCAD"];
        const COLORS=["#00ff9d","#ffcc00","#ff3d71","#00bfff","#00ffaa","#ff8c00","#bbbbff"];
        const charts={};

        function createChart(pair,color){
          const div=document.createElement('div');
          div.className='chart-box';
          div.innerHTML=`<h3 style='color:${color};text-align:center;'>${pair}</h3><canvas id='c-${pair}'></canvas>`;
          document.getElementById("charts").appendChild(div);
          const ctx=document.getElementById(`c-${pair}`);
          return new Chart(ctx,{
            type:'candlestick',
            data:{datasets:[{label:pair,borderColor:color,data:[]}]},
            options:{
              plugins:{legend:{display:false}},
              scales:{
                x:{display:false},
                y:{display:true,ticks:{color:'#999'}}
              },
              animation:false
            }
          });
        }

        PAIRS.forEach((p,i)=>charts[p]=createChart(p,COLORS[i]));

        async function load(){
          try{
            const r=await fetch('/chart');
            const d=await r.json();
            document.getElementById('time').textContent='Last update: '+d.timestamp;

            const tbody=document.querySelector('#prices tbody');
            tbody.innerHTML='';
            PAIRS.forEach(p=>{
              const data=d.pairs[p];
              if(!data)return;
              const price=data.price||'N/A';
              const tr=document.createElement('tr');
              tr.innerHTML=`<td>${p}</td><td style="color:#00ff9d;font-weight:bold">${price}</td>`;
              tbody.appendChild(tr);

              const ohlc=data.chart;
              if(ohlc&&ohlc.length){
                charts[p].data.datasets[0].data=ohlc.map(v=>({
                  x:v.x,o:v.o,h:v.h,l:v.l,c:v.c
                }));
                charts[p].update();
              }
            });
          }catch(e){
            document.getElementById('time').textContent='Error fetching data';
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
