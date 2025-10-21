from flask import Flask, jsonify, Response, request
import requests, datetime, time

app = Flask(__name__)

API_KEY = "d3rnlnhr01qopgh97glgd3rnlnhr01qopgh97gm0"
EXCHANGE = "oanda"  # bisa diganti 'ic markets', 'fxcm', dll

# Ambil daftar symbol forex dari Finnhub
def get_symbols(exchange=EXCHANGE):
    url = f"https://finnhub.io/api/v1/forex/symbol?exchange={exchange}&token={API_KEY}"
    r = requests.get(url, timeout=10)
    data = r.json()
    symbols = []
    for s in data:
        if "USD" in s["displaySymbol"]:  # filter hanya pair dengan USD
            symbols.append({
                "name": s["displaySymbol"].replace("/", ""),
                "symbol": s["symbol"]
            })
    return symbols[:7]  # tampilkan 7 pair teratas (EURUSD, GBPUSD, dll)

# Ambil harga terkini
def get_price(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
        r = requests.get(url, timeout=10)
        d = r.json()
        return round(float(d.get("c", 0)), 5)
    except:
        return 0.0

# Ambil data candle 5 menit terakhir
def get_chart_data(symbol):
    try:
        now = int(time.time())
        from_ = now - 3600 * 6
        url = f"https://finnhub.io/api/v1/forex/candle?symbol={symbol}&resolution=5&from={from_}&to={now}&token={API_KEY}"
        r = requests.get(url, timeout=10)
        d = r.json()
        if "t" not in d or not d["t"]:
            return []
        candles = []
        for i in range(len(d["t"])):
            ts = datetime.datetime.utcfromtimestamp(d["t"][i]).strftime("%H:%M")
            candles.append({
                "x": ts,
                "o": d["o"][i],
                "h": d["h"][i],
                "l": d["l"][i],
                "c": d["c"][i]
            })
        return candles
    except:
        return []

@app.route("/chart")
def chart():
    symbols = get_symbols()
    data = {}
    for s in symbols:
        data[s["name"]] = {
            "price": get_price(s["symbol"]),
            "chart": get_chart_data(s["symbol"])
        }
    return jsonify({
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "pairs": data
    })

@app.route("/")
def home():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Prop Firm AI Bridge (Auto Forex FX)</title>
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
      <h1>✅ Prop Firm AI Bridge (Auto Forex FX)</h1>
      <div id="time">Loading...</div>
      <table id="prices">
        <thead><tr><th>Pair</th><th>Price</th></tr></thead>
        <tbody></tbody>
      </table>
      <div id="charts"></div>

      <script>
        let PAIRS=[];
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
              scales:{x:{display:false},y:{display:true,ticks:{color:'#999'}}},
              animation:false
            }
          });
        }

        async function load(){
          try{
            const r=await fetch('/chart');
            const d=await r.json();
            document.getElementById('time').textContent='Last update: '+d.timestamp;
            const tbody=document.querySelector('#prices tbody');
            tbody.innerHTML='';
            PAIRS=Object.keys(d.pairs);
            document.getElementById("charts").innerHTML='';
            PAIRS.forEach((p,i)=>{
              const data=d.pairs[p];
              if(!data)return;
              const price=data.price||'N/A';
              const tr=document.createElement('tr');
              tr.innerHTML=`<td>${p}</td><td style="color:#00ff9d;font-weight:bold">${price}</td>`;
              tbody.appendChild(tr);
              charts[p]=createChart(p,COLORS[i%COLORS.length]);
              const ohlc=data.chart;
              if(ohlc&&ohlc.length){
                charts[p].data.datasets[0].data=ohlc.map(v=>({
                  x:v.x,o:v.o,h:v.h,l:v.l,c:v.c
                }));
                charts[p].update();
              }
            });
          }catch(e){
            document.getElementById('time').textContent='Error loading data';
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
