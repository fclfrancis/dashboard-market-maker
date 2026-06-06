"""
╔══════════════════════════════════════════════════════════════════╗
║   DASHBOARD INSTITUCIONAL MARKET MAKER                          ║
║   Engine: V9  |  Layout: Futurista / Cyberpunk HUD             ║
║   + Níveis Institucionais no Triple Pressure Map (timesat.py)  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import json, os, re, math, glob, io
import requests
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import yaml

# ══════════════════════════════════════════════════════════════════
# 0 · PÁGINA & CSS
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Dashboard Institucional Market Maker",
    layout="wide",
    initial_sidebar_state="expanded",
)
st_autorefresh(interval=60_000, key="mm_refresh")

HUD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
html, body, [class*="css"] { background: radial-gradient(circle at 20% 30%, #0a0c12, #030507) !important; color: #c5f5ef; font-family: 'JetBrains Mono', monospace; font-size: 13px; }
.stApp { background: radial-gradient(circle at 20% 30%, #0a0c12, #030507) !important; }
[data-testid="stAppViewContainer"] { background: radial-gradient(circle at 20% 30%, #0a0c12, #030507) !important; }
[data-testid="stHeader"] { background: rgba(3, 5, 7, 0.95) !important; }
[data-testid="stMain"] { background: transparent !important; }
section[data-testid="stMain"] > div { background: transparent !important; }
[data-testid="stSidebar"] { background: rgba(8, 12, 20, 0.85) !important; backdrop-filter: blur(12px); border-right: 1px solid rgba(0, 255, 255, 0.2); }
[data-testid="stSidebar"] * { color: #c5f5ef !important; font-size: 13px !important; }
[data-testid="stSidebar"] input { background: rgba(12, 18, 28, 0.8) !important; border: 1px solid rgba(0, 255, 255, 0.3) !important; color: #00ffe7 !important; font-size: 13px !important; }
[data-testid="stSidebar"] label { color: #0ff !important; font-size: 13px !important; letter-spacing: 1px; }
h1, h2, h3, .stMarkdown h1, .stMarkdown h2 { font-family: 'Inter', sans-serif; font-weight: 700; letter-spacing: -0.5px; background: linear-gradient(135deg, #FFFFFF 0%, #88AAFF 100%); -webkit-background-clip: text; background-clip: text; color: transparent; text-shadow: 0 0 8px rgba(136,170,255,0.3); }
.dashboard-card { background: rgba(12, 18, 28, 0.65); backdrop-filter: blur(8px); border: 1px solid rgba(0, 255, 255, 0.2); border-radius: 16px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 8px 20px rgba(0,0,0,0.5), 0 0 12px rgba(0, 255, 255, 0.1); transition: all 0.2s ease; }
.dashboard-card:hover { border-color: #0ff; box-shadow: 0 0 18px rgba(0, 255, 255, 0.3); background: rgba(12, 18, 28, 0.8); }
.kpi-card { background: rgba(12, 18, 28, 0.65); backdrop-filter: blur(8px); border: 1px solid rgba(0, 255, 255, 0.2); border-left: 3px solid #00ffe7; border-radius: 12px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.4), 0 0 8px rgba(0, 255, 255, 0.08); transition: all 0.2s ease; }
.kpi-card:hover { border-color: #0ff; box-shadow: 0 0 14px rgba(0, 255, 255, 0.25); }
.kpi-label { font-family: 'JetBrains Mono', monospace; font-size: 13px; letter-spacing: 2px; color: #0ff; text-shadow: 0 0 4px #0ff; text-transform: uppercase; margin-bottom: 4px; }
.kpi-value { font-family: 'JetBrains Mono', monospace; font-size: 22px; font-weight: 700; color: #f0f3fa; text-shadow: 0 0 5px rgba(0,255,255,0.5); letter-spacing: -0.5px; line-height: 1; }
.kpi-value.bull { color: #0f0; text-shadow: 0 0 10px rgba(0,255,0,0.5); }
.kpi-value.bear { color: #f44; text-shadow: 0 0 10px rgba(255,68,68,0.5); }
.kpi-value.neutral { color: #fa0; }
.kpi-sub { font-size: 13px; color: #8a9bb5; margin-top: 4px; }
.sec-header { font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 700; letter-spacing: 3px; color: #0ff; text-shadow: 0 0 4px #0ff; border-bottom: 1px solid rgba(0, 255, 255, 0.2); padding-bottom: 6px; margin: 18px 0 10px 0; text-transform: uppercase; }
.sec-header::before { content: "◈  "; color: rgba(0,255,255,0.5); }
.alert-success { background: rgba(0,255,0,0.08); border: 1px solid rgba(0,255,0,0.4); border-left: 4px solid #0f0; border-radius: 8px; padding: 10px 14px; font-size: 13px; color: #0f0; margin: 8px 0; font-family: 'JetBrains Mono', monospace; }
.alert-warning { background: rgba(255,165,0,0.08); border: 1px solid rgba(255,165,0,0.4); border-left: 4px solid #fa0; border-radius: 8px; padding: 10px 14px; font-size: 13px; color: #fa0; margin: 8px 0; font-family: 'JetBrains Mono', monospace; }
.alert-danger { background: rgba(255,68,68,0.08); border: 1px solid rgba(255,68,68,0.4); border-left: 4px solid #f44; border-radius: 8px; padding: 10px 14px; font-size: 13px; color: #f44; margin: 8px 0; font-family: 'JetBrains Mono', monospace; }
.alert-info { background: rgba(0,255,231,0.06); border: 1px solid rgba(0,255,231,0.3); border-left: 4px solid #0ff; border-radius: 8px; padding: 10px 14px; font-size: 13px; color: #0ff; margin: 8px 0; font-family: 'JetBrains Mono', monospace; }
.hud-table { width:100%; border-collapse:collapse; font-family:'JetBrains Mono',monospace; font-size:13px; }
.hud-table th { color:#0ff; text-shadow:0 0 3px #0ff; text-align:left; font-size:13px; letter-spacing:1.5px; border-bottom:1px solid rgba(0,255,255,0.3); padding:6px 8px; text-transform:uppercase; }
.hud-table td { padding:7px 8px; border-bottom:1px solid rgba(255,255,255,0.04); color:#ccddf8; font-size:13px; }
.hud-table tr:hover td { background: rgba(0,255,255,0.04); }
.tt-table { width:100%; border-collapse:collapse; font-family:'JetBrains Mono',monospace; font-size:13px; }
.tt-table th { color:#0ff; text-shadow:0 0 3px #0ff; text-align:left; font-size:13px; letter-spacing:1.5px; border-bottom:1px solid rgba(0,255,255,0.3); padding:7px 8px; text-transform:uppercase; background:rgba(0,0,0,0.3); }
.tt-table td { padding:6px 8px; border-bottom:1px solid rgba(255,255,255,0.04); color:#ccddf8; font-size:13px; }
.tt-table tr:hover td { background: rgba(0,255,255,0.04); }
.tt-buy { color:#0f0 !important; font-weight:bold; text-shadow:0 0 3px #0f0; }
.tt-sell { color:#f44 !important; font-weight:bold; text-shadow:0 0 3px #f44; }
.tt-bruto { color:#666 !important; }
.tt-mm-buy { color:#0af !important; }
.tt-mm-sell { color:#fa6 !important; }
.tt-mm-neu { color:#666 !important; }
.tt-pos { color:#0f0 !important; text-shadow:0 0 3px #0f0; }
.tt-neg { color:#f44 !important; text-shadow:0 0 3px #f44; }
.whale-card { background: rgba(12,18,28,0.65); border:1px solid rgba(0,255,255,0.15); border-radius:8px; padding:8px 12px; margin-bottom:6px; font-size:13px; font-family:'JetBrains Mono',monospace; }
.tag { padding:2px 8px; border-radius:20px; font-size:13px; font-weight:700; font-family:'JetBrains Mono',monospace; background:rgba(0,0,0,0.5); backdrop-filter:blur(4px); border:1px solid; }
.tag-bull { background:rgba(0,255,0,0.12); color:#0f0; border-color:#0f0; box-shadow:0 0 5px #0f0; }
.tag-bear { background:rgba(255,50,50,0.12); color:#f44; border-color:#f44; box-shadow:0 0 5px #f44; }
.tag-neutral { background:rgba(255,165,0,0.12); color:#fa0; border-color:#fa0; box-shadow:0 0 5px #fa0; }
.text-green { color:#0f0; text-shadow:0 0 3px #0f0; }
.text-red { color:#f44; text-shadow:0 0 3px #f44; }
.text-cyan { color:#0ff; text-shadow:0 0 3px #0ff; }
.text-dim { color:#8a9bb5; font-size:13px; letter-spacing:0.5px; }
.text-gold { color:#fa0; text-shadow:0 0 3px #fa0; }
.glow-divider { height:1px; background:linear-gradient(90deg, transparent, #0ff, #0ff, transparent); margin:12px 0; }
body::after { content:""; position:fixed; top:0; left:0; width:100vw; height:100vh; background: repeating-linear-gradient(0deg, rgba(0,255,255,0.015) 0px, rgba(0,255,255,0.015) 2px, transparent 2px, transparent 6px); pointer-events:none; z-index:9999; }
.js-plotly-plot .plotly .main-svg { background:transparent !important; }
.plotly .modebar { filter:drop-shadow(0 0 4px #0ff); }
div[data-testid="stNumberInput"] input, div[data-testid="stTextInput"] input { background:rgba(12,18,28,0.8) !important; border:1px solid rgba(0,255,255,0.2) !important; color:#00ffe7 !important; font-family:'JetBrains Mono',monospace !important; border-radius:6px !important; font-size:13px !important; }
.stSelectbox > div > div { background:rgba(12,18,28,0.8) !important; border:1px solid rgba(0,255,255,0.2) !important; color:#00ffe7 !important; border-radius:6px !important; font-size:13px !important; }
.stDownloadButton button { background:linear-gradient(90deg, #0a2b3a, #02131c); border:1px solid #0ff; border-radius:40px; color:#0ff; font-family:'JetBrains Mono',monospace; transition:0.2s; font-size:13px !important; }
.stDownloadButton button:hover { box-shadow:0 0 12px #0ff; border-color:#0ff; color:#fff; }
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:rgba(3,5,7,0.8); }
::-webkit-scrollbar-thumb { background:rgba(0,255,255,0.3); border-radius:2px; }
::-webkit-scrollbar-thumb:hover { background:#0ff; }
hr { border-color:rgba(0,255,255,0.15) !important; }
</style>
"""
st.markdown(HUD_CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# CONSTANTES GITHUB + FUNÇÕES DE CARGA (nível de módulo)
# ══════════════════════════════════════════════════════════════════
GITHUB_USER   = "fclfrancis"
GITHUB_REPO   = "dashboard-market-maker"
GITHUB_BRANCH = "main"
GITHUB_PASTA  = "dados"
API_URL  = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PASTA}?ref={GITHUB_BRANCH}"
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{GITHUB_PASTA}"

