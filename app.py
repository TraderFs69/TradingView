import streamlit as st
import pandas as pd
import requests
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(layout="wide")

st.title("📊 TEA - Trading Dashboard")

# 🔎 Input utilisateur
ticker = st.text_input("Ticker", "AAPL")

# 🚀 CACHE DATA (optimisé Polygon)
@st.cache_data(ttl=60)
def get_data(ticker):
    API_KEY = st.secrets["POLYGON_API_KEY"]

    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/2024-01-01/2024-03-01?apiKey={API_KEY}"

    try:
        response = requests.get(url)
        return response.json()
    except:
        return None

# 🔗 Appel des données
data = get_data(ticker)

# ❌ Gestion erreurs
if data is None:
    st.error("❌ Erreur de connexion API")
    st.stop()

if "results" not in data:
    st.error("❌ Données invalides (clé API, limite ou ticker)")
    st.stop()

# 📊 Traitement données
df = pd.DataFrame(data["results"])

df["time"] = pd.to_datetime(df["t"], unit="ms")
df["time"] = df["time"].dt.strftime('%Y-%m-%d')

df = df.rename(columns={
    "o": "open",
    "h": "high",
    "l": "low",
    "c": "close"
})

# 📈 EMA
df["ema_20"] = df["close"].ewm(span=20).mean()

# 🎯 Format graphique
candles = df[["time", "open", "high", "low", "close"]].to_dict(orient="records")

ema = df[["time", "ema_20"]].rename(columns={"ema_20": "value"}).to_dict(orient="records")

# 🎨 Options graphique
chartOptions = {
    "layout": {
        "background": {"type": "solid", "color": "#0e0e0e"},
        "textColor": "white"
    },
    "grid": {
        "vertLines": {"color": "#222"},
        "horzLines": {"color": "#222"}
    }
}

# 📊 Séries
seriesCandlestickChart = {
    "type": "Candlestick",
    "data": candles
}

seriesEMA = {
    "type": "Line",
    "data": ema,
    "options": {
        "color": "orange",
        "lineWidth": 2
    }
}

# 🚀 RENDER
renderLightweightCharts([
    {
        "chart": chartOptions,
        "series": [seriesCandlestickChart, seriesEMA]
    }
], 'chart')
