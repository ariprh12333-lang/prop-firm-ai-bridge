from flask import Flask, jsonify, Response
import requests, datetime, time

app = Flask(__name__)

API_KEY = "d3rnlnhr01qopgh97glgd3rnlnhr01qopgh97gm0"

PAIRS = {
    "EURUSD": ["OANDA:EUR_USD", "FX:EURUSD"],
    "GBPUSD": ["OANDA:GBP_USD", "FX:GBPUSD"],
    "USDJPY": ["OANDA:USD_JPY", "FX:USDJPY"],
    "AUDUSD": ["OANDA:AUD_USD", "FX:AUDUSD"],
    "NZDUSD": ["OANDA:NZD_USD", "FX:NZDUSD"],
    "USDCHF": ["OANDA:USD_CHF", "FX:USDCHF"],
    "USDCAD": ["OANDA:USD_CAD", "FX:USDCAD"]
}

def fetch_json(url):
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except:
        return {}

def get_price(symbols):
    for s in symbols:
        url = f"https://finnhub.io/api/v1/quote?symbol={s}&token={API_KEY}"
        d = fetch_json(url)
        if "c" in d and d["c"] != 0:
            return round(float(d["c"]), 5)
    return 0.0

def get_chart_data(symbols):
    now = int(time.time())
    from_ = now - 3600 * 6  # 6 jam terakhir
    for s in symbols:
        url = f"https://finnhub.io/api/v1/forex/candle?symbol={s}&resolution=5&from={from_}&to={now}&token={API_KEY}"
        d = fetch_json(url)
        if "t" in d and d["t"]:
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
    return []

@app.route("/chart")
def chart():
    data = {}
    for name, symbols in PAIRS.items():
        price = get_price(symbols)
        chart = get_chart_data(symbols)
        data[name] = {"price": price, "chart": chart}
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
      <title>Prop Firm AI Bridge (Stable FX)</title>
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
      <h1>✅ Prop Firm AI Bridge (Stable FX)</h1>
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