def _gh_headers():
    headers = {}
    try:
        token = st.secrets["GITHUB_TOKEN"]
        if token:
            headers["Authorization"] = f"token {token}"
    except Exception:
        pass
    return headers

@st.cache_data(ttl=300)
def carregar_emails_autorizados():
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/config.yaml"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            cfg = yaml.safe_load(r.text)
            return [e.lower().strip() for e in cfg.get("emails_autorizados", [])]
    except Exception:
        pass
    return []

@st.cache_data(ttl=300)
def listar_arquivos_github():
    try:
        r = requests.get(API_URL, headers=_gh_headers(), timeout=10)
        if r.status_code == 200:
            return [f["name"] for f in r.json() if f["name"].endswith(".json")]
        else:
            st.error(f"GitHub API {r.status_code}: {r.text[:200]}")
    except Exception as e:
        st.error(f"Erro listar: {e}")
    return []

@st.cache_data(ttl=60)
def baixar_json_github(nome_arquivo):
    url = f"{RAW_BASE}/{nome_arquivo}"
    try:
        r = requests.get(url, headers=_gh_headers(), timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

# ══════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════
def tela_login():
    st.markdown("<div style='max-width:420px;margin:80px auto 0;'><div class='dashboard-card' style='padding:32px;text-align:center;'><div style='font-family:Inter,sans-serif;font-size:22px;font-weight:700;background:linear-gradient(135deg,#fff,#88aaff);-webkit-background-clip:text;background-clip:text;color:transparent;margin-bottom:8px;'>📡 MARKET MAKER</div><div style='color:#4a7a75;font-size:13px;letter-spacing:2px;margin-bottom:28px;'>DASHBOARD INSTITUCIONAL · V9</div></div></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        email_input = st.text_input("📧 Seu email:", placeholder="seuemail@exemplo.com", key="login_email")
        entrar = st.button("ENTRAR", use_container_width=True)
        if entrar:
            email = email_input.lower().strip()
            autorizados = carregar_emails_autorizados()
            if email and email in autorizados:
                st.session_state["email_logado"] = email; st.rerun()
            elif email:
                st.markdown("<div class='alert-danger'>❌ Email não autorizado.</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='alert-warning'>⚠ Digite seu email.</div>", unsafe_allow_html=True)
    st.stop()

if "email_logado" not in st.session_state:
    tela_login()

with st.sidebar:
    st.markdown(f"<div style='font-size:13px;color:#4a7a75;margin-bottom:8px;'>✅ {st.session_state['email_logado']}</div>", unsafe_allow_html=True)
    if st.button("🚪 Sair", use_container_width=True):
        del st.session_state["email_logado"]; st.rerun()
    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 1 · CONSTANTES
# ══════════════════════════════════════════════════════════════════
LAST_STALE_THRESHOLD = 0.85
MULTIPLICADOR_FIXO   = 100          # ← fixo, não exposto ao usuário
COLOR_CALL   = "#FF3131"
COLOR_PUT    = "#00FF00"
COLOR_NEON   = "#00ffe7"
COLOR_PURPLE = "#7b2fff"
COLOR_ORANGE = "#ff6b35"
COLOR_GOLD   = "#f0c040"

# ══════════════════════════════════════════════════════════════════
# 2 · HELPERS
# ══════════════════════════════════════════════════════════════════
def fmt_M(v):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))): return "—"
    a = abs(v); sign = "-" if v < 0 else "+"
    return f"{sign}{a/1e3:.1f}K" if a < 1e6 else f"{sign}{a/1e6:.1f}M"

def kpi(label, value, cls="", sub=""):
    return (f"<div class='kpi-card'><div class='kpi-label'>{label}</div>"
            f"<div class='kpi-value {cls}'>{value}</div>"
            f"<div class='kpi-sub'>{sub}</div></div>")

def alert_box(msg, kind="info"):
    return f"<div class='alert-{kind}'>{msg}</div>"

