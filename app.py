import streamlit as st
import pandas as pd
import requests
from streamlit_lightweight_charts import renderLightweightCharts
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

st.title("📊 TEA - Trading Dashboard")

ticker = st.text_input("Ticker", "AAPL")

# =========================
# 🔥 DATA FUNCTION (ROBUSTE)
# =========================
@st.cache_data(ttl=60)
def get_data(ticker):
    API_KEY = st.secrets["POLYGON_API_KEY"]

    end = datetime.today()
    start = end - timedelta(days=120)

    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start.strftime('%Y-%m-%d')}/{end.strftime('%Y-%m-%d')}?apiKey={API_KEY}"

    try:
        response = requests.get(url)

        if response.status_code != 200:
            return None, f"Erreur API: {response.status_code}"

        data = response.json()

        if "results" not in data:
            return None, "Aucune donnée retournée"

        df = pd.DataFrame(data["results"])

        if df.empty:
            return None, "Data vide"

        return df, None

    except Exception as e:
        return None, str(e)

# =========================
# 📥 LOAD DATA
# =========================
df, error = get_data(ticker)

# 🔴 FALLBACK si problème API
if df is None:
    st.warning(f"⚠️ Polygon ne répond pas ({error}) → données simulées utilisées")

    # données fake pour debug
    df = pd.DataFrame({
        "t": pd.date_range(end=datetime.today(), periods=50),
        "o": range(100, 150),
        "h": range(105, 155),
        "l": range(95, 145),
        "c": range(102, 152),
    })

# =========================
# 📊 CLEAN DATA
# =========================
df["time"] = pd.to_datetime(df["t"])
df["time"] = df["time"].dt.strftime('%Y-%m-%d')

df = df.rename(columns={
    "o": "open",
    "h": "high",
    "l": "low",
    "c": "close"
})

st.write(f"📊 Nombre de bougies: {len(df)}")

# =========================
# 📈 INDICATEURS
# =========================

# EMA
df["ema20"] = df["close"].ewm(span=20).mean()

# RSI
delta = df["close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()

rs = avg_gain / avg_loss
df["rsi"] = 100 - (100 / (1 + rs))

# MACD
ema12 = df["close"].ewm(span=12).mean()
ema26 = df["close"].ewm(span=26).mean()

df["macd"] = ema12 - ema26
df["signal"] = df["macd"].ewm(span=9).mean()

# =========================
# 🚀 SIGNAUX TEA
# =========================

df["buy"] = (
    (df["macd"] > df["signal"]) &
    (df["rsi"] > 40) &
    (df["close"] > df["ema20"])
)

df["sell"] = (
    (df["macd"] < df["signal"]) &
    (df["rsi"] < 60)
)

# =========================
# 🎯 FORMAT GRAPH
# =========================

candles = df[["time","open","high","low","close"]].to_dict("records")

ema = df[["time","ema20"]].rename(columns={"ema20":"value"}).to_dict("records")

# 🔥 MARKERS
markers = []

for i in range(len(df)):
    if df["buy"].iloc[i]:
        markers.append({
            "time": df["time"].iloc[i],
            "position": "belowBar",
            "color": "green",
            "shape": "arrowUp",
            "text": "BUY"
        })

    elif df["sell"].iloc[i]:
        markers.append({
            "time": df["time"].iloc[i],
            "position": "aboveBar",
            "color": "red",
            "shape": "arrowDown",
            "text": "SELL"
        })

# =========================
# 📊 CHART
# =========================

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

seriesCandlestickChart = {
    "type": "Candlestick",
    "data": candles,
    "markers": markers
}

seriesEMA = {
    "type": "Line",
    "data": ema,
    "options": {
        "color": "orange",
        "lineWidth": 2
    }
}

renderLightweightCharts([
    {
        "chart": chartOptions,
        "series": [seriesCandlestickChart, seriesEMA]
    }
], "chart")