def section(title):
    st.markdown(f"<div class='sec-header'>{title}</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 3 · AGRUPAMENTO
# ══════════════════════════════════════════════════════════════════
def agrupar_snapshots(caminhos):
    snapshots = {}
    for caminho in caminhos:
        nome = os.path.basename(caminho)
        match = re.search(r"(\d{4}-\d{2}-\d{2})", nome)
        chave = match.group(1) if match else nome.rsplit(".", 1)[0]
        snapshots.setdefault(chave, []).append(caminho)
    return dict(sorted(snapshots.items(), reverse=True))

# ══════════════════════════════════════════════════════════════════
# 4 · PARSER JSON
# ══════════════════════════════════════════════════════════════════
def _clean_num(x):
    if x is None: return 0.0
    try:
        s = str(x).strip().replace(",", "").replace("N/A", "0")
        return float(s) if s not in ("", "None", "null", "nan") else 0.0
    except: return 0.0

def _fmt_strike(v):
    if v == 0: return "0"
    if abs(v) < 100: return f"{v:.5f}".rstrip("0").rstrip(".")
    return f"{v:,.0f}"

def parse_json(source):
    try:
        if hasattr(source, "read"):
            source.seek(0); js = json.load(source)
        else:
            with open(source, "r", encoding="utf-8") as fh: js = json.load(fh)
    except Exception as e:
        st.warning(f"Erro ao abrir {getattr(source, 'name', source)}: {e}"); return None

    data_block = js.get("data", {}); records = []

    if isinstance(data_block, dict) and ("Call" in data_block or "Put" in data_block):
        for opt_type in ("Call", "Put"):
            for row in data_block.get(opt_type, []):
                raw = row.get("raw", row)
                raw["_opt_type"]   = opt_type
                raw["_strike_str"] = str(raw.get("strikePrice", raw.get("strike", "0")))
                records.append(raw)
    elif isinstance(data_block, dict):
        key = list(data_block.keys())[0] if data_block else ""
        rows = data_block.get(key, [])
        if not isinstance(rows, list): rows = []
        for row in rows:
            raw = row.get("raw", row)
            strike_str = str(row.get("strike", raw.get("strike", "")))
            raw["_opt_type"]     = "Call" if strike_str.upper().endswith("C") else "Put"
            raw["_strike_str"]   = strike_str
            if "tradeTime" not in raw and "tradeTime" in row:
                raw["tradeTime"] = row["tradeTime"]
            records.append(raw)
    elif isinstance(data_block, list):
        for row in data_block:
            raw = row.get("raw", row)
            strike_str = str(row.get("strike", raw.get("strike", "")))
            raw["_opt_type"]     = "Call" if strike_str.upper().endswith("C") else "Put"
            raw["_strike_str"]   = strike_str
            records.append(raw)

    if not records: return None
    df = pd.DataFrame(records)

    def _parse_strike(row):
        s = str(row.get("_strike_str", row.get("strikePrice", row.get("strike", "0"))))
        s = re.sub(r"[CPcp]$", "", s.replace(",", "").strip())
        try: return float(s)
        except: return 0.0

    df["strikePrice"] = df.apply(_parse_strike, axis=1)
    df["optionType"]  = df["_opt_type"]
    for col in ["strikePrice","bidPrice","askPrice","lastPrice","volume","openInterest","delta","gamma","vega","theta"]:
        df[col] = df[col].apply(_clean_num) if col in df.columns else 0.0
    if "tradeTime" in df.columns:
        df["tradeTime"] = pd.to_numeric(df["tradeTime"], errors="coerce")
        df["tradeTime"] = pd.to_datetime(df["tradeTime"], unit="s", errors="coerce")
    df = df[df["strikePrice"] > 0].copy()
    return df if not df.empty else None

# ══════════════════════════════════════════════════════════════════
# 5 · ENGINE V9
# ══════════════════════════════════════════════════════════════════
def calcular_v9(df_raw, spot, s_min, s_max, min_fin, mult=100.0):
    df = df_raw.copy()
    df = df[(df["strikePrice"] >= s_min) & (df["strikePrice"] <= s_max)].copy()
    df = df[df["volume"] > 0].copy()
    if df.empty: return df
    records = []
    for _, row in df.iterrows():
        last=_clean_num(row.get("lastPrice",0)); bid=_clean_num(row.get("bidPrice",0)); ask=_clean_num(row.get("askPrice",0))
        delta=_clean_num(row.get("delta",0)); gamma=_clean_num(row.get("gamma",0)); vega=_clean_num(row.get("vega",0))
        vol=_clean_num(row.get("volume",0)); oi=_clean_num(row.get("openInterest",0)); sp=_clean_num(row.get("strikePrice",0))
        opt=row.get("optionType","Call"); ttime=row.get("tradeTime",pd.NaT)
        bid_ask_ok=bid>0 and ask>0; mid_price=(bid+ask)/2 if bid_ask_ok else last
        fin_opc=mid_price*vol*mult
        if min_fin>0 and fin_opc<min_fin: continue
        last_ok=bid_ask_ok and last>0 and (last>=bid*LAST_STALE_THRESHOLD)
        last_only=not bid_ask_ok and last>0
        if last_ok: direction=1 if last>=mid_price else -1; side="BUY" if direction==1 else "SELL"
        elif bid_ask_ok: direction=0; side="BRUTO_STALE"
        elif last_only: direction=1; side="LAST_ONLY"
        else: direction=0; side="BRUTO_NOBID"
        greeks_ok=not(delta==0 and gamma==0 and vega==0 and sp!=spot); opt_sign=1 if opt=="Call" else -1
        d_flow=delta*vol*mult*spot*direction; dex_total=d_flow
        gex_total=gamma*vol*mult*(spot**2)*opt_sign*direction if greeks_ok and direction!=0 else 0.0
        g_flow=gex_total
        vanna_total=(delta*vega/spot)*vol*mult*direction*opt_sign if greeks_ok and spot>0 and direction!=0 else 0.0
        v_flow=vanna_total; fin_flow=mid_price*vol*mult
        dex_oi=delta*oi*mult*spot*opt_sign
        gex_oi=gamma*oi*mult*(spot**2)*opt_sign if greeks_ok else 0.0
        vanna_oi=(delta*vega/spot)*oi*mult*opt_sign if greeks_ok and spot>0 else 0.0
        if gex_total>0: acao_mm="BUY"
        elif gex_total<0: acao_mm="SELL"
        else: acao_mm="NEUTRO"
        records.append({
            "Horário":ttime,"strikePrice":sp,"Strike":f"{_fmt_strike(sp)}{opt[0]}","optionType":opt,
            "Lado":side,"volume":vol,"Vol":int(vol),"openInterest":oi,"delta":delta,"gamma":gamma,"vega":vega,
            "lastPrice":last,"bidPrice":bid,"askPrice":ask,"Fin_Opc":fin_opc,"Acao_MM":acao_mm,"side":side,
            "direction":direction,"greeks_ok":greeks_ok,"d_flow":d_flow,"g_flow":g_flow,"v_flow":v_flow,
            "financial_flow":fin_flow,"gex_total":gex_total,"dex_total":dex_total,"vanna_total":vanna_total,
            "dex_oi":dex_oi,"gex_oi":gex_oi,"vanna_oi":vanna_oi,
        })
    return pd.DataFrame(records) if records else pd.DataFrame()

def detectar_spot(df, spot_manual=None):
    if spot_manual and spot_manual>0: return float(spot_manual)
    calls=df[df["optionType"]=="Call"].copy()
    if calls.empty: return 0.0
    valid=calls[calls["delta"].between(0.01,0.99)]
    if valid.empty: return float(calls["strikePrice"].median())
    idx=(valid["delta"]-0.5).abs().idxmin(); return float(valid.loc[idx,"strikePrice"])

def _detectar_spot_pcp(df):
    try:
        by_strike={}
        for _,row in df.iterrows():
            sk=float(row.get("strikePrice",0)); bid=float(row.get("bidPrice",0) or 0)
            ask=float(row.get("askPrice",0) or 0); d=float(row.get("delta",0) or 0)
            opt=row.get("optionType","")
            if sk<=0 or bid<=0 or ask<=0: continue
            by_strike.setdefault(sk,{})
            if opt=="Call": by_strike[sk]["call"]={"mid":(bid+ask)/2,"delta":abs(d)}
            elif opt=="Put": by_strike[sk]["put"]={"mid":(bid+ask)/2}
        estimates=[]
        for sk,sides in by_strike.items():
            c=sides.get("call"); p=sides.get("put")
            if not c or not p: continue
            F=sk+c["mid"]-p["mid"]; weight=1.0/(abs(c["delta"]-0.5)+0.001)
            estimates.append((F,weight))
        if not estimates: return 0.0
        total_w=sum(w for _,w in estimates)
        return sum(F*w for F,w in estimates)/total_w
    except: return 0.0

def calcular_pcp_detalhado(df):
    resultado={"spot_implicito":0.0,"strike_atm":0.0,"c_bid":0.0,"c_ask":0.0,"c_mid":0.0,
               "p_bid":0.0,"p_ask":0.0,"p_mid":0.0,"diferenca":0.0,"delta_call_atm":None,
               "delta_flip_abaixo":None,"delta_flip_acima":None,"tabela":[]}
    try:
        by_strike={}
        for _,row in df.iterrows():
            sk=float(row.get("strikePrice",0) or 0); bid=float(row.get("bidPrice",0) or 0)
            ask=float(row.get("askPrice",0) or 0); d=float(row.get("delta",0) or 0)
            opt=row.get("optionType","")
            if sk<=0 or bid<=0 or ask<=0: continue
            by_strike.setdefault(sk,{})
            if opt=="Call": by_strike[sk]["call"]={"bid":bid,"ask":ask,"mid":(bid+ask)/2,"delta":abs(d)}
            elif opt=="Put": by_strike[sk]["put"]={"bid":bid,"ask":ask,"mid":(bid+ask)/2}
        estimates=[]
        for sk,sides in by_strike.items():
            c=sides.get("call"); p=sides.get("put")
            if not c or not p: continue
            F=sk+c["mid"]-p["mid"]; weight=1.0/(abs(c["delta"]-0.5)+0.001)
            estimates.append({"K":sk,"c_bid":c["bid"],"c_ask":c["ask"],"c_mid":c["mid"],
                              "p_bid":p["bid"],"p_ask":p["ask"],"p_mid":p["mid"],
                              "F":F,"weight":weight,"delta_call":c["delta"]})
        if not estimates: return resultado
        total_w=sum(e["weight"] for e in estimates)
        spot_pond=sum(e["F"]*e["weight"] for e in estimates)/total_w
        best=min(estimates,key=lambda e:abs(e["delta_call"]-0.5))
        near=sorted(sorted(estimates,key=lambda e:abs(e["delta_call"]-0.5))[:12],key=lambda e:e["K"])
        strikes_sorted=sorted(estimates,key=lambda e:e["K"])
        flip_abaixo=flip_acima=None
        for i in range(len(strikes_sorted)-1):
            a=strikes_sorted[i]; b=strikes_sorted[i+1]
            if a["delta_call"]>=0.50 and b["delta_call"]<0.50:
                flip_abaixo=a["K"]; flip_acima=b["K"]; break
        resultado.update({"spot_implicito":spot_pond,"strike_atm":best["K"],
            "c_bid":best["c_bid"],"c_ask":best["c_ask"],"c_mid":best["c_mid"],
            "p_bid":best["p_bid"],"p_ask":best["p_ask"],"p_mid":best["p_mid"],
            "diferenca":best["c_mid"]-best["p_mid"],"delta_call_atm":best["delta_call"],
            "delta_flip_abaixo":flip_abaixo,"delta_flip_acima":flip_acima,"tabela":near})
    except: pass
    return resultado

# ══════════════════════════════════════════════════════════════════
# 5.1 · NÍVEIS INSTITUCIONAIS (port do timesat.py)
# ══════════════════════════════════════════════════════════════════
def _zero_cross(xs, ys):
    xs = np.asarray(xs, float); ys = np.asarray(ys, float)
    if len(ys) == 0:
        return None
    for i in range(1, len(ys)):
        if np.sign(ys[i]) != np.sign(ys[i-1]):
            y0, y1 = ys[i-1], ys[i]
            if y1 != y0:
                return float(xs[i-1] - y0 * (xs[i] - xs[i-1]) / (y1 - y0))
    return float(xs[np.nanargmin(np.abs(ys))])

def calcular_niveis_institucionais(df_raw, spot, s_min, s_max, mult=100.0):
    """Retorna dict de níveis estruturais para overlay no Triple Pressure Map.

    GEX subplot: VOL Trigger, Γ+ OI, Γ- OI (= VOL Attack), Γ+ Vol, Γ- Vol
    DEX subplot: Δ Flip, Δ+ OI, Δ- OI, Δ+ Vol, Δ- Vol
    """
    d = df_raw[(df_raw["strikePrice"] >= s_min) & (df_raw["strikePrice"] <= s_max)].copy()
    if d.empty or spot <= 0:
        return {}

    SG = (spot ** 2) * 0.01
    SD = spot
    d["Sign"]    = np.where(d["optionType"] == "Call", 1, -1)
    d["GEX_OI"]  = d["gamma"] * d["openInterest"] * mult * SG * d["Sign"]
    d["GEX_VOL"] = d["gamma"] * d["volume"]       * mult * SG * d["Sign"]
    d["DEX_OI"]  = d["delta"] * d["openInterest"] * mult * SD
    d["DEX_VOL"] = d["delta"] * d["volume"]       * mult * SD

    per = d.groupby("strikePrice").agg(
        GEX_OI=("GEX_OI","sum"),  GEX_VOL=("GEX_VOL","sum"),
        DEX_OI=("DEX_OI","sum"),  DEX_VOL=("DEX_VOL","sum"),
    ).sort_index()
    if per.empty:
        return {}

    # ── Curva GEX OI suavizada → Gamma Pos/Neg (OI) + VOL Trigger ──
    xs = per.index.to_numpy(float)
    ys = per["GEX_OI"].rolling(5, center=True, min_periods=1).mean().to_numpy(float)
    i_max, i_min = int(np.nanargmax(ys)), int(np.nanargmin(ys))
    gamma_pos_oi = float(xs[i_max])
    gamma_neg_oi = float(xs[i_min])          # = VOL Attack
    zf = _zero_cross(xs, ys)
    x_dom = gamma_pos_oi if abs(ys[i_max]) >= abs(ys[i_min]) else gamma_neg_oi
    vol_trigger = float(zf + 0.75 * (x_dom - zf)) if zf is not None else None

    # ── Delta Flip: zero-cross do DEX OI líquido ──
    delta_flip = _zero_cross(per.index.to_numpy(float), per["DEX_OI"].to_numpy(float))

    def _safe(v):
        try:
            v = float(v)
            return v if not (np.isnan(v) or np.isinf(v)) else None
        except:
            return None

    return {
        # GEX subplot (col 2)
        "VOL Trigger":                    _safe(vol_trigger),
        "Gamma Pos.OI":                   _safe(gamma_pos_oi),
        "Gamma Neg. OI | VOL Attack":     _safe(gamma_neg_oi),
        "Gamma Pos. Vol":                 _safe(per["GEX_VOL"].idxmax()),
        "Gamma Neg. OIVol":               _safe(per["GEX_VOL"].idxmin()),
        # DEX subplot (col 1)
        "Delta Flip":                     _safe(delta_flip),
        "Delta Pos. OI":                  _safe(per["DEX_OI"].idxmax()),
        "Delta Neg. OI":                  _safe(per["DEX_OI"].idxmin()),
        "Delta Pos.Vol":                  _safe(per["DEX_VOL"].idxmax()),
        "Delta Neg. Vol":                 _safe(per["DEX_VOL"].idxmin()),
    }

# ══════════════════════════════════════════════════════════════════
# 6 · INTELIGÊNCIA
# ══════════════════════════════════════════════════════════════════
def processar_inteligencia(df, spot, threshold=2.5):
    if df is None or df.empty: return None, 0.0
    std=df["d_flow"].std(); df=df.copy()
    df["z_score"]=(df["d_flow"]-df["d_flow"].mean())/std if std>0 else 0.0
    whales=df[df["z_score"].abs()>threshold].copy(); net_delta=df["d_flow"].sum()
    gex_by_s=df.groupby("strikePrice")["gex_total"].sum().sort_index()
    gex_vals=gex_by_s.values; gex_idx=gex_by_s.index.tolist(); gamma_flip=0.0
    for i in range(len(gex_vals)-1):
        if gex_vals[i]*gex_vals[i+1]<0:
            k0,k1=gex_idx[i],gex_idx[i+1]; g0,g1=gex_vals[i],gex_vals[i+1]
            gamma_flip=k0+(k1-k0)*(-g0)/(g1-g0); break
    if gamma_flip==0.0 and not gex_by_s.empty: gamma_flip=float(gex_by_s.abs().idxmin())
    if   spot>gamma_flip and net_delta>0: stat,msg="success","🔥 ALTA CONVICÇÃO (Safe Zone) — MMs provêm liquidez para a subida."
    elif spot<gamma_flip and net_delta>0: stat,msg="warning",f"🚀 RISCO DE SQUEEZE! MMs precisam cobrir Delta acima de {_fmt_strike(gamma_flip)}"
    elif spot<gamma_flip and net_delta<0: stat,msg="danger","💀 CASCATA (Falling Knife) — Zona de aceleração negativa. Evite compras."
    else:                                 stat,msg="info","⚖️ MERCADO EM EQUILÍBRIO / CONSOLIDAÇÃO — Aguarde confirmação."
    return {"whales":whales,"msg":msg,"status":stat,"net_delta":net_delta,"z_score":df["z_score"]},gamma_flip

# ══════════════════════════════════════════════════════════════════
# 7 · LEGENDAS CONTEXTUAIS
# ══════════════════════════════════════════════════════════════════
def legenda_dex_ctx(valor,serie,strike,spot):
    p75=serie.abs().quantile(0.75); p90=serie.abs().quantile(0.90)
    alto=abs(valor)>p90; medio=abs(valor)>p75; pos=valor>=0; abaixo=strike<spot
    if pos and alto:   return ("🟢 COMPRA INTENSA","MM muito comprado nesse nível. Age como piso forte." if abaixo else "Fluxo comprador intenso acima do spot. Possível squeeze de alta.")
    elif pos and medio:return ("🟢 PRESSÃO COMPRADORA","MM comprado em delta. Tende a sustentar o preço." if abaixo else "Demanda acima do spot. MM favorece continuação de alta.")
    elif pos:          return "🔵 LEVE COMPRA","Fluxo comprador moderado. Sem força direcional expressiva."
    elif not pos and alto:  return ("🔴 VENDA INTENSA","Fluxo vendedor intenso abaixo do spot. Risco de cascade." if abaixo else "MM muito vendido acima do spot. Age como teto forte.")
    elif not pos and medio: return ("🔴 PRESSÃO VENDEDORA","Fluxo vendedor abaixo do spot. MM favorece queda." if abaixo else "MM vendido em delta. Tende a pressionar o preço para baixo.")
    else: return "🔵 LEVE VENDA","Fluxo vendedor moderado. Sem força direcional expressiva."

def legenda_gex_ctx(valor,serie,strike,spot):
    p75=serie.abs().quantile(0.75); p90=serie.abs().quantile(0.90)
    alto=abs(valor)>p90; medio=abs(valor)>p75; pos=valor>=0
    if pos and alto:        return "🛡️ DEFESA MÁXIMA","MM vai travar o preço aqui. Rompimento requer volume institucional forte."
    elif pos and medio:     return "🛡️ DEFESA FORTE","MM amortece o movimento. Difícil de romper."
    elif pos:               return "🔵 DEFESA LEVE","Alguma defesa do MM. Strike pode ser testado sem grande resistência."
    elif not pos and alto:  return "🚨 RUPTURA MÁXIMA","MM vai amplificar o movimento. Rompimento rápido e forte esperado."
    elif not pos and medio: return "⚠️ ZONA DE RUPTURA","MM pode acelerar o movimento. Evitar contra-tendência."
    else: return "🌀 ZONA NEUTRA","MM sem posição relevante. Strike pode ser cruzado sem grande reação."

def legenda_vanna_ctx(valor,serie,strike,spot):
    p75=serie.abs().quantile(0.75); p90=serie.abs().quantile(0.90)
    alto=abs(valor)>p90; medio=abs(valor)>p75; pos=valor>=0
    if pos and alto:        return "⚡ VANNA MÁXIMO+","Strike muito sensível à IV. Se vol subir, MM compra delta — favorece alta."
    elif pos and medio:     return "⚡ VANNA ALTO+","Aumento de IV empurra MM a comprar delta nesse nível."
    elif pos:               return "🔵 VANNA LEVE+","Pequena sensibilidade positiva à vol. Efeito direcional limitado."
    elif not pos and alto:  return "⚡ VANNA MÁXIMO−","Strike muito sensível à IV. Se vol subir, MM vende delta — favorece baixa."
    elif not pos and medio: return "⚡ VANNA ALTO−","Aumento de IV empurra MM a vender delta nesse nível."
    else: return "🔵 VANNA LEVE−","Pequena sensibilidade negativa à vol. Efeito direcional limitado."

# ══════════════════════════════════════════════════════════════════
# 8 · GRÁFICO TERMINAL — VOL e OI
# ══════════════════════════════════════════════════════════════════
def build_main_chart(df, strikes_agg, spot):
    sy_num=sorted(df["strikePrice"].unique()); sy_lbl=[_fmt_strike(s) for s in sy_num]
    num2lbl={n:l for n,l in zip(sy_num,sy_lbl)}
    oi_col="openInterest" if "openInterest" in df.columns else "volume"
    agg_cp=(df.groupby(["strikePrice","optionType"]).agg(volume=("volume","sum"),open_interest=(oi_col,"sum")).reset_index())
    def get_cp(metric,opt):
        d=agg_cp[agg_cp["optionType"]==opt].set_index("strikePrice").reindex(sy_num).fillna(0)
        v=d[metric].values; return -v if opt=="Put" else v
    def cp_colors(metric,opt):
        d=agg_cp[agg_cp["optionType"]==opt].set_index("strikePrice").reindex(sy_num).fillna(0)
        v=d[metric].values
        if opt=="Put": v=-v
        base=COLOR_CALL if opt=="Call" else COLOR_PUT; mx=float(np.abs(v).max()) if len(v)>0 else 0.0
        return [COLOR_GOLD if(mx>0 and abs(x)==mx) else base for x in v]
    fig=make_subplots(rows=1,cols=2,shared_yaxes=True,column_widths=[0.50,0.50],
        subplot_titles=["VOLUME  (Call +  |  Put −)","OPEN INTEREST  (Call +  |  Put −)"],horizontal_spacing=0.04)
    for metric,col_idx in [("volume",1),("open_interest",2)]:
        for opt in ["Call","Put"]:
            name=f"{'Vol' if metric=='volume' else 'OI'} {opt}"
            vals_raw=get_cp(metric,opt); serie_abs=pd.Series(np.abs(vals_raw))
            legendas_niveis=[]; legendas_descs=[]
            for i,(sk,xv) in enumerate(zip(sy_num,vals_raw)):
                acima=sk>spot; oi_v=float(serie_abs.iloc[i])
                p75=serie_abs.quantile(0.75); p90=serie_abs.quantile(0.90)
                if metric=="open_interest":
                    if opt=="Call":
                        if acima: nv="⛔ Resistência" if oi_v>p75 else "🔵 OTM Fraca"; dc="Call OTM acima do spot. MM vai vender delta se preço subir."
                        else: nv="🟢 Suporte" if oi_v>p75 else "🔵 ITM Fraca"; dc="Call ITM abaixo do spot. MM já comprou futuros para hedge."
                    else:
                        if not acima: nv="🟢 Suporte" if oi_v>p75 else "🔵 OTM Fraca"; dc="Put OTM abaixo do spot. MM vai comprar futuros se preço cair."
                        else: nv="⛔ Pressão Vend." if oi_v>p75 else "🔵 ITM Fraca"; dc="Put ITM acima do spot. MM já vendeu futuros para hedge."
                else: nv="📊 Volume"; dc=f"Volume de {opt} nesse strike."
                legendas_niveis.append(nv); legendas_descs.append(dc)
            customdata=np.array(list(zip(legendas_niveis,legendas_descs,np.abs(vals_raw))))
            fig.add_trace(go.Bar(y=sy_lbl,x=vals_raw,orientation="h",marker_color=cp_colors(metric,opt),name=name,
                customdata=customdata,hovertemplate=(f"<b>Strike: %{{y}}</b><br>{'Vol' if metric=='volume' else 'OI'}: %{{x:,.0f}}<br>──────────────────<br>%{{customdata[0]}}<br><i>%{{customdata[1]}}</i><extra>{name}</extra>")),row=1,col=col_idx)
    spot_lbl=num2lbl.get(spot) or _fmt_strike(min(sy_num,key=lambda s:abs(s-spot)))
    def cat_hline(lbl,color,dash,annotation,ci,width=2.0):
        xref=f"x{ci if ci>1 else ''}"; fig.add_shape(type="line",x0=0,x1=1,xref=f"{xref} domain",y0=lbl,y1=lbl,yref="y",line=dict(color=color,width=width,dash="dashdot" if dash=="longdash" else dash),row=1,col=ci)
        if annotation: fig.add_annotation(x=1,xref=f"{xref} domain",y=lbl,yref="y",text=annotation,showarrow=False,xanchor="right",yanchor="bottom",yshift=4,font=dict(color=color,size=13,family="JetBrains Mono"),row=1,col=ci)
    cat_hline(spot_lbl,COLOR_NEON,"dash",f"SPOT {_fmt_strike(spot)}",1,width=2.5)
    cat_hline(spot_lbl,COLOR_NEON,"dash",f"SPOT {_fmt_strike(spot)}",2,width=2.5)
    agg_vc=agg_cp[agg_cp["optionType"]=="Call"].set_index("strikePrice")["volume"]
    agg_vp=agg_cp[agg_cp["optionType"]=="Put"].set_index("strikePrice")["volume"]
    agg_oc=agg_cp[agg_cp["optionType"]=="Call"].set_index("strikePrice")["open_interest"]
    agg_op=agg_cp[agg_cp["optionType"]=="Put"].set_index("strikePrice")["open_interest"]
    for series,color,label,ci in [(agg_vc,COLOR_CALL,"Call Vol Wall",1),(agg_vp,COLOR_PUT,"Put Vol Wall",1),(agg_oc,COLOR_CALL,"Call OI Wall",2),(agg_op,COLOR_PUT,"Put OI Wall",2)]:
        if not series.empty:
            sk=float(series.idxmax()); lbl=num2lbl.get(sk,_fmt_strike(sk)); cat_hline(lbl,color,"dot",label,ci)
    fig.update_layout(height=900,template="plotly_dark",barmode="relative",showlegend=False,margin=dict(t=50,b=20,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(8,12,20,0.6)",font=dict(family="JetBrains Mono",size=13,color="#ccddf8"),
        hoverlabel=dict(font_size=14,font_family="JetBrains Mono",bgcolor="#0a1a20",bordercolor="#00ffe7"))
    for ci in range(1,3):
        fig.update_xaxes(showgrid=True,gridcolor="rgba(0,255,255,0.06)",zerolinecolor="rgba(0,255,255,0.4)",zerolinewidth=1.5,tickfont=dict(size=13,family="JetBrains Mono"),row=1,col=ci)
    fig.update_yaxes(showgrid=True,gridcolor="rgba(0,255,255,0.06)",tickfont=dict(size=13,family="JetBrains Mono"),row=1,col=1)
    for ann in fig.layout.annotations: ann.font.color=COLOR_NEON; ann.font.size=13; ann.font.family="Inter, sans-serif"
    return fig

# ══════════════════════════════════════════════════════════════════
# 9 · GRÁFICO TRIPLE PRESSURE  (com níveis institucionais)
# ══════════════════════════════════════════════════════════════════
def build_pressure_chart(df, spot, niveis=None):
    bar_vol=(df.groupby("strikePrice").agg(dex=("dex_total","sum"),gex=("gex_total","sum"),vanna=("vanna_total","sum")).reset_index().sort_values("strikePrice"))
    bar_oi=(df.groupby("strikePrice").agg(dex_oi=("dex_oi","sum"),gex_oi=("gex_oi","sum"),vanna_oi=("vanna_oi","sum")).reset_index().sort_values("strikePrice"))
    bar5=bar_vol.merge(bar_oi,on="strikePrice",how="left").fillna(0)
    sy_num=bar5["strikePrice"].tolist(); bar5_lbl=bar5["strikePrice"].map(_fmt_strike)
    spot_lbl=_fmt_strike(min(sy_num,key=lambda s:abs(s-spot)))

    def build_legends(metric_vol,metric_oi,legend_fn):
        niveis_l,descs=[],[]
        serie_vol=bar5[metric_vol]; serie_oi=bar5[metric_oi]
        for i,sk in enumerate(sy_num):
            vol_val=float(serie_vol.iloc[i]); oi_val=float(serie_oi.iloc[i])
            nv,dc=legend_fn(vol_val,serie_vol,sk,spot)
            niveis_l.append(nv); descs.append(f"{dc} | OI-based: {fmt_M(oi_val)}")
        return niveis_l,descs

    dex_niveis,dex_descs=build_legends("dex","dex_oi",legenda_dex_ctx)
    gex_niveis,gex_descs=build_legends("gex","gex_oi",legenda_gex_ctx)
    vanna_niveis,vanna_descs=build_legends("vanna","vanna_oi",legenda_vanna_ctx)

    fig=make_subplots(rows=1,cols=3,shared_yaxes=True,subplot_titles=["DELTA FLOW (DEX)","GAMMA EXPOSURE (GEX)","VANNA (dΔ/dVol)"],horizontal_spacing=0.025)

    def colored_bars(vals,pc,nc):
        arr=np.array(vals,dtype=float); mx=float(np.abs(arr).max()) if len(arr)>0 else 1.0
        return [COLOR_GOLD if(mx>0 and abs(x)==mx) else(pc if x>=0 else nc) for x in arr]

    configs=[("dex","dex_oi",dex_niveis,dex_descs,COLOR_NEON,COLOR_ORANGE,"DEX (Delta Flow)",1),
             ("gex","gex_oi",gex_niveis,gex_descs,COLOR_PURPLE,COLOR_ORANGE,"GEX (Gamma MM)",2),
             ("vanna","vanna_oi",vanna_niveis,vanna_descs,"#4dff91",COLOR_ORANGE,"VANNA (dΔ/dVol)",3)]
    for metric_vol,metric_oi,niveis_l,descs,pc,nc,label,ci in configs:
        v_vol=bar5[metric_vol].values; v_oi=bar5[metric_oi].values
        cd=np.stack([niveis_l,descs,[fmt_M(x) for x in v_oi]],axis=1)
        fig.add_trace(go.Bar(y=bar5_lbl,x=bar5[metric_vol],orientation="h",marker_color=colored_bars(v_vol,pc,nc),
            showlegend=False,name=f"{label} VOL",customdata=cd,
            hovertemplate=(f"<b>Strike: %{{y}}</b><br>VOL-based: $%{{x:,.0f}}<br>OI-based: %{{customdata[2]}}<br>──────────────────<br>%{{customdata[0]}}<br><i>%{{customdata[1]}}</i><extra>{label}</extra>")),row=1,col=ci)
        oi_colors=[pc if x>=0 else nc for x in v_oi]
        fig.add_trace(go.Bar(y=bar5_lbl,x=bar5[metric_oi],orientation="h",marker_color=oi_colors,marker_opacity=0.35,
            marker_line=dict(color=pc,width=0.5),showlegend=False,name=f"{label} OI",hoverinfo="skip"),row=1,col=ci)
        fig.add_vline(x=0,line_color=COLOR_NEON,line_width=0.6,line_dash="dot",row=1,col=ci)
        xref=f"x{ci if ci>1 else ''}"
        fig.add_shape(type="line",x0=0,x1=1,xref=f"{xref} domain",y0=spot_lbl,y1=spot_lbl,yref="y",
            line=dict(color=COLOR_NEON,width=1.5,dash="dash"),row=1,col=ci)
        if ci==1: fig.add_annotation(x=1,xref=f"{xref} domain",y=spot_lbl,yref="y",text=f"  SPOT {_fmt_strike(spot)}",showarrow=False,xanchor="left",font=dict(color=COLOR_NEON,size=13,family="JetBrains Mono"),row=1,col=ci)

    fig.update_layout(height=700,template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(8,12,20,0.6)",
        barmode="overlay",showlegend=False,margin=dict(t=90,b=20,l=10,r=10),font=dict(family="JetBrains Mono",size=13,color="#ccddf8"),
        hoverlabel=dict(font_size=14,font_family="JetBrains Mono",bgcolor="#0a1a20",bordercolor="#00ffe7"))
    for ci in range(1,4): fig.update_xaxes(showgrid=True,gridcolor="rgba(0,255,255,0.06)",zerolinecolor="rgba(0,255,255,0.4)",zerolinewidth=1.5,row=1,col=ci)
    fig.update_yaxes(showgrid=True,gridcolor="rgba(0,255,255,0.06)",row=1,col=1)

    # Estiliza anotações já existentes (subplot titles + label de SPOT) com cor neon
    for ann in fig.layout.annotations:
        ann.font.color = COLOR_NEON
        ann.font.family = "Inter, sans-serif"
        ann.font.size = 13

    # ── NÍVEIS INSTITUCIONAIS (linhas + labels douradas) ──
    # Adicionados APÓS o loop de override acima, para garantir que as labels
    # douradas não sejam sobrescritas pelo estilo neon padrão.
    if niveis and sy_num:
        gex_keys = ["VOL Trigger", "Gamma Pos.OI", "Gamma Neg. OI | VOL Attack", "Gamma Pos. Vol", "Gamma Neg. OIVol"]
        dex_keys = ["Delta Flip", "Delta Pos. OI", "Delta Neg. OI", "Delta Pos.Vol", "Delta Neg. Vol"]

        def _draw_levels(keys, col_idx):
            buckets = {}  # lbl_cat -> [(nome, raw_strike), ...]
            for k in keys:
                v = niveis.get(k)
                if v is None: continue
                closest = min(sy_num, key=lambda s: abs(s - v))
                lbl = _fmt_strike(closest)
                buckets.setdefault(lbl, []).append((k, v))

            xref = f"x{col_idx if col_idx>1 else ''}"
            for lbl, items in buckets.items():
                fig.add_shape(type="line", x0=0, x1=1, xref=f"{xref} domain",
                    y0=lbl, y1=lbl, yref="y",
                    line=dict(color=COLOR_GOLD, width=1.2, dash="dot"),
                    row=1, col=col_idx)
                if len(items) == 1:
                    name, raw = items[0]
                    txt = f"{name} · {_fmt_strike(raw)}"
                else:
                    nomes = " | ".join(n for n, _ in items)
                    raw_med = float(np.mean([r for _, r in items]))
                    txt = f"{nomes} · {_fmt_strike(raw_med)}"
                fig.add_annotation(x=0.99, xref=f"{xref} domain", y=lbl, yref="y",
                    text=txt, showarrow=False, xanchor="right", yanchor="middle",
                    font=dict(color=COLOR_GOLD, size=10, family="JetBrains Mono"),
                    bgcolor="rgba(8,12,20,0.7)",
                    row=1, col=col_idx)

        _draw_levels(dex_keys, 1)
        _draw_levels(gex_keys, 2)

    # Legenda do topo — posicionada acima dos subplot titles
    fig.add_annotation(x=0.5,y=1.10,xref="paper",yref="paper",showarrow=False,
        text=(f"<span style='color:{COLOR_NEON};'>█</span> VOL-based (opaco)  &nbsp;&nbsp;"
              f"<span style='color:{COLOR_NEON};opacity:0.35;'>█</span> OI-based (transparente)  &nbsp;&nbsp;"
              f"<span style='color:{COLOR_GOLD};'>┄┄</span> Níveis institucionais"),
        font=dict(size=12,family="JetBrains Mono",color="#8a9bb5"),align="center")
    return fig

# ══════════════════════════════════════════════════════════════════
# 10 · SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("<div style='font-family:Inter,sans-serif;font-size:14px;font-weight:700;color:#0ff;letter-spacing:2px;padding:10px 0 16px;text-shadow:0 0 6px #0ff;'>⚙ SETUP OPERACIONAL</div>", unsafe_allow_html=True)

    nomes_disponiveis=listar_arquivos_github()

    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    snapshots={}
    if nomes_disponiveis: snapshots=agrupar_snapshots(nomes_disponiveis)
    if snapshots: momento=st.selectbox("📅 Snapshot (data):",list(snapshots.keys()))
    else: momento=None; st.info("Aguardando arquivos no GitHub...")

    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    modo_spot=st.radio("🎯 Fonte do Spot:",["Automático","Manual"],horizontal=True)
    spot_in=None
    if modo_spot=="Manual":
        spot_manual_str=st.text_input("💲 Spot Atual:",value="",placeholder="Ex: 27200")
        try: spot_in=float(spot_manual_str.replace(",",".")) if spot_manual_str.strip() else None
        except: st.warning("⚠ Spot inválido."); spot_in=None

    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    _sb_key=f"pcp_sb_{momento}"
    if _sb_key not in st.session_state and momento and snapshots.get(momento):
        _frames_sb=[]
        for nome in snapshots[momento]:
            js=baixar_json_github(nome)
            if js:
                _f=parse_json(io.StringIO(json.dumps(js)))
                if _f is not None and not _f.empty: _frames_sb.append(_f)
        if _frames_sb: st.session_state[_sb_key]=calcular_pcp_detalhado(pd.concat(_frames_sb,ignore_index=True))
    _pcp_sb=st.session_state.get(_sb_key,{})
    if _pcp_sb.get("spot_implicito",0)>0:
        st.markdown("<div style='color:#fa0;font-size:13px;letter-spacing:2px;'>⚡ PARIDADE PUT-CALL</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:15px;color:#f0c040;text-shadow:0 0 6px #fa0;margin:4px 0 2px;'>F = <b>{_fmt_strike(_pcp_sb['spot_implicito'])}</b></div><div style='font-size:13px;color:#8a9bb5;margin-bottom:4px;'>ATM: {_fmt_strike(_pcp_sb['strike_atm'])} &nbsp;|&nbsp; Δ call: {_pcp_sb['delta_call_atm']:.4f}</div>", unsafe_allow_html=True)
        if _pcp_sb.get("delta_flip_abaixo") is not None:
            st.markdown(f"<div style='font-size:13px;color:#8a9bb5;'>Δ flip: {_fmt_strike(_pcp_sb['delta_flip_abaixo'])} → {_fmt_strike(_pcp_sb['delta_flip_acima'])}</div>", unsafe_allow_html=True)
        st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)

    st.markdown("<div style='color:#0ff;font-size:13px;letter-spacing:2px;'>📏 RANGE DE STRIKES</div>", unsafe_allow_html=True)
    col_s1,col_s2=st.columns(2)
    with col_s1: s_min_str=st.text_input("Strike Mín",value="0")
    with col_s2: s_max_str=st.text_input("Strike Máx",value="999999")
    try: s_min=float(s_min_str.replace(",","."))
    except: s_min=0.0
    try: s_max=float(s_max_str.replace(",","."))
    except: s_max=999999.0

    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    min_fin=st.number_input("💰 Vol. Financeiro Mín ($)",value=0,step=10_000,format="%d")

# ══════════════════════════════════════════════════════════════════
# 11 · HEADER
# ══════════════════════════════════════════════════════════════════
st.markdown(f"<div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;'><h3 style='margin:0;'>📡 PAINEL DE CONTROLE • MARKET MAKER</h3><span class='text-dim'>⏱️ {datetime.now().strftime('%H:%M:%S')} | V9</span></div>", unsafe_allow_html=True)
st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 12 · GUARD
# ══════════════════════════════════════════════════════════════════
if not momento:
    st.markdown(alert_box("⬆ Aguardando arquivos JSON na pasta 'dados/' do repositório GitHub.","info"), unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════
# 13 · CARGA DE DADOS
# ══════════════════════════════════════════════════════════════════
lista_arq=snapshots[momento]; frames=[]
for nome in lista_arq:
    js=baixar_json_github(nome)
    if js:
        f=parse_json(io.StringIO(json.dumps(js)))
        if f is not None and not f.empty: frames.append(f)

if not frames:
    st.error("❌ Nenhum dado válido nos arquivos selecionados."); st.stop()

df_raw=pd.concat(frames,ignore_index=True)
if modo_spot=="Manual": spot=detectar_spot(df_raw,spot_in)
else: spot=_detectar_spot_pcp(df_raw) or detectar_spot(df_raw,None)

if spot<=0:
    st.error("❌ Não foi possível detectar o Spot. Informe manualmente na sidebar."); st.stop()

df=calcular_v9(df_raw,spot,s_min,s_max,min_fin=float(min_fin),mult=float(MULTIPLICADOR_FIXO))
if df is None or df.empty:
    st.warning(f"⚠ Nenhum dado no range {_fmt_strike(s_min)} — {_fmt_strike(s_max)} com os filtros atuais."); st.stop()

# ══════════════════════════════════════════════════════════════════
# 14 · MÉTRICAS GLOBAIS
# ══════════════════════════════════════════════════════════════════
res_intel,g_flip=processar_inteligencia(df,spot)
strikes_agg=(df.groupby(["strikePrice","optionType"]).agg(gex_total=("gex_total","sum"),dex_total=("dex_total","sum"),
    vanna_total=("vanna_total","sum"),volume=("volume","sum"),financial_flow=("financial_flow","sum")).reset_index())
net_gex=df["gex_total"].sum(); net_dex=df["dex_total"].sum(); net_vanna=df["vanna_total"].sum(); net_delta=net_dex
call_vol=df[df["optionType"]=="Call"]["volume"].sum(); put_vol=df[df["optionType"]=="Put"]["volume"].sum()
mom_val=call_vol/put_vol if put_vol>0 else 1.0
cnt_buy=(df["side"]=="BUY").sum(); cnt_sell=(df["side"]=="SELL").sum()
cnt_bruto=df["side"].str.startswith("BRUTO").sum(); total_cls=len(df)
sent_bull=net_delta>0; sent_label="ALTISTA" if sent_bull else "BAIXISTA"; sent_cls="bull" if sent_bull else "bear"
vol_bull=net_vanna>0; vol_status="LONG VOL" if vol_bull else "SHORT VOL"
vol_color="#0f0" if vol_bull else "#f44"; tag_vol_cls="tag-bull" if vol_bull else "tag-bear"
shock_act="MM COMPRA" if net_vanna>0 else "MM VENDE"; shock_col="#0f0" if net_vanna>0 else "#f44"
gex_by_s=strikes_agg.groupby("strikePrice")["gex_total"].sum()
gamma_wall=float(gex_by_s.abs().idxmax()) if not gex_by_s.empty else 0.0
gex_wall_val=float(gex_by_s.get(gamma_wall,0.0))
vol_by_s=strikes_agg.groupby("strikePrice")["volume"].sum()
max_vol_s=float(vol_by_s.idxmax()) if not vol_by_s.empty else 0.0
bar_agg=strikes_agg.groupby("strikePrice").agg(gex_total=("gex_total","sum"),dex_total=("dex_total","sum"),financial_flow=("financial_flow","sum")).reset_index()
ic_df=strikes_agg[strikes_agg["optionType"]=="Call"].nlargest(2,"dex_total")
ip_df=strikes_agg[strikes_agg["optionType"]=="Put"].nsmallest(2,"dex_total")
top_v=strikes_agg.sort_values("vanna_total",key=abs,ascending=False).head(3)
w_calls=res_intel["whales"][res_intel["whales"]["optionType"]=="Call"] if not res_intel["whales"].empty else pd.DataFrame()
w_puts=res_intel["whales"][res_intel["whales"]["optionType"]=="Put"] if not res_intel["whales"].empty else pd.DataFrame()

# ══════════════════════════════════════════════════════════════════
# 15 · LAYOUT PRINCIPAL  30% | 70%
# ══════════════════════════════════════════════════════════════════
col_left,col_right=st.columns([3,7])

with col_left:
    st.markdown(alert_box(res_intel["msg"],res_intel["status"]), unsafe_allow_html=True)
    pcp_res=calcular_pcp_detalhado(df_raw); pcp_spot=pcp_res["spot_implicito"]
    pcp_label=_fmt_strike(pcp_spot) if pcp_spot>0 else "—"
    spot_source="PCP" if(modo_spot=="Automático" and pcp_spot>0) else("Manual" if modo_spot=="Manual" else "Δ0.5")
    st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:13px;color:#0ff;margin:12px 0 2px;letter-spacing:1px;text-shadow:0 0 5px #0ff;'>⚡ SPOT: <b>{_fmt_strike(spot)}</b><span style='font-size:13px;color:#8a9bb5;margin-left:8px;'>({spot_source})</span></div>", unsafe_allow_html=True)

    if pcp_spot>0:
        with st.expander("📐 Paridade Put-Call — Cálculo Detalhado",expanded=False):
            diff_str=f"+{pcp_res['diferenca']:.3f}" if pcp_res['diferenca']>=0 else f"{pcp_res['diferenca']:.3f}"
            st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:13px;'><div style='font-size:13px;color:#fa0;letter-spacing:2px;margin-bottom:6px;'>FÓRMULA: F = K + (C − P)</div><div style='background:rgba(240,192,64,0.07);border:1px solid rgba(240,192,64,0.3);border-left:4px solid #f0c040;border-radius:8px;padding:10px 14px;margin-bottom:8px;'><div style='font-size:13px;color:#8a9bb5;margin-bottom:4px;'>Strike ATM: <b style='color:#f0c040;'>{_fmt_strike(pcp_res['strike_atm'])}</b> &nbsp;|&nbsp; Δ call: <b style='color:#f0c040;'>{pcp_res['delta_call_atm']:.4f}</b></div><div style='font-size:13px;color:#8a9bb5;'>C mid = ({pcp_res['c_bid']:.2f} + {pcp_res['c_ask']:.2f}) / 2 = <b style='color:#ccddf8;'>{pcp_res['c_mid']:.3f}</b></div><div style='font-size:13px;color:#8a9bb5;'>P mid = ({pcp_res['p_bid']:.2f} + {pcp_res['p_ask']:.2f}) / 2 = <b style='color:#ccddf8;'>{pcp_res['p_mid']:.3f}</b></div><div style='font-size:13px;color:#8a9bb5;margin-top:4px;'>F = {_fmt_strike(pcp_res['strike_atm'])} + ({pcp_res['c_mid']:.3f} − {pcp_res['p_mid']:.3f}) = {_fmt_strike(pcp_res['strike_atm'])} {diff_str} = <b style='color:#f0c040;font-size:14px;text-shadow:0 0 6px #fa0;'>{pcp_label}</b></div></div>", unsafe_allow_html=True)
            flip_ab=pcp_res["delta_flip_abaixo"]; flip_ac=pcp_res["delta_flip_acima"]
            if flip_ab is not None:
                st.markdown(f"<div style='background:rgba(0,255,255,0.05);border:1px solid rgba(0,255,255,0.2);border-left:4px solid #0ff;border-radius:8px;padding:8px 12px;margin-bottom:8px;font-family:JetBrains Mono,monospace;font-size:13px;'><span style='color:#0ff;'>⚡ VALIDAÇÃO DELTA:</span> Strike <b style='color:#f0c040;'>{_fmt_strike(flip_ab)}</b> (Δ≥0.50) → <b style='color:#f0c040;'>{_fmt_strike(flip_ac)}</b> (Δ&lt;0.50) &nbsp;→&nbsp; <span style='color:#0f0;'>spot entre {_fmt_strike(flip_ab)} e {_fmt_strike(flip_ac)}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='font-size:13px;color:#8a9bb5;margin-bottom:8px;'>⚡ Flip de delta não detectado no range atual.</div>", unsafe_allow_html=True)
            if pcp_res["tabela"]:
                rows_pcp=""
                for e in pcp_res["tabela"]:
                    is_atm=e["K"]==pcp_res["strike_atm"]; row_style="background:rgba(240,192,64,0.08);" if is_atm else ""; star=" ★" if is_atm else ""
                    rows_pcp+=(f"<tr style='{row_style}'><td class='text-gold'>{_fmt_strike(e['K'])}{star}</td><td style='color:#ccddf8;'>{e['c_bid']:.2f}</td><td style='color:#ccddf8;'>{e['c_ask']:.2f}</td><td style='color:#f0c040;font-weight:bold;'>{e['delta_call']:.4f}</td><td style='color:#ccddf8;'>{e['p_bid']:.2f}</td><td style='color:#ccddf8;'>{e['p_ask']:.2f}</td><td style='color:#0ff;font-weight:bold;'>{e['F']:.2f}</td></tr>")
                st.markdown(f"<div style='overflow-x:auto;'><table class='hud-table'><thead><tr><th>STRIKE</th><th>C BID</th><th>C ASK</th><th>Δ CALL</th><th>P BID</th><th>P ASK</th><th>F IMP.</th></tr></thead><tbody>{rows_pcp}</tbody></table><div style='font-size:11px;color:#4a7a75;margin-top:4px;'>★ ATM selecionado</div></div>", unsafe_allow_html=True)

    k1,k2=st.columns(2)
    k1.markdown(kpi("SENTIMENTO",sent_label,sent_cls,f"Net Δ {fmt_M(net_delta)}"), unsafe_allow_html=True)
    k2.markdown(kpi("C/P MOMENTUM",f"{mom_val:.2f}x","neutral",f"C:{call_vol:,.0f}  P:{put_vol:,.0f}"), unsafe_allow_html=True)
    k3,k4=st.columns(2)
    k3.markdown(kpi("NET GEX (MM)",fmt_M(net_gex),"neutral","Long+=estabil. Short−=aceler."), unsafe_allow_html=True)
    k4.markdown(kpi("NET DEX (flow)",fmt_M(net_delta),sent_cls,"Delta flow real c/ dir"), unsafe_allow_html=True)

    section("ESTRUTURA GAMA & RISCO")
    def legenda_gwall(sk,gex,spot):
        dist=(sk-spot)/spot*100; acima=sk>spot; val=fmt_M(gex); dist_s=f"{dist:+.1f}%"
        if acima: acao="⛔ Teto"; cor="#FF4444"; desc=f"Gamma Wall acima do spot ({dist_s}). MM vai vender delta se preço subir. Difícil de romper."
        else: acao="🟢 Piso"; cor="#00FF00"; desc=f"Gamma Wall abaixo do spot ({dist_s}). MM vai comprar delta se preço cair. Suporte estrutural forte."
        return acao,cor,desc,val,dist_s
    def legenda_gflip(sk,spot):
        dist=(sk-spot)/spot*100; dist_s=f"{dist:+.1f}%"; acima=sk>spot
        desc=(f"Gamma Flip acima do spot ({dist_s}). MM passa de long para short gamma acima desse nível." if acima else f"Gamma Flip abaixo do spot ({dist_s}). MM passa de long para short gamma abaixo desse nível.")
        return desc,dist_s
    def legenda_maxvol(sk,spot):
        dist=(sk-spot)/spot*100; dist_s=f"{dist:+.1f}%"; acima=sk>spot
        desc=(f"Maior concentração de volume acima do spot ({dist_s}). Strike magnético — preço pode ser atraído até ele." if acima else f"Maior concentração de volume abaixo do spot ({dist_s}). Strike magnético — preço pode gravitar até ele.")
        return desc,dist_s
    gw_acao,gw_cor,gw_desc,gw_val,gw_dist=legenda_gwall(gamma_wall,gex_wall_val,spot)
    gf_desc,gf_dist=legenda_gflip(g_flip,spot); mv_desc,mv_dist=legenda_maxvol(max_vol_s,spot)
    gex_wall_sign="Long" if gex_wall_val>=0 else "Short"
    st.markdown(f"<div class='dashboard-card'><table class='hud-table'><tr><th>NÍVEL</th><th>STRIKE</th><th>VALOR</th><th>AÇÃO</th><th>DIST</th></tr><tr title='{gw_desc}' style='border-bottom:1px solid rgba(255,255,255,0.05);cursor:help;'><td style='font-size:13px;'>🧱 Gamma Wall</td><td class='text-gold'><b>{_fmt_strike(gamma_wall)}</b></td><td style='color:#0ff;font-size:13px;'>{gex_wall_sign} {gw_val}</td><td style='color:{gw_cor};font-size:13px;'>{gw_acao}</td><td style='color:#8a9bb5;font-size:13px;'>{gw_dist}</td></tr><tr title='{gf_desc}' style='border-bottom:1px solid rgba(255,255,255,0.05);cursor:help;'><td style='font-size:13px;'>⚡ Gamma Flip</td><td class='text-gold'><b>{_fmt_strike(g_flip)}</b></td><td class='text-dim' style='font-size:13px;'>Zero-crossing</td><td style='color:#ffa500;font-size:13px;'>🔄 Transição</td><td style='color:#8a9bb5;font-size:13px;'>{gf_dist}</td></tr><tr title='{mv_desc}' style='cursor:help;'><td style='font-size:13px;'>🎯 Max Volume</td><td class='text-gold'><b>{_fmt_strike(max_vol_s)}</b></td><td class='text-dim' style='font-size:13px;'>Pico</td><td style='color:#ffd700;font-size:13px;'>🧲 Magnético</td><td style='color:#8a9bb5;font-size:13px;'>{mv_dist}</td></tr></table><div style='font-size:11px;color:#3a7a8a;margin-top:6px;font-family:JetBrains Mono;'>💡 Passe o mouse nas linhas para ver a interpretação operacional.</div></div>", unsafe_allow_html=True)

    section("ZONAS DE IMPACTO DELTA")
    ri=""
    for _,r in ic_df.iterrows():
        sk=r["strikePrice"]; dist=abs(sk-spot)/spot*100
        if sk>spot: tipo_lbl="<span style='color:#FF4444;font-size:13px;'>⛔ Resistência</span>"; motivo="Call OTM acima do spot. MM vai vender delta se preço subir até aqui."
        else: tipo_lbl="<span style='color:#00FF00;font-size:13px;'>🟢 Suporte</span>"; motivo="Call ITM abaixo do spot. MM já comprou futuros para hedge."
        ri+=f"<tr title='{motivo}' style='cursor:help;'><td>{tipo_lbl}</td><td class='text-gold' style='font-size:13px;'>{_fmt_strike(sk)}C</td><td style='color:#8a9bb5;font-size:13px;'>{dist:.1f}%</td></tr>"
    for _,r in ip_df.iterrows():
        sk=r["strikePrice"]; dist=abs(sk-spot)/spot*100
        if sk<spot: tipo_lbl="<span style='color:#00FF00;font-size:13px;'>🟢 Suporte</span>"; motivo="Put OTM abaixo do spot. MM vai comprar futuros se preço cair até aqui."
        else: tipo_lbl="<span style='color:#FF4444;font-size:13px;'>⛔ Pressão Vend.</span>"; motivo="Put ITM acima do spot. MM já vendeu futuros para hedge."
        ri+=f"<tr title='{motivo}' style='cursor:help;'><td>{tipo_lbl}</td><td class='text-gold' style='font-size:13px;'>{_fmt_strike(sk)}P</td><td style='color:#8a9bb5;font-size:13px;'>{dist:.1f}%</td></tr>"
    dex_sorted_df=bar_agg.sort_values("strikePrice"); delta_flip_strike=None
    for i in range(len(dex_sorted_df)-1):
        if dex_sorted_df.iloc[i]["dex_total"]*dex_sorted_df.iloc[i+1]["dex_total"]<0:
            delta_flip_strike=dex_sorted_df.iloc[i+1]["strikePrice"]; break
    delta_flip_html=""
    if delta_flip_strike is not None:
        dist_flip=abs(delta_flip_strike-spot)/spot*100; lado_flip="acima do spot" if delta_flip_strike>spot else "abaixo do spot"
        msg_flip="MM passa de vendido para comprado acima desse nível." if delta_flip_strike>spot else "MM passa de comprado para vendido abaixo desse nível."
        delta_flip_html=(f"<tr style='border-top:1px solid rgba(255,165,0,0.4);'><td colspan='3' style='padding-top:8px;'><span style='color:#ffa500;font-family:JetBrains Mono;font-size:13px;letter-spacing:1px;'>🔄 DELTA FLIP &nbsp;<b style='color:#fff;'>{_fmt_strike(delta_flip_strike)}</b>&nbsp;<span style='color:#8a9bb5;'>({dist_flip:.1f}% · {lado_flip})</span><br><span style='color:#8a9bb5;font-size:11px;'>Ponto onde pressão direcional muda de sinal. {msg_flip}</span></span></td></tr>")
    st.markdown(f"<div class='dashboard-card'><table class='hud-table'><tr><th>TIPO</th><th>STRIKE</th><th>DIST.</th></tr>{ri}{delta_flip_html}</table><div style='font-size:11px;color:#3a7a8a;margin-top:6px;font-family:JetBrains Mono;'>💡 Passe o mouse nas linhas para ver o motivo da classificação.</div></div>", unsafe_allow_html=True)

    section("VANNA & VOLATILIDADE")
    st.markdown(f"<div class='dashboard-card' style='border-left:4px solid {vol_color};'><div style='display:flex;justify-content:space-between;align-items:center;'><span class='kpi-label' style='font-size:13px;'>{vol_status}</span><span class='tag {tag_vol_cls}'>{vol_status}</span></div><div style='font-family:JetBrains Mono,monospace;font-size:18px;color:#f0f3fa;margin:6px 0;text-shadow:0 0 5px rgba(0,255,255,0.4);'>{fmt_M(net_vanna)}</div><div style='background:rgba(0,255,255,0.04);padding:6px;border-left:3px solid {shock_col};border-radius:6px;font-size:13px;font-family:JetBrains Mono,monospace;'><span class='text-dim'>VANNA LÍQUIDA:</span> <span style='color:{shock_col};font-weight:bold;'>{shock_act} {fmt_M(net_vanna)}</span></div></div>", unsafe_allow_html=True)

    section("TOP VANNA POINTS")
    vrows=""; serie_vanna=strikes_agg["vanna_total"]
    for _,r in top_v.iterrows():
        nv,dc=legenda_vanna_ctx(r["vanna_total"],serie_vanna,r["strikePrice"],spot)
        act="COMPRA" if r["vanna_total"]>0 else "VENDE"; clr="#0f0" if r["vanna_total"]>0 else "#f44"
        vrows+=f"<tr title='{dc}' style='cursor:help;'><td class='text-cyan' style='font-size:13px;'>🐳 {_fmt_strike(r['strikePrice'])}{r['optionType'][0]}</td><td style='color:{clr};font-weight:bold;font-size:13px;'>{act}</td><td class='text-gold' style='font-size:13px;'>{fmt_M(r['vanna_total'])}</td><td style='color:#8a9bb5;font-size:11px;'>{nv}</td></tr>"
    st.markdown(f"<div class='dashboard-card'><table class='hud-table'><tr><th>STRIKE</th><th>AÇÃO IV↑</th><th>FLUXO</th><th>NÍVEL</th></tr>{vrows}</table><div style='font-size:11px;color:#3a7a8a;margin-top:6px;font-family:JetBrains Mono;'>💡 Passe o mouse nas linhas para ver a interpretação.</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    section("DIAGNÓSTICO ESTRATÉGICO")
    regime_gamma="SHORT GAMMA" if net_gex<0 else "LONG GAMMA"
    rg_sub="Aceleração de Movimentos" if net_gex<0 else "Estabilidade / Mean Reversion"
    bias_label="ALTISTA (MM Buying)" if net_delta>0 else "BAIXISTA (MM Selling)"
    bias_cls="bull" if net_delta>0 else "bear"
    greeks_inv=(~df["greeks_ok"]).sum(); stale_cnt=(df["side"]=="BRUTO_STALE").sum()
    d1,d2=st.columns(2)
    d1.markdown(kpi("REGIME GAMMA (MM)",regime_gamma,"",rg_sub), unsafe_allow_html=True)
    d2.markdown(kpi("BIAS DIRECIONAL",bias_label,bias_cls,f"Net DEX {fmt_M(net_dex)}"), unsafe_allow_html=True)
    d3,d4=st.columns(2)
    d3.markdown(kpi("GREEKS INVÁLIDOS",f"{greeks_inv}","neutral","Excluídos GEX/Vanna"), unsafe_allow_html=True)
    d4.markdown(kpi("BRUTO (sem dir.)",f"{cnt_bruto}","neutral","GEX/DEX/Vanna zerados"), unsafe_allow_html=True)
    notas=[]
    if net_gex<0 and net_delta<0: notas.append(("danger","⚠ PERIGO: MM em Short Gamma com bias baixista → Queda Acelerada"))
    if net_gex>0 and net_delta>0: notas.append(("warning","✅ ANCORAGEM: Long Gamma com bias altista → Topo em formação"))
    if g_flip>0 and abs(g_flip-spot)/spot<0.005: notas.append(("info",f"🎯 ZONA CRÍTICA: Spot próximo ao Gamma Flip ({_fmt_strike(g_flip)})"))
    if notas:
        section("NOTAS DE CAMPO")
        for kind,msg_nota in notas: st.markdown(alert_box(msg_nota,kind), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# COLUNA DIREITA
# ══════════════════════════════════════════════════════════════════
with col_right:
    section("TERMINAL: VOLUME · OPEN INTEREST")
    fig_main=build_main_chart(df,strikes_agg,spot)
    st.plotly_chart(fig_main,use_container_width=True)

    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    section("TRIPLE PRESSURE MAP  —  DEX · GEX · VANNA  (VOL opaco + OI transparente)")
    niveis_inst = calcular_niveis_institucionais(df_raw, spot, s_min, s_max, mult=float(MULTIPLICADOR_FIXO))
    fig_press = build_pressure_chart(df, spot, niveis=niveis_inst)
    st.plotly_chart(fig_press, use_container_width=True)

    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    section("MOMENTUM REAL — VOL/OI  (urgência do fluxo por strike)")

    _df_mom = df_raw[
        (df_raw["openInterest"] > 10) &
        (df_raw["strikePrice"] >= s_min) &
        (df_raw["strikePrice"] <= s_max)
    ].copy()

    if not _df_mom.empty:
        _df_mom["Vol_OI"] = _df_mom["volume"] / _df_mom["openInterest"].replace(0, 1)
        _urg_threshold = _df_mom["Vol_OI"][_df_mom["Vol_OI"] > 0].quantile(0.75) if not _df_mom.empty else 1.0

        def _classif_urgencia(vol_oi, tipo, threshold):
            if vol_oi < 0.3:   return "⚪ POSIÇÃO ESTÁTICA",  "Strike sem atividade relevante no momento."
            elif vol_oi < 1.0: return "🔵 FLUXO NORMAL",      "Nada fora do comum. MM operando normalmente."
            elif vol_oi < threshold: return "🟡 FLUXO ELEVADO","Movimento acima do normal. Fique atento."
            elif vol_oi < threshold * 2:
                if tipo == "Call": return "🟠 URGÊNCIA DETECTADA","Grandes players comprando. Pressão de alta."
                else:              return "🟠 URGÊNCIA DETECTADA","Grandes players se protegendo. Pressão de baixa."
            else:
                if tipo == "Call": return "🔴 ALERTA MÁXIMO","Muita compra aqui. Preço pode subir rápido e forte."
                else:              return "🔴 ALERTA MÁXIMO","Muita proteção aqui. Preço pode cair rápido e forte."

        _niveis_m, _comps_m = [], []
        for _, _row in _df_mom.iterrows():
            _nv, _cp = _classif_urgencia(_row["Vol_OI"], _row["optionType"], _urg_threshold)
            _niveis_m.append(_nv); _comps_m.append(_cp)
        _df_mom["nivel"]         = _niveis_m
        _df_mom["comportamento"] = _comps_m

        fig_mom = go.Figure()
        for _tipo, _color, _label in zip(["Call","Put"],[COLOR_CALL,COLOR_PUT],["CALL","PUT"]):
            _df_v = (
                _df_mom[_df_mom["optionType"] == _tipo]
                .groupby("strikePrice")[["Vol_OI","nivel","comportamento"]]
                .agg({"Vol_OI":"sum","nivel":"first","comportamento":"first"})
                .reset_index()
            )
            if _df_v.empty: continue
            fig_mom.add_trace(go.Bar(
                x=_df_v["strikePrice"], y=_df_v["Vol_OI"],
                marker_color=_color, marker_line_width=0, name=_label,
                customdata=np.stack([_df_v["nivel"],_df_v["comportamento"]],axis=1),
                hovertemplate=(
                    "<b>Strike: %{x:,.2f}</b><br>Vol/OI: %{y:.2f}x<br>"
                    f"Tipo: {_label}<br>──────────────────<br>"
                    "%{customdata[0]}<br><i>%{customdata[1]}</i><extra></extra>"
                ),
            ))

        fig_mom.add_hline(y=_urg_threshold, line_dash="dash", line_color="#ffa500", line_width=1.5, opacity=0.9,
            annotation_text=f"URGÊNCIA MM ({_urg_threshold:.2f}x)", annotation_position="top right",
            annotation_font=dict(color="#ffa500",size=11,family="JetBrains Mono"))
        fig_mom.add_hline(y=1.0, line_dash="dot", line_color="#ffffff", line_width=1, opacity=0.35,
            annotation_text="neutro 1.0x", annotation_position="bottom right",
            annotation_font=dict(color="#888",size=10,family="JetBrains Mono"))
        fig_mom.add_vline(x=spot, line_dash="dot", line_color=COLOR_NEON, line_width=1.5)
        fig_mom.add_annotation(x=spot, y=1.0, xref="x", yref="paper",
            text=f"SPOT {_fmt_strike(spot)}", showarrow=False, yshift=8,
            font=dict(color=COLOR_NEON,size=10,family="JetBrains Mono"), xanchor="center")
        fig_mom.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(8,12,20,0.6)",
            height=420, barmode="group", showlegend=True,
            legend=dict(orientation="h",y=1.02,x=1,xanchor="right",font=dict(size=11,family="JetBrains Mono"),bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=10,r=10,t=20,b=20),
            font=dict(family="JetBrains Mono",size=11,color="#ccddf8"),
            xaxis=dict(gridcolor="rgba(0,255,255,0.06)",tickangle=-45,tickfont=dict(size=11),title="Strike"),
            yaxis=dict(gridcolor="rgba(0,255,255,0.06)",title="Vol/OI ratio"),
            hoverlabel=dict(font_size=13,font_family="JetBrains Mono",bgcolor="#0a1a20",bordercolor=COLOR_NEON),
        )
        st.plotly_chart(fig_mom, use_container_width=True)

        _mom_max = _df_mom.sort_values("Vol_OI", ascending=False).head(1)
        if not _mom_max.empty:
            _mx = _mom_max.iloc[0]
            _mx_cor = "#ffa500" if _mx["Vol_OI"] >= _urg_threshold else "#8a9bb5"
            st.markdown(
                f"<div style='font-family:JetBrains Mono,monospace;font-size:13px;"
                f"color:{_mx_cor};padding:6px 10px;background:rgba(255,165,0,0.05);"
                f"border-left:3px solid {_mx_cor};border-radius:4px;margin-top:4px;'>"
                f"⚡ Máx. urgência: <b>Strike {_fmt_strike(_mx['strikePrice'])}</b> · "
                f"{_mx['optionType']} · <b>{_mx['Vol_OI']:.2f}x</b> · {_mx['nivel']}</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(alert_box("⚠ Dados insuficientes para calcular Vol/OI (OI > 10 em nenhum strike).","warning"), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 16 · RADAR INSTITUCIONAL
# ══════════════════════════════════════════════════════════════════
if not res_intel["whales"].empty:
    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    section("🐋 RADAR INSTITUCIONAL (Z > 2.5σ)")

    def agg_whales(wdf):
        if wdf.empty: return wdf
        return (wdf.groupby("strikePrice").agg(
            z_score=("z_score",lambda x:x.abs().max()), d_flow=("d_flow","sum"),
            volume=("volume","sum"), financial_flow=("financial_flow","sum"),
            optionType=("optionType","first")).reset_index().sort_values("z_score",ascending=False).head(8))

    def legenda_whale_ctx(sk,opt,spot):
        acima=sk>spot; dist=(sk-spot)/spot*100
        if opt=="Call":
            if acima: acao="⛔ Resistência"; cor="#FF4444"; desc="Call OTM. MM vai vender delta se preço subir até aqui."
            else: acao="🟢 Suporte"; cor="#00FF00"; desc="Call ITM. MM já comprou futuros — age como piso."
        else:
            if not acima: acao="🟢 Suporte"; cor="#00FF00"; desc="Put OTM. MM vai comprar futuros se preço cair até aqui."
            else: acao="⛔ Press. Vend."; cor="#FF4444"; desc="Put ITM. MM já vendeu futuros — pressiona para baixo."
        return acao,cor,desc,f"{dist:+.1f}%"

    w_calls_agg=agg_whales(w_calls) if not w_calls.empty else pd.DataFrame()
    w_puts_agg=agg_whales(w_puts) if not w_puts.empty else pd.DataFrame()
    wc1,wc2=st.columns(2)
    with wc1:
        st.markdown("<div style='color:#0f0;font-size:13px;font-weight:bold;letter-spacing:1px;margin-bottom:8px;font-family:JetBrains Mono,monospace;'>🟢 CALLS — IMPACTO MM</div>", unsafe_allow_html=True)
        if not w_calls_agg.empty:
            for _,row in w_calls_agg.iterrows():
                sk=row["strikePrice"]; acao,cor,desc,dist_fmt=legenda_whale_ctx(sk,"Call",spot)
                st.markdown(f"<div class='whale-card' title='{desc}'><b class='text-cyan' style='font-size:13px;'>{_fmt_strike(sk)}C</b> <span style='color:{cor};font-size:13px;font-weight:bold;'>{acao}</span><span class='text-dim' style='float:right;font-size:13px;'>{dist_fmt} do spot</span><br><span class='text-green' style='font-size:13px;'>z={row['z_score']:.1f}</span><span class='text-dim' style='font-size:13px;'> &nbsp;·&nbsp; ΔFlow {fmt_M(row['d_flow'])} &nbsp;·&nbsp; Vol {row['volume']:,.0f} &nbsp;·&nbsp; Fin {fmt_M(row.get('financial_flow',0))}</span></div>", unsafe_allow_html=True)
        else: st.caption("Sem anomalias.")
    with wc2:
        st.markdown("<div style='color:#f44;font-size:13px;font-weight:bold;letter-spacing:1px;margin-bottom:8px;font-family:JetBrains Mono,monospace;'>🔴 PUTS — IMPACTO MM</div>", unsafe_allow_html=True)
        if not w_puts_agg.empty:
            for _,row in w_puts_agg.iterrows():
                sk=row["strikePrice"]; acao,cor,desc,dist_fmt=legenda_whale_ctx(sk,"Put",spot)
                st.markdown(f"<div class='whale-card' title='{desc}'><b class='text-cyan' style='font-size:13px;'>{_fmt_strike(sk)}P</b> <span style='color:{cor};font-size:13px;font-weight:bold;'>{acao}</span><span class='text-dim' style='float:right;font-size:13px;'>{dist_fmt} do spot</span><br><span class='text-red' style='font-size:13px;'>z={row['z_score']:.1f}</span><span class='text-dim' style='font-size:13px;'> &nbsp;·&nbsp; ΔFlow {fmt_M(abs(row['d_flow']))} &nbsp;·&nbsp; Vol {row['volume']:,.0f} &nbsp;·&nbsp; Fin {fmt_M(row.get('financial_flow',0))}</span></div>", unsafe_allow_html=True)
        else: st.caption("Sem anomalias.")


# ══════════════════════════════════════════════════════════════════
# 19 · RODAPÉ
# ══════════════════════════════════════════════════════════════════
st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
st.markdown(f"<div style='text-align:center;font-size:13px;color:rgba(0,255,255,0.25);letter-spacing:2px;padding:8px 0;font-family:JetBrains Mono,monospace;'>◈  DASHBOARD INSTITUCIONAL MARKET MAKER  |  V9  |  {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}  ◈</div>", unsafe_allow_html=True)
