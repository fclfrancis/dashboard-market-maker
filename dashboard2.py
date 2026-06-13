"""
╔══════════════════════════════════════════════════════════════════╗
║   DASHBOARD INSTITUCIONAL MARKET MAKER                          ║
║   Engine: V9  |  Layout: Futurista / Cyberpunk HUD             ║
║   + Níveis Institucionais no Triple Pressure Map (timesat.py)  ║
║   + Ajuste CFD display-only                                     ║
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

# ============================================================
# Esconde ícone GitHub / Fork da toolbar do Streamlit Cloud
# ============================================================
st.markdown("""
<style>
    [data-testid="stToolbarActions"] { display: none !important; }
    [data-testid="stAppDeployButton"] { display: none !important; }
    .stAppDeployButton { display: none !important; }
    .stAppToolbar a[href*="github"] { display: none !important; }
    .stAppToolbar [kind="header"] { display: none !important; }
    header a[href*="github.com"],
    [data-testid="stHeader"] a[href*="github.com"],
    [data-testid="stDecoration"] a[href*="github.com"] { 
        display: none !important; 
    }
    [data-testid="stToolbar"] > div:has(a[href*="github"]) { 
        display: none !important; 
    }
</style>
""", unsafe_allow_html=True)

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

# Offset CFD — display-only, atualizado após detecção do spot
cfd_offset = 0.0

def _fmt_strike_cfd(v):
    """Versão de _fmt_strike que aplica o ajuste CFD (apenas display)."""
    try:
        return _fmt_strike(float(v) + cfd_offset)
    except Exception:
        return _fmt_strike(v)

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
        "Gamma Neg. Vol":                 _safe(per["GEX_VOL"].idxmin()),
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
    elif spot<gamma_flip and net_delta>0: stat,msg="warning",f"🚀 RISCO DE SQUEEZE! MMs precisam cobrir Delta acima de {_fmt_strike_cfd(gamma_flip)}"
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
    sy_num=sorted(df["strikePrice"].unique()); sy_lbl=[_fmt_strike_cfd(s) for s in sy_num]
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
    spot_lbl=num2lbl.get(spot) or _fmt_strike_cfd(min(sy_num,key=lambda s:abs(s-spot)))
    def cat_hline(lbl,color,dash,annotation,ci,width=2.0):
        xref=f"x{ci if ci>1 else ''}"; fig.add_shape(type="line",x0=0,x1=1,xref=f"{xref} domain",y0=lbl,y1=lbl,yref="y",line=dict(color=color,width=width,dash="dashdot" if dash=="longdash" else dash),row=1,col=ci)
        if annotation: fig.add_annotation(x=1,xref=f"{xref} domain",y=lbl,yref="y",text=annotation,showarrow=False,xanchor="right",yanchor="bottom",yshift=4,font=dict(color=color,size=13,family="JetBrains Mono"),row=1,col=ci)
    cat_hline(spot_lbl,COLOR_NEON,"dash",f"SPOT {_fmt_strike_cfd(spot)}",1,width=2.5)
    cat_hline(spot_lbl,COLOR_NEON,"dash",f"SPOT {_fmt_strike_cfd(spot)}",2,width=2.5)
    agg_vc=agg_cp[agg_cp["optionType"]=="Call"].set_index("strikePrice")["volume"]
    agg_vp=agg_cp[agg_cp["optionType"]=="Put"].set_index("strikePrice")["volume"]
    agg_oc=agg_cp[agg_cp["optionType"]=="Call"].set_index("strikePrice")["open_interest"]
    agg_op=agg_cp[agg_cp["optionType"]=="Put"].set_index("strikePrice")["open_interest"]
    for series,color,label,ci in [(agg_vc,COLOR_CALL,"Call Vol Wall",1),(agg_vp,COLOR_PUT,"Put Vol Wall",1),(agg_oc,COLOR_CALL,"Call OI Wall",2),(agg_op,COLOR_PUT,"Put OI Wall",2)]:
        if not series.empty:
            sk=float(series.idxmax()); lbl=num2lbl.get(sk,_fmt_strike_cfd(sk)); cat_hline(lbl,color,"dot",label,ci)
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
    sy_num=bar5["strikePrice"].tolist(); bar5_lbl=bar5["strikePrice"].map(_fmt_strike_cfd)
    spot_lbl=_fmt_strike_cfd(min(sy_num,key=lambda s:abs(s-spot)))

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
        if ci==1: fig.add_annotation(x=1,xref=f"{xref} domain",y=spot_lbl,yref="y",text=f"  SPOT {_fmt_strike_cfd(spot)}",showarrow=False,xanchor="left",font=dict(color=COLOR_NEON,size=13,family="JetBrains Mono"),row=1,col=ci)

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
        gex_keys = ["VOL Trigger", "Gamma Pos.OI", "Gamma Neg. OI | VOL Attack", "Gamma Pos. Vol", "Gamma Neg. Vol"]
        dex_keys = ["Delta Flip", "Delta Pos. OI", "Delta Neg. OI", "Delta Pos.Vol", "Delta Neg. Vol"]

        def _draw_levels(keys, col_idx):
            buckets = {}  # lbl_cat -> [(nome, raw_strike), ...]
            for k in keys:
                v = niveis.get(k)
                if v is None: continue
                closest = min(sy_num, key=lambda s: abs(s - v))
                lbl = _fmt_strike_cfd(closest)
                buckets.setdefault(lbl, []).append((k, v))

            xref = f"x{col_idx if col_idx>1 else ''}"
            for lbl, items in buckets.items():
                fig.add_shape(type="line", x0=0, x1=1, xref=f"{xref} domain",
                    y0=lbl, y1=lbl, yref="y",
                    line=dict(color=COLOR_GOLD, width=1.2, dash="dot"),
                    row=1, col=col_idx)
                if len(items) == 1:
                    name, raw = items[0]
                    txt = f"{name} · {_fmt_strike_cfd(raw)}"
                else:
                    nomes = " | ".join(n for n, _ in items)
                    raw_med = float(np.mean([r for _, r in items]))
                    txt = f"{nomes} · {_fmt_strike_cfd(raw_med)}"
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

    nomes_disponiveis = listar_arquivos_github()
    snapshots = {}
    if nomes_disponiveis:
        snapshots = agrupar_snapshots(nomes_disponiveis)
    momento = list(snapshots.keys())[0] if snapshots else None

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
        st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:15px;color:#f0c040;text-shadow:0 0 6px #fa0;margin:4px 0 2px;'>F = <b>{_fmt_strike_cfd(_pcp_sb['spot_implicito'])}</b></div><div style='font-size:13px;color:#8a9bb5;margin-bottom:4px;'>ATM: {_fmt_strike_cfd(_pcp_sb['strike_atm'])} &nbsp;|&nbsp; Δ call: {_pcp_sb['delta_call_atm']:.4f}</div>", unsafe_allow_html=True)
        if _pcp_sb.get("delta_flip_abaixo") is not None:
            st.markdown(f"<div style='font-size:13px;color:#8a9bb5;'>Δ flip: {_fmt_strike_cfd(_pcp_sb['delta_flip_abaixo'])} → {_fmt_strike_cfd(_pcp_sb['delta_flip_acima'])}</div>", unsafe_allow_html=True)
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
    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    spot_cfd_str = st.text_input(
        "💱 Spot CFD (ajuste manual):",
        value="",
        placeholder="Ex: 4500  (vazio = sem ajuste)"
    )
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

# ── Offset CFD (display-only) ──
try:
    if spot_cfd_str.strip():
        _spot_cfd_val = float(spot_cfd_str.replace(",", "."))
        if _spot_cfd_val > 0:
            cfd_offset = _spot_cfd_val - spot
        else:
            cfd_offset = 0.0
    else:
        cfd_offset = 0.0
except Exception:
    cfd_offset = 0.0

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
    pcp_label=_fmt_strike_cfd(pcp_spot) if pcp_spot>0 else "—"
    spot_source="PCP" if(modo_spot=="Automático" and pcp_spot>0) else("Manual" if modo_spot=="Manual" else "Δ0.5")
    cfd_tag = f"<span style='font-size:11px;color:#fa0;margin-left:8px;'>+ CFD offset {cfd_offset:+.2f}</span>" if cfd_offset != 0.0 else ""
    st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:13px;color:#0ff;margin:12px 0 2px;letter-spacing:1px;text-shadow:0 0 5px #0ff;'>⚡ SPOT: <b>{_fmt_strike_cfd(spot)}</b><span style='font-size:13px;color:#8a9bb5;margin-left:8px;'>({spot_source})</span>{cfd_tag}</div>", unsafe_allow_html=True)

    if pcp_spot>0:
        with st.expander("📐 Paridade Put-Call — Cálculo Detalhado",expanded=False):
            diff_str=f"+{pcp_res['diferenca']:.3f}" if pcp_res['diferenca']>=0 else f"{pcp_res['diferenca']:.3f}"
            st.markdown(f"<div style='font-family:JetBrains Mono,monospace;font-size:13px;'><div style='font-size:13px;color:#fa0;letter-spacing:2px;margin-bottom:6px;'>FÓRMULA: F = K + (C − P)</div><div style='background:rgba(240,192,64,0.07);border:1px solid rgba(240,192,64,0.3);border-left:4px solid #f0c040;border-radius:8px;padding:10px 14px;margin-bottom:8px;'><div style='font-size:13px;color:#8a9bb5;margin-bottom:4px;'>Strike ATM: <b style='color:#f0c040;'>{_fmt_strike_cfd(pcp_res['strike_atm'])}</b> &nbsp;|&nbsp; Δ call: <b style='color:#f0c040;'>{pcp_res['delta_call_atm']:.4f}</b></div><div style='font-size:13px;color:#8a9bb5;'>C mid = ({pcp_res['c_bid']:.2f} + {pcp_res['c_ask']:.2f}) / 2 = <b style='color:#ccddf8;'>{pcp_res['c_mid']:.3f}</b></div><div style='font-size:13px;color:#8a9bb5;'>P mid = ({pcp_res['p_bid']:.2f} + {pcp_res['p_ask']:.2f}) / 2 = <b style='color:#ccddf8;'>{pcp_res['p_mid']:.3f}</b></div><div style='font-size:13px;color:#8a9bb5;margin-top:4px;'>F = {_fmt_strike_cfd(pcp_res['strike_atm'])} + ({pcp_res['c_mid']:.3f} − {pcp_res['p_mid']:.3f}) = {_fmt_strike_cfd(pcp_res['strike_atm'])} {diff_str} = <b style='color:#f0c040;font-size:14px;text-shadow:0 0 6px #fa0;'>{pcp_label}</b></div></div>", unsafe_allow_html=True)
            flip_ab=pcp_res["delta_flip_abaixo"]; flip_ac=pcp_res["delta_flip_acima"]
            if flip_ab is not None:
                st.markdown(f"<div style='background:rgba(0,255,255,0.05);border:1px solid rgba(0,255,255,0.2);border-left:4px solid #0ff;border-radius:8px;padding:8px 12px;margin-bottom:8px;font-family:JetBrains Mono,monospace;font-size:13px;'><span style='color:#0ff;'>⚡ VALIDAÇÃO DELTA:</span> Strike <b style='color:#f0c040;'>{_fmt_strike_cfd(flip_ab)}</b> (Δ≥0.50) → <b style='color:#f0c040;'>{_fmt_strike_cfd(flip_ac)}</b> (Δ&lt;0.50) &nbsp;→&nbsp; <span style='color:#0f0;'>spot entre {_fmt_strike_cfd(flip_ab)} e {_fmt_strike_cfd(flip_ac)}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='font-size:13px;color:#8a9bb5;margin-bottom:8px;'>⚡ Flip de delta não detectado no range atual.</div>", unsafe_allow_html=True)
            if pcp_res["tabela"]:
                rows_pcp=""
                for e in pcp_res["tabela"]:
                    is_atm=e["K"]==pcp_res["strike_atm"]; row_style="background:rgba(240,192,64,0.08);" if is_atm else ""; star=" ★" if is_atm else ""
                    rows_pcp+=(f"<tr style='{row_style}'><td class='text-gold'>{_fmt_strike_cfd(e['K'])}{star}</td><td style='color:#ccddf8;'>{e['c_bid']:.2f}</td><td style='color:#ccddf8;'>{e['c_ask']:.2f}</td><td style='color:#f0c040;font-weight:bold;'>{e['delta_call']:.4f}</td><td style='color:#ccddf8;'>{e['p_bid']:.2f}</td><td style='color:#ccddf8;'>{e['p_ask']:.2f}</td><td style='color:#0ff;font-weight:bold;'>{e['F']:.2f}</td></tr>")
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
    st.markdown(f"<div class='dashboard-card'><table class='hud-table'><tr><th>NÍVEL</th><th>STRIKE</th><th>VALOR</th><th>AÇÃO</th><th>DIST</th></tr><tr title='{gw_desc}' style='border-bottom:1px solid rgba(255,255,255,0.05);cursor:help;'><td style='font-size:13px;'>🧱 Gamma Wall</td><td class='text-gold'><b>{_fmt_strike_cfd(gamma_wall)}</b></td><td style='color:#0ff;font-size:13px;'>{gex_wall_sign} {gw_val}</td><td style='color:{gw_cor};font-size:13px;'>{gw_acao}</td><td style='color:#8a9bb5;font-size:13px;'>{gw_dist}</td></tr><tr title='{gf_desc}' style='border-bottom:1px solid rgba(255,255,255,0.05);cursor:help;'><td style='font-size:13px;'>⚡ Gamma Flip</td><td class='text-gold'><b>{_fmt_strike_cfd(g_flip)}</b></td><td class='text-dim' style='font-size:13px;'>Zero-crossing</td><td style='color:#ffa500;font-size:13px;'>🔄 Transição</td><td style='color:#8a9bb5;font-size:13px;'>{gf_dist}</td></tr><tr title='{mv_desc}' style='cursor:help;'><td style='font-size:13px;'>🎯 Max Volume</td><td class='text-gold'><b>{_fmt_strike_cfd(max_vol_s)}</b></td><td class='text-dim' style='font-size:13px;'>Pico</td><td style='color:#ffd700;font-size:13px;'>🧲 Magnético</td><td style='color:#8a9bb5;font-size:13px;'>{mv_dist}</td></tr></table><div style='font-size:11px;color:#3a7a8a;margin-top:6px;font-family:JetBrains Mono;'>💡 Passe o mouse nas linhas para ver a interpretação operacional.</div></div>", unsafe_allow_html=True)

    section("ZONAS DE IMPACTO DELTA")
    ri=""
    for _,r in ic_df.iterrows():
        sk=r["strikePrice"]; dist=abs(sk-spot)/spot*100
        if sk>spot: tipo_lbl="<span style='color:#FF4444;font-size:13px;'>⛔ Resistência</span>"; motivo="Call OTM acima do spot. MM vai vender delta se preço subir até aqui."
        else: tipo_lbl="<span style='color:#00FF00;font-size:13px;'>🟢 Suporte</span>"; motivo="Call ITM abaixo do spot. MM já comprou futuros para hedge."
        ri+=f"<tr title='{motivo}' style='cursor:help;'><td>{tipo_lbl}</td><td class='text-gold' style='font-size:13px;'>{_fmt_strike_cfd(sk)}C</td><td style='color:#8a9bb5;font-size:13px;'>{dist:.1f}%</td></tr>"
    for _,r in ip_df.iterrows():
        sk=r["strikePrice"]; dist=abs(sk-spot)/spot*100
        if sk<spot: tipo_lbl="<span style='color:#00FF00;font-size:13px;'>🟢 Suporte</span>"; motivo="Put OTM abaixo do spot. MM vai comprar futuros se preço cair até aqui."
        else: tipo_lbl="<span style='color:#FF4444;font-size:13px;'>⛔ Pressão Vend.</span>"; motivo="Put ITM acima do spot. MM já vendeu futuros para hedge."
        ri+=f"<tr title='{motivo}' style='cursor:help;'><td>{tipo_lbl}</td><td class='text-gold' style='font-size:13px;'>{_fmt_strike_cfd(sk)}P</td><td style='color:#8a9bb5;font-size:13px;'>{dist:.1f}%</td></tr>"
    dex_sorted_df=bar_agg.sort_values("strikePrice"); delta_flip_strike=None
    for i in range(len(dex_sorted_df)-1):
        if dex_sorted_df.iloc[i]["dex_total"]*dex_sorted_df.iloc[i+1]["dex_total"]<0:
            delta_flip_strike=dex_sorted_df.iloc[i+1]["strikePrice"]; break
    delta_flip_html=""
    if delta_flip_strike is not None:
        dist_flip=abs(delta_flip_strike-spot)/spot*100; lado_flip="acima do spot" if delta_flip_strike>spot else "abaixo do spot"
        msg_flip="MM passa de vendido para comprado acima desse nível." if delta_flip_strike>spot else "MM passa de comprado para vendido abaixo desse nível."
        delta_flip_html=(f"<tr style='border-top:1px solid rgba(255,165,0,0.4);'><td colspan='3' style='padding-top:8px;'><span style='color:#ffa500;font-family:JetBrains Mono;font-size:13px;letter-spacing:1px;'>🔄 DELTA FLIP &nbsp;<b style='color:#fff;'>{_fmt_strike_cfd(delta_flip_strike)}</b>&nbsp;<span style='color:#8a9bb5;'>({dist_flip:.1f}% · {lado_flip})</span><br><span style='color:#8a9bb5;font-size:11px;'>Ponto onde pressão direcional muda de sinal. {msg_flip}</span></span></td></tr>")
    st.markdown(f"<div class='dashboard-card'><table class='hud-table'><tr><th>TIPO</th><th>STRIKE</th><th>DIST.</th></tr>{ri}{delta_flip_html}</table><div style='font-size:11px;color:#3a7a8a;margin-top:6px;font-family:JetBrains Mono;'>💡 Passe o mouse nas linhas para ver o motivo da classificação.</div></div>", unsafe_allow_html=True)

    section("VANNA & VOLATILIDADE")
    st.markdown(f"<div class='dashboard-card' style='border-left:4px solid {vol_color};'><div style='display:flex;justify-content:space-between;align-items:center;'><span class='kpi-label' style='font-size:13px;'>{vol_status}</span><span class='tag {tag_vol_cls}'>{vol_status}</span></div><div style='font-family:JetBrains Mono,monospace;font-size:18px;color:#f0f3fa;margin:6px 0;text-shadow:0 0 5px rgba(0,255,255,0.4);'>{fmt_M(net_vanna)}</div><div style='background:rgba(0,255,255,0.04);padding:6px;border-left:3px solid {shock_col};border-radius:6px;font-size:13px;font-family:JetBrains Mono,monospace;'><span class='text-dim'>VANNA LÍQUIDA:</span> <span style='color:{shock_col};font-weight:bold;'>{shock_act} {fmt_M(net_vanna)}</span></div></div>", unsafe_allow_html=True)

    section("TOP VANNA POINTS")
    vrows=""; serie_vanna=strikes_agg["vanna_total"]
    for _,r in top_v.iterrows():
        nv,dc=legenda_vanna_ctx(r["vanna_total"],serie_vanna,r["strikePrice"],spot)
        act="COMPRA" if r["vanna_total"]>0 else "VENDE"; clr="#0f0" if r["vanna_total"]>0 else "#f44"
        vrows+=f"<tr title='{dc}' style='cursor:help;'><td class='text-cyan' style='font-size:13px;'>🐳 {_fmt_strike_cfd(r['strikePrice'])}{r['optionType'][0]}</td><td style='color:{clr};font-weight:bold;font-size:13px;'>{act}</td><td class='text-gold' style='font-size:13px;'>{fmt_M(r['vanna_total'])}</td><td style='color:#8a9bb5;font-size:11px;'>{nv}</td></tr>"
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
    if g_flip>0 and abs(g_flip-spot)/spot<0.005: notas.append(("info",f"🎯 ZONA CRÍTICA: Spot próximo ao Gamma Flip ({_fmt_strike_cfd(g_flip)})"))
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
                x=_df_v["strikePrice"] + cfd_offset, y=_df_v["Vol_OI"],
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
        fig_mom.add_vline(x=spot + cfd_offset, line_dash="dot", line_color=COLOR_NEON, line_width=1.5)
        fig_mom.add_annotation(x=spot + cfd_offset, y=1.0, xref="x", yref="paper",
            text=f"SPOT {_fmt_strike_cfd(spot)}", showarrow=False, yshift=8,
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
                f"⚡ Máx. urgência: <b>Strike {_fmt_strike_cfd(_mx['strikePrice'])}</b> · "
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
                st.markdown(f"<div class='whale-card' title='{desc}'><b class='text-cyan' style='font-size:13px;'>{_fmt_strike_cfd(sk)}C</b> <span style='color:{cor};font-size:13px;font-weight:bold;'>{acao}</span><span class='text-dim' style='float:right;font-size:13px;'>{dist_fmt} do spot</span><br><span class='text-green' style='font-size:13px;'>z={row['z_score']:.1f}</span><span class='text-dim' style='font-size:13px;'> &nbsp;·&nbsp; ΔFlow {fmt_M(row['d_flow'])} &nbsp;·&nbsp; Vol {row['volume']:,.0f} &nbsp;·&nbsp; Fin {fmt_M(row.get('financial_flow',0))}</span></div>", unsafe_allow_html=True)
        else: st.caption("Sem anomalias.")
    with wc2:
        st.markdown("<div style='color:#f44;font-size:13px;font-weight:bold;letter-spacing:1px;margin-bottom:8px;font-family:JetBrains Mono,monospace;'>🔴 PUTS — IMPACTO MM</div>", unsafe_allow_html=True)
        if not w_puts_agg.empty:
            for _,row in w_puts_agg.iterrows():
                sk=row["strikePrice"]; acao,cor,desc,dist_fmt=legenda_whale_ctx(sk,"Put",spot)
                st.markdown(f"<div class='whale-card' title='{desc}'><b class='text-cyan' style='font-size:13px;'>{_fmt_strike_cfd(sk)}P</b> <span style='color:{cor};font-size:13px;font-weight:bold;'>{acao}</span><span class='text-dim' style='float:right;font-size:13px;'>{dist_fmt} do spot</span><br><span class='text-red' style='font-size:13px;'>z={row['z_score']:.1f}</span><span class='text-dim' style='font-size:13px;'> &nbsp;·&nbsp; ΔFlow {fmt_M(abs(row['d_flow']))} &nbsp;·&nbsp; Vol {row['volume']:,.0f} &nbsp;·&nbsp; Fin {fmt_M(row.get('financial_flow',0))}</span></div>", unsafe_allow_html=True)
        else: st.caption("Sem anomalias.")
# ══════════════════════════════════════════════════════════════════
# 17 · GERADOR DE INDICADOR TRADINGVIEW (PINE SCRIPT)
# ──────────────────────────────────────────────────────────────────
# Anexar ao FINAL dos dashboards NQ / SP500 / GLD,
# logo após o "RADAR INSTITUCIONAL" e ANTES do rodapé.
#
# Reaproveita variáveis já em escopo:
#   • df_raw    — DataFrame parseado bruto
#   • df        — output de calcular_v9 (já filtrado pela sidebar)
#   • spot      — spot detectado em USD
#   • cfd_offset — offset display-only (CFD - implied)
#   • momento   — snapshot
#   • MULTIPLICADOR_FIXO
# ══════════════════════════════════════════════════════════════════

from collections import defaultdict

# ─────────────────────────────────────────────────────────────────
# 17.0 · CONFIGURAÇÃO POR DASHBOARD  ← AJUSTAR APENAS ESTA LINHA
# ─────────────────────────────────────────────────────────────────
_PINE_ATIVO = "NASDAQ"   # "NASDAQ" | "SP500" | "GOLD"

_PINE_CONFIGS = {
    "NASDAQ": dict(
        nome              = "NASDAQ",
        tickers           = ["US100", "USATECM2026", "USTEC", "MNQ1!", "NQ1!"],
        filename          = "Gamma Levels NASDAQ.txt",
        meia_altura       = 10,         # meia-altura barras Pine (em USD)
        offset_split      = 25,         # offset vertical quando >3 niveis no mesmo strike
        win_focus_pct     = 0.02,       # ±2% do spot
    ),
    "SP500": dict(
        nome              = "SP500",
        tickers           = ["US500", "ES1!", "MES1!", "USA500M2026"],
        filename          = "Gamma Levels SP500.txt",
        meia_altura       = 2,
        offset_split      = 5,
        win_focus_pct     = 0.02,
    ),
    "GOLD": dict(
        nome              = "OURO",
        tickers           = ["GOLD", "XAUUSD", "GCZ2025", "MGCZ2025", "GC1!", "MGC1!"],
        filename          = "Gamma Levels OURO.txt",
        meia_altura       = 1,
        offset_split      = 2,
        win_focus_pct     = 0.02,
    ),
}
_CFG = _PINE_CONFIGS[_PINE_ATIVO]


# ─────────────────────────────────────────────────────────────────
# 17.1 · TEMPLATE PINE SCRIPT (parametrizado)
# ─────────────────────────────────────────────────────────────────
_PINE_TEMPLATE = r"""//@version=6
indicator('GAMMA-LEVELS/GEX/DEX – __ATIVO_NOME__', overlay=true, max_bars_back=1000, max_labels_count=500, max_lines_count=500, max_boxes_count=1000)

// ===============================================
// VARIÁVEIS GLOBAIS
// ===============================================
var line[]  lines  = array.new_line()
var label[] labels = array.new_label()
var box[]   boxes  = array.new_box()

// ===============================================
// PARÂMETROS VISUAIS — GEX/Volume (G/V)
// ===============================================
grpGV = "Visual - GEX/Volume (G/V)"
gv_escala_maxima = input.float(50.0, "Escala Máxima das Barras (G/V)", group=grpGV)
gv_offset_barras = input.int(-50, "Distância horizontal (G/V)", group=grpGV, tooltip="Distância a partir da borda esquerda. Positivo = direita do left_index.")
gv_dist_y        = input.float(__MEIA_ALTURA__, "Meia-altura da barra G/V (USD)", group=grpGV, tooltip="Metade da altura de cada barra em USD do __ATIVO_NOME__.")
gv_opacidade     = input.int(20, "Opacidade (G/V)", minval=0, maxval=100, group=grpGV)
gv_cor_net_pos   = input.color(color.rgb(131, 20, 196), "Cor NET GEX + (esquerda)", group=grpGV)
gv_cor_net_neg   = input.color(color.new(#ea0c0c, 0),   "Cor NET GEX - (esquerda)", group=grpGV)
gv_cor_vol_call  = input.color(color.new(color.red, 0),   "Cor Volume CALL (direita)", group=grpGV)
gv_cor_vol_put   = input.color(color.new(color.green, 0), "Cor Volume PUT (direita)", group=grpGV)
gv_min_volume    = input.float(0.0, "Volume mínimo por strike (G/V)", minval=0, group=grpGV)

// ===============================================
// PARÂMETROS VISUAIS — DEX (Δ)
// ===============================================
grpDEX = "Visual - DEX (Δ)"
dex_escala_maxima = input.float(50.0, "Escala Máxima das Barras (Δ)", group=grpDEX)
dex_offset_barras = input.int(125, "Distância horizontal (Δ)", group=grpDEX, tooltip="Distância a partir da borda esquerda.")
dex_dist_y        = input.float(__MEIA_ALTURA__, "Meia-altura da barra DEX (USD)", group=grpDEX, tooltip="Metade da altura de cada barra em USD do __ATIVO_NOME__.")
dex_opacidade     = input.int(20, "Transparência (Δ)", minval=0, maxval=100, group=grpDEX)
dex_cor_delta_pos = input.color(color.rgb(20, 160, 60),  "Cor Δ POSITIVO", group=grpDEX)
dex_cor_delta_neg = input.color(color.rgb(234, 12, 12),  "Cor Δ NEGATIVO", group=grpDEX)

// ===============================================
// PARÂMETROS VISUAIS — Camada OI (Transparente)
// ===============================================
grpOI = "Visual - Camada OI (Transparente)"
oi_opacidade = input.int(65, "Opacidade OI (mais transparente)", minval=0, maxval=100, group=grpOI)

// ===============================================
// FUNÇÕES AUXILIARES
// ===============================================
f_ts_brt(y, m, d, hh, mm) =>
    timestamp("America/Sao_Paulo", y, m, d, hh, mm)

get_open_day_window() =>
    yBR = year(time, "America/Sao_Paulo")
    mBR = month(time, "America/Sao_Paulo")
    dBR = dayofmonth(time, "America/Sao_Paulo")
    todayOpenBR = f_ts_brt(yBR, mBR, dBR, 19, 0)
    lastOpenTs  = time >= todayOpenBR ? todayOpenBR : (todayOpenBR - 24 * 60 * 60 * 1000)
    dayEnd      = time
    [lastOpenTs, dayEnd]

getLineStyle(styleStr) =>
    styleStr == "Sólido" ? line.style_solid : styleStr == "Tracejado" ? line.style_dashed : line.style_dotted

clear_objects() =>
    for l in lines
        line.delete(l)
    array.clear(lines)
    for lb in labels
        label.delete(lb)
    array.clear(labels)

create_indicator(name, yValue, lineColor, lineStyleInput) =>
    [dayStart, dayEnd] = get_open_day_window()
    ls = getLineStyle(lineStyleInput)
    l  = line.new(x1=dayStart, y1=yValue, x2=dayEnd, y2=yValue, color=lineColor, width=2, style=ls, xloc=xloc.bar_time)
    array.push(lines, l)
    lb = label.new(x=dayEnd, y=yValue, text=name + ' (' + str.tostring(yValue) + ')', style=label.style_label_left, color=color.new(lineColor, 100), textcolor=lineColor, xloc=xloc.bar_time)
    array.push(labels, lb)

// ===============================================
// ARRAYS — __ATIVO_NOME__ (gerados pelo dashboard)
// ===============================================
__ARRAYS_PLACEHOLDER__

// ===============================================
// SELEÇÃO DE ARRAYS
// ===============================================
ativo = syminfo.ticker
is_active = __IS_ACTIVE_EXPR__

gex_strikes        = is_active ? unified_gex_strikes        : array.new_float(0)
gex_call_values    = is_active ? unified_gex_call_values    : array.new_float(0)
gex_put_values     = is_active ? unified_gex_put_values     : array.new_float(0)
gex_oi_call_values = is_active ? unified_gex_oi_call_values : array.new_float(0)
gex_oi_put_values  = is_active ? unified_gex_oi_put_values  : array.new_float(0)
vol_strikes        = is_active ? unified_vol_strikes        : array.new_float(0)
vol_call_values    = is_active ? unified_vol_call_values    : array.new_float(0)
vol_put_values     = is_active ? unified_vol_put_values     : array.new_float(0)
dex_strikes        = is_active ? unified_dex_strikes        : array.new_float(0)
dex_call_values    = is_active ? unified_dex_call_values    : array.new_float(0)
dex_put_values     = is_active ? unified_dex_put_values     : array.new_float(0)
dex_oi_call_values = is_active ? unified_dex_oi_call_values : array.new_float(0)
dex_oi_put_values  = is_active ? unified_dex_oi_put_values  : array.new_float(0)

// ===============================================
// NÍVEIS INSTITUCIONAIS EM LINHAS
// ===============================================
display_levels() =>
    if is_active
__NIVEIS_PLACEHOLDER__

// ===============================================
// PRÉ-CÁLCULO: posição horizontal das barras
// ===============================================
left_time  = chart.left_visible_bar_time
cond       = not na(left_time) ? time >= left_time : true
left_index = ta.valuewhen(cond, bar_index, 0)

// ===============================================
// DESENHO DAS BARRAS (GEX, VOLUME, DEX)
// ===============================================
if barstate.islast
    sz = array.size(boxes)
    if sz > 0
        for b = 0 to sz - 1
            box.delete(array.get(boxes, b))
        array.clear(boxes)

    x_base_gv  = left_index + gv_offset_barras
    x_base_dex = left_index + dex_offset_barras

    // ── NET GEX VOL e OI (lado esquerdo) ───────────────────────────
    valid_gex = math.min(array.size(gex_strikes), array.size(gex_call_values))
    valid_gex := math.min(valid_gex, array.size(gex_put_values))

    if valid_gex > 0
        abs_nets_vol = array.new_float()
        for i = 0 to valid_gex - 1
            n = array.get(gex_call_values, i) + array.get(gex_put_values, i)
            if n != 0
                array.push(abs_nets_vol, math.abs(n))
        max_gex_vol = array.size(abs_nets_vol) > 0 ? array.percentile_linear_interpolation(abs_nets_vol, 95) : 1.0
        max_gex_vol := max_gex_vol == 0 ? 1.0 : max_gex_vol

        abs_nets_oi = array.new_float()
        for i = 0 to valid_gex - 1
            n = array.get(gex_oi_call_values, i) + array.get(gex_oi_put_values, i)
            if n != 0
                array.push(abs_nets_oi, math.abs(n))
        max_gex_oi = array.size(abs_nets_oi) > 0 ? array.percentile_linear_interpolation(abs_nets_oi, 95) : 1.0
        max_gex_oi := max_gex_oi == 0 ? 1.0 : max_gex_oi

        for i = 0 to valid_gex - 1
            sk      = array.get(gex_strikes, i)
            net_vol = array.get(gex_call_values, i)    + array.get(gex_put_values, i)
            net_oi  = array.get(gex_oi_call_values, i) + array.get(gex_oi_put_values, i)

            if net_oi != 0
                norm_oi = math.min(math.abs(net_oi) / max_gex_oi, 1.0) * gv_escala_maxima
                cor_oi  = net_oi > 0 ? color.new(gv_cor_net_pos, oi_opacidade) : color.new(gv_cor_net_neg, oi_opacidade)
                array.push(boxes, box.new(left=x_base_gv - int(norm_oi), top=sk + gv_dist_y, right=x_base_gv, bottom=sk - gv_dist_y, xloc=xloc.bar_index, bgcolor=cor_oi, border_color=na, border_width=0))

            if net_vol != 0
                norm_vol = math.min(math.abs(net_vol) / max_gex_vol, 1.0) * gv_escala_maxima
                cor_vol  = net_vol > 0 ? color.new(gv_cor_net_pos, gv_opacidade) : color.new(gv_cor_net_neg, gv_opacidade)
                array.push(boxes, box.new(left=x_base_gv - int(norm_vol), top=sk + gv_dist_y, right=x_base_gv, bottom=sk - gv_dist_y, xloc=xloc.bar_index, bgcolor=cor_vol, border_color=na, border_width=0))

    // ── VOLUME DOMINANTE (lado direito) ────────────────────────────
    valid_vol = math.min(array.size(vol_strikes), array.size(vol_call_values))
    valid_vol := math.min(valid_vol, array.size(vol_put_values))

    if valid_vol > 0
        max_vol = 0.0
        for i = 0 to valid_vol - 1
            max_vol := math.max(max_vol, math.max(array.get(vol_call_values, i), array.get(vol_put_values, i)))
        max_vol := max_vol == 0 ? 1.0 : max_vol

        opa_v = int(math.min(gv_opacidade + 10, 100))
        for i = 0 to valid_vol - 1
            sk  = array.get(vol_strikes, i)
            cv  = array.get(vol_call_values, i)
            pv  = array.get(vol_put_values, i)
            dom = math.max(cv, pv)
            if dom >= gv_min_volume
                norm  = (dom / max_vol) * gv_escala_maxima
                cor_v = cv >= pv ? color.new(gv_cor_vol_call, opa_v) : color.new(gv_cor_vol_put, opa_v)
                array.push(boxes, box.new(left=x_base_gv, top=sk + gv_dist_y, right=x_base_gv + int(norm), bottom=sk - gv_dist_y, xloc=xloc.bar_index, bgcolor=cor_v, border_color=na, border_width=0))

    // ── NET DEX VOL e OI ───────────────────────────────────────────
    valid_dex = math.min(array.size(dex_strikes), array.size(dex_call_values))
    valid_dex := math.min(valid_dex, array.size(dex_put_values))

    if valid_dex > 0
        abs_nets_dex_vol = array.new_float()
        for i = 0 to valid_dex - 1
            n = array.get(dex_call_values, i) + array.get(dex_put_values, i)
            if n != 0
                array.push(abs_nets_dex_vol, math.abs(n))
        max_dex_vol = array.size(abs_nets_dex_vol) > 0 ? array.percentile_linear_interpolation(abs_nets_dex_vol, 95) : 1.0
        max_dex_vol := max_dex_vol == 0 ? 1.0 : max_dex_vol

        abs_nets_dex_oi = array.new_float()
        for i = 0 to valid_dex - 1
            n = array.get(dex_oi_call_values, i) + array.get(dex_oi_put_values, i)
            if n != 0
                array.push(abs_nets_dex_oi, math.abs(n))
        max_dex_oi = array.size(abs_nets_dex_oi) > 0 ? array.percentile_linear_interpolation(abs_nets_dex_oi, 95) : 1.0
        max_dex_oi := max_dex_oi == 0 ? 1.0 : max_dex_oi

        for i = 0 to valid_dex - 1
            sk      = array.get(dex_strikes, i)
            net_vol = array.get(dex_call_values, i)    + array.get(dex_put_values, i)
            net_oi  = array.get(dex_oi_call_values, i) + array.get(dex_oi_put_values, i)

            if net_oi != 0
                norm_oi = math.min(math.abs(net_oi) / max_dex_oi, 1.0) * dex_escala_maxima
                cor_oi  = net_oi > 0 ? color.new(dex_cor_delta_pos, oi_opacidade) : color.new(dex_cor_delta_neg, oi_opacidade)
                array.push(boxes, box.new(left=x_base_dex - int(norm_oi), top=sk + dex_dist_y, right=x_base_dex, bottom=sk - dex_dist_y, xloc=xloc.bar_index, bgcolor=cor_oi, border_color=na, border_width=0))

            if net_vol != 0
                norm_vol = math.min(math.abs(net_vol) / max_dex_vol, 1.0) * dex_escala_maxima
                cor_vol  = net_vol > 0 ? color.new(dex_cor_delta_pos, dex_opacidade) : color.new(dex_cor_delta_neg, dex_opacidade)
                array.push(boxes, box.new(left=x_base_dex - int(norm_vol), top=sk + dex_dist_y, right=x_base_dex, bottom=sk - dex_dist_y, xloc=xloc.bar_index, bgcolor=cor_vol, border_color=na, border_width=0))

// ===============================================
// LINHAS E RÓTULOS
// ===============================================
clear_objects()
display_levels()

plot(na, title="__dummy__", display=display.none)
"""


# ─────────────────────────────────────────────────────────────────
# 17.2 · HELPERS NUMÉRICOS LOCAIS
# ─────────────────────────────────────────────────────────────────
def _gp_clean(v) -> float:
    try:
        v = float(v)
        return 0.0 if (math.isnan(v) or math.isinf(v)) else v
    except Exception:
        return 0.0

def _gp_fmt_num(v) -> str:
    """
    Formata float pra inclusão no array.from() do Pine.
    SEMPRE preserva o ponto decimal: '29500' viraria array<int> no Pine v6
    e quebraria o ternário 'is_active ? array<float> : array.new_float(0)'.
    """
    fv = float(v)
    s = f"{fv:.4f}".rstrip("0").rstrip(".")
    if "." not in s:
        s += ".0"
    return s


# ─────────────────────────────────────────────────────────────────
# 17.3 · BUILD ARRAYS — agregação por strike (sem z-score, sem peso)
# ─────────────────────────────────────────────────────────────────

def _gp_build_arrays_block(df_pine: pd.DataFrame, spot: float,
                            s_lo: float, s_hi: float, cfd_off: float,
                            snapshot: str) -> tuple:
    """
    Agrega df_pine (output de calcular_v9) por (strikePrice, optionType).
    Já filtrado em ±2% do spot.
    Aplica cfd_offset aos strikes para alinhar com o chart do TradingView.
    Puts ficam com sinal negativo (convenção do Pine que renderiza
    'CALL + | PUT -' nas barras).
    """
    if df_pine.empty:
        return "", []

    d = df_pine[
        (df_pine["strikePrice"] >= s_lo) &
        (df_pine["strikePrice"] <= s_hi)
    ].copy()
    if d.empty:
        return "", []

    calls = d[d["optionType"] == "Call"].groupby("strikePrice").agg(
        gex_total=("gex_total", "sum"),
        gex_oi   =("gex_oi",    "sum"),
        dex_total=("dex_total", "sum"),
        dex_oi   =("dex_oi",    "sum"),
        volume   =("volume",    "sum"),
        oi       =("openInterest", "sum"),
    )
    puts = d[d["optionType"] == "Put"].groupby("strikePrice").agg(
        gex_total=("gex_total", "sum"),
        gex_oi   =("gex_oi",    "sum"),
        dex_total=("dex_total", "sum"),
        dex_oi   =("dex_oi",    "sum"),
        volume   =("volume",    "sum"),
        oi       =("openInterest", "sum"),
    )

    # Convenção Pine: puts com sinal negativo nos arrays
    for col in ("gex_total", "gex_oi", "dex_total", "dex_oi"):
        puts[col] = -puts[col].abs()

    all_strikes = sorted(set(calls.index) | set(puts.index))
    if not all_strikes:
        return "", []

    strikes      = []
    g_calls      = []; g_puts      = []
    g_oi_calls   = []; g_oi_puts   = []
    v_calls      = []; v_puts      = []
    d_calls      = []; d_puts      = []
    d_oi_calls   = []; d_oi_puts   = []
    d_net        = []

    for sk in all_strikes:
        c = calls.loc[sk] if sk in calls.index else None
        p = puts.loc[sk]  if sk in puts.index  else None
        val_c = _gp_clean(c["dex_total"] if c is not None else 0)
        val_p = _gp_clean(p["dex_total"] if p is not None else 0)

        strikes.append(   _gp_fmt_num(sk + cfd_off))
        g_calls.append(   _gp_fmt_num(_gp_clean(c["gex_total"] if c is not None else 0)))
        g_puts.append(    _gp_fmt_num(_gp_clean(p["gex_total"] if p is not None else 0)))
        g_oi_calls.append(_gp_fmt_num(_gp_clean(c["gex_oi"]    if c is not None else 0)))
        g_oi_puts.append( _gp_fmt_num(_gp_clean(p["gex_oi"]    if p is not None else 0)))
        v_calls.append(   _gp_fmt_num(_gp_clean(c["volume"]    if c is not None else 0)))
        v_puts.append(    _gp_fmt_num(_gp_clean(p["volume"]    if p is not None else 0)))
        d_calls.append(   _gp_fmt_num(val_c))
        d_puts.append(    _gp_fmt_num(val_p))
        d_oi_calls.append(_gp_fmt_num(_gp_clean(c["dex_oi"]    if c is not None else 0)))
        d_oi_puts.append( _gp_fmt_num(_gp_clean(p["dex_oi"]    if p is not None else 0)))
        d_net.append(     _gp_fmt_num(val_c + val_p))

    cfd_tag = f"  |  CFD offset: {cfd_off:+.2f}" if cfd_off != 0.0 else ""
    header = (
        f"// ═══════════════════════════════════════════════════════\n"
        f"// ARRAYS — {_CFG['nome']} (agregação direta, sem z-score)\n"
        f"// Snapshot: {snapshot}  |  Spot: {spot:.2f}{cfd_tag}\n"
        f"// Janela: ±{_CFG['win_focus_pct']*100:.0f}% = [{s_lo:.2f}, {s_hi:.2f}]\n"
        f"// Strikes: {len(strikes)}\n"
        f"// Gerado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"// ═══════════════════════════════════════════════════════"
    )

    linhas = [
        header,
        f"unified_gex_strikes        = array.from({', '.join(strikes)})",
        f"unified_gex_call_values    = array.from({', '.join(g_calls)})",
        f"unified_gex_put_values     = array.from({', '.join(g_puts)})",
        f"unified_gex_oi_call_values = array.from({', '.join(g_oi_calls)})",
        f"unified_gex_oi_put_values  = array.from({', '.join(g_oi_puts)})",
        f"unified_vol_strikes        = array.from({', '.join(strikes)})",
        f"unified_vol_call_values    = array.from({', '.join(v_calls)})",
        f"unified_vol_put_values     = array.from({', '.join(v_puts)})",
        f"unified_dex_strikes        = array.from({', '.join(strikes)})",
        f"unified_dex_call_values    = array.from({', '.join(d_calls)})",
        f"unified_dex_put_values     = array.from({', '.join(d_puts)})",
        f"unified_dex_oi_call_values = array.from({', '.join(d_oi_calls)})",
        f"unified_dex_oi_put_values  = array.from({', '.join(d_oi_puts)})",
        f"unified_dex_net_values     = array.from({', '.join(d_net)})",
    ]
    return "\n".join(linhas), all_strikes


# ─────────────────────────────────────────────────────────────────
# 17.4 · CÁLCULO DE NÍVEIS INSTITUCIONAIS (USD-space, sem bucket)
# ─────────────────────────────────────────────────────────────────

def _gp_calcular_niveis(df_pine: pd.DataFrame, spot: float) -> list:
    if df_pine.empty:
        return []

    niveis = []
    def add(nome, strike, cor, estilo):
        niveis.append(dict(
            nome=nome, strike=float(strike),
            cor_pine=cor, estilo=estilo,
        ))

    agg = df_pine.groupby("strikePrice").agg(
        gex_total =("gex_total", "sum"),
        gex_oi    =("gex_oi",    "sum"),
        dex_total =("dex_total", "sum"),
        dex_oi    =("dex_oi",    "sum"),
        vanna_total=("vanna_total", "sum"),
        volume    =("volume", "sum"),
        openInterest=("openInterest", "sum"),
        financial_flow=("financial_flow", "sum"),
    ).sort_index()

    calls_agg = df_pine[df_pine["optionType"] == "Call"].groupby("strikePrice").agg(
        volume        =("volume", "sum"),
        openInterest  =("openInterest", "sum"),
        financial_flow=("financial_flow", "sum"),
        dex_total     =("dex_total", "sum"),
    ).sort_index()
    puts_agg = df_pine[df_pine["optionType"] == "Put"].groupby("strikePrice").agg(
        volume        =("volume", "sum"),
        openInterest  =("openInterest", "sum"),
        financial_flow=("financial_flow", "sum"),
        dex_total     =("dex_total", "sum"),
    ).sort_index()

    gex_s   = agg["gex_total"]
    dex_s   = agg["dex_total"]
    strikes = gex_s.index.tolist()

    # ── GAMMA WALL ───────────────────────────────────────────────
    gamma_wall = float(gex_s.abs().idxmax()) if not gex_s.empty else float(spot)
    lbl_gw = ("MAX GEX | GAMMA WALL | MM VENDE" if gamma_wall > spot
              else "MAX GEX | GAMMA WALL | MM COMPRA")
    add(lbl_gw, gamma_wall, "color.rgb(57,142,232)", "Sólido")

    # ── GAMMA FLIP (zero-cross interpolado) ──────────────────────
    gamma_flip = None
    for i in range(len(strikes) - 1):
        g0 = gex_s.iloc[i]; g1 = gex_s.iloc[i + 1]
        if g0 * g1 < 0:
            k0 = strikes[i]; k1 = strikes[i + 1]
            gamma_flip = k0 + (k1 - k0) * (-g0) / (g1 - g0)
            break
    if gamma_flip is None:
        gamma_flip = float(gex_s.abs().idxmin()) if not gex_s.empty else float(spot)
    add("GAMMA FLIP (EST) | Divisor de Regime",
        gamma_flip, "color.rgb(82,157,255)", "Sólido")

    # ── MAX VOL ──────────────────────────────────────────────────
    vol_s = agg["volume"]
    if not vol_s.empty and vol_s.sum() > 0:
        add("MAX VOL | Imã de Liquidez",
            float(vol_s.idxmax()), "color.rgb(240,192,64)", "Tracejado")

    # ── DELTA FLIP ───────────────────────────────────────────────
    df_encontrado = False
    for i in range(len(strikes) - 1):
        d0 = dex_s.iloc[i]; d1 = dex_s.iloc[i + 1]
        if d0 * d1 < 0:
            add("DELTA FLIP | Inversao de Risco",
                float(strikes[i + 1]), "color.rgb(82,157,255)", "Sólido")
            df_encontrado = True
            break
    if not df_encontrado and not dex_s.empty:
        add("DELTA FLIP (EST) | Inversao de Risco",
            float(dex_s.abs().idxmin()), "color.rgb(82,157,255)", "Sólido")

    # ── CALL/PUT WALLS ───────────────────────────────────────────
    if not calls_agg.empty and calls_agg["volume"].sum() > 0:
        add("CALL WALL (VOL) | Resistencia de Fluxo",
            float(calls_agg["volume"].idxmax()), "color.rgb(176,39,46)", "Tracejado")
    if not calls_agg.empty and calls_agg["openInterest"].sum() > 0:
        add("CALL WALL (OI) | Teto Estrutural",
            float(calls_agg["openInterest"].idxmax()), "color.rgb(176,39,46)", "Sólido")
    if not puts_agg.empty and puts_agg["volume"].sum() > 0:
        add("PUT WALL (VOL) | Defesa de Fluxo",
            float(puts_agg["volume"].idxmax()), "color.rgb(82,157,255)", "Tracejado")
    if not puts_agg.empty and puts_agg["openInterest"].sum() > 0:
        add("PUT WALL (OI) | Muro Estrutural",
            float(puts_agg["openInterest"].idxmax()), "color.rgb(82,157,255)", "Sólido")

    # ── DEX-C top 2 ──────────────────────────────────────────────
    if not calls_agg.empty:
        for sk in calls_agg["dex_total"].nlargest(2).index:
            lbl = ("DELTA POS (VOL) | Amplificacao de Compra" if sk > spot
                   else "DELTA NEG (VOL) | Defesa Ativa Venda")
            cor = ("color.rgb(82,157,255)" if sk > spot
                   else "color.rgb(235,12,12)")
            add(lbl, float(sk), cor, "Tracejado")

    # ── DEX-P top 2 ──────────────────────────────────────────────
    if not puts_agg.empty:
        for sk in puts_agg["dex_total"].nsmallest(2).index:
            lbl = ("DELTA NEG (VOL) | Defesa Ativa Venda" if sk > spot
                   else "DELTA POS (VOL) | Amplificacao de Compra")
            cor = ("color.rgb(235,12,12)" if sk > spot
                   else "color.rgb(82,157,255)")
            add(lbl, float(sk), cor, "Tracejado")

    # ── TOP VANNA ────────────────────────────────────────────────
    vanna_s = agg["vanna_total"]
    if not vanna_s.empty:
        for sk in vanna_s.abs().nlargest(3).index:
            val = vanna_s[sk]; pos = val > 0
            lbl = ("VANNA + | Pressao Compradora" if pos
                   else "VANNA - | Pressao Vendedora")
            cor = "color.rgb(0,230,118)" if pos else "color.rgb(255,23,68)"
            add(lbl, float(sk), cor, "Tracejado")

    # ── VOL TRIGGER ──────────────────────────────────────────────
    vol_trigger = (gamma_flip + 0.75 * (gamma_wall - gamma_flip)
                   if gamma_wall != gamma_flip else gamma_flip)
    add("VOL TRIGGER | Perda de Controle",
        vol_trigger, "color.rgb(76,87,77)", "Sólido")

    # ── GEX OI / DEX OI POS-NEG ──────────────────────────────────
    goi = agg["gex_oi"]
    if not goi.empty:
        add("MAX GEX | GAMMA POS (OI) | Suporte Estrutural",
            float(goi.idxmax()), "color.rgb(57,142,232)", "Sólido")
        add("MIN GEX | GAMMA NEG (OI) | VOL ATTACK | Risco Estrutural",
            float(goi.idxmin()), "color.rgb(91,2,2)", "Sólido")
    doi = agg["dex_oi"]
    if not doi.empty:
        add("DELTA POS (OI) | MM Vendido Estrutural",
            float(doi.idxmax()), "color.rgb(57,142,232)", "Sólido")
        add("DELTA NEG (OI) | MM Comprado Estrutural",
            float(doi.idxmin()), "color.rgb(91,2,2)", "Sólido")

    # ── GEX/DEX VOL POS-NEG ──────────────────────────────────────
    if not gex_s.empty:
        add("GAMMA POS (VOL) | Zona de Atracao",
            float(gex_s.idxmax()), "color.rgb(82,157,255)", "Tracejado")
        add("GAMMA NEG (VOL) | Pressao de Venda",
            float(gex_s.idxmin()), "color.rgb(235,12,12)", "Tracejado")
    if not dex_s.empty:
        add("DELTA POS (VOL) | Amplificacao de Compra",
            float(dex_s.idxmax()), "color.rgb(82,157,255)", "Tracejado")
        add("DELTA NEG (VOL) | Defesa Ativa Venda",
            float(dex_s.idxmin()), "color.rgb(235,12,12)", "Tracejado")

    add("SPOT", float(spot), "color.gray", "Sólido")

    return sorted(niveis, key=lambda x: x["strike"], reverse=True)


# ─────────────────────────────────────────────────────────────────
# 17.5 · AGRUPAMENTO DE NÍVEIS POR STRIKE EXATO
# ─────────────────────────────────────────────────────────────────
_GP_MAX_TAGS = 3

def _gp_prioridade(nome: str) -> int:
    n = nome.upper()
    if "GAMMA WALL" in n or "VOL ATTACK" in n:   return 5
    if "GAMMA FLIP" in n or "DELTA FLIP" in n:   return 4
    if "VOL TRIGGER" in n:                        return 4
    if "(OI)" in n:                               return 3
    if "MAX VOL" in n:                            return 2
    if "(VOL)" in n or "VANNA" in n:              return 1
    if "SPOT" in n:                               return 0
    return 1

def _gp_tag_curta(nome: str) -> str:
    parte = nome.split("|")[0].strip()
    mapa = {
        "MAX VOL":                            "MAX-VOL",
        "MAX GEX | GAMMA WALL | MM VENDE":    "Gamma (VENDE)",
        "MAX GEX | GAMMA WALL | MM COMPRA":   "Gamma (COMPRA)",
        "MAX GEX | GAMMA WALL":               "Gamma Wall",
        "GAMMA FLIP (EST)":                   "Gamma FLIP",
        "GAMMA FLIP":                         "Gamma FLIP",
        "DELTA FLIP (EST)":                   "Delta FLIP",
        "DELTA FLIP":                         "Delta FLIP",
        "VOL TRIGGER":                        "VOL-TRIG",
        "CALL WALL (OI)":                     "Call Wall-OI",
        "PUT WALL (OI)":                      "Put Wall-OI",
        "CALL WALL (VOL)":                    "Call Wall VOL",
        "PUT WALL (VOL)":                     "Put Wall VOL",
        "MAX GEX | GAMMA POS (OI)":           "Gamma Pos. OI",
        "MIN GEX | GAMMA NEG (OI)":           "Gamma Neg. OI",
        "GAMMA POS (VOL)":                    "Gamma Pos. Vol",
        "GAMMA NEG (VOL)":                    "Gamma Neg. Vol",
        "DELTA POS (OI)":                     "Delta Pos. OI",
        "DELTA NEG (OI)":                     "Delta Neg. OI",
        "DELTA POS (VOL)":                    "Delta Pos VOL",
        "DELTA NEG (VOL)":                    "Delta Neg. VOL",
        "VANNA +":                            "VANNA+",
        "VANNA -":                            "VANNA-",
    }
    pu = parte.upper()
    for chave, abrev in mapa.items():
        if chave.upper() in pu:
            return abrev
    return parte[:20].strip()

def _gp_cor_do_grupo(itens: list) -> tuple:
    melhor = max(itens, key=lambda x: _gp_prioridade(x["nome"]))
    return melhor["cor_pine"], melhor["estilo"]

def _gp_agrupar_niveis(niveis_raw: list, cfd_off: float) -> list:
    """
    Agrupa por strike EXATO (sem bucket). Aplica cfd_offset no Y de saída.
    Quando >3 niveis coincidem no mesmo strike, divide em blocos com offset.
    """
    por_strike = defaultdict(list)
    for n in niveis_raw:
        # arredonda para 4 casas pra evitar floats infinitesimalmente diferentes
        chave = round(n["strike"], 4)
        por_strike[chave].append(n)

    resultado = []
    for strike in sorted(por_strike.keys(), reverse=True):
        itens = sorted(por_strike[strike],
                       key=lambda x: _gp_prioridade(x["nome"]), reverse=True)
        if len(itens) == 1:
            it = itens[0]
            resultado.append({
                "label":  it["nome"],
                "strike": strike + cfd_off,
                "cor":    it["cor_pine"],
                "estilo": it["estilo"],
            })
        elif len(itens) <= _GP_MAX_TAGS:
            cor, est = _gp_cor_do_grupo(itens)
            resultado.append({
                "label":  " + ".join(_gp_tag_curta(it["nome"]) for it in itens),
                "strike": strike + cfd_off,
                "cor":    cor, "estilo": est,
            })
        else:
            grupos = [itens[i:i + _GP_MAX_TAGS]
                      for i in range(0, len(itens), _GP_MAX_TAGS)]
            for gi, g_itens in enumerate(grupos):
                cor, est = _gp_cor_do_grupo(g_itens)
                resultado.append({
                    "label":  " + ".join(_gp_tag_curta(it["nome"]) for it in g_itens),
                    "strike": strike + cfd_off + gi * _CFG["offset_split"],
                    "cor": cor, "estilo": est,
                })
    return sorted(resultado, key=lambda x: x["strike"], reverse=True)


def _gp_build_niveis_block(df_pine: pd.DataFrame, spot: float,
                            cfd_off: float) -> str:
    niveis_raw = _gp_calcular_niveis(df_pine, spot)
    if not niveis_raw:
        return "        // (nenhum nível calculado — verifique os dados)"
    niveis_agrup = _gp_agrupar_niveis(niveis_raw, cfd_off)

    linhas = [
        f"        // {len(niveis_raw)} níveis → {len(niveis_agrup)} linhas após agrupamento",
        f"        // Gerado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    for n in niveis_agrup:
        # Format strike: inteiro se for inteiro, senão 2 casas decimais
        sk_v = n["strike"]
        sk_str = (f"{sk_v:.0f}" if abs(sk_v - round(sk_v)) < 1e-6
                  else f"{sk_v:.2f}")
        linhas.append(
            f"        create_indicator('{n['label']}', "
            f"{sk_str}, {n['cor']}, '{n['estilo']}')"
        )
    return "\n".join(linhas)


# ─────────────────────────────────────────────────────────────────
# 17.6 · ORQUESTRADOR
# ─────────────────────────────────────────────────────────────────

def _gp_gerar_pine_completo(df_raw_local: pd.DataFrame, spot_local: float,
                              cfd_off: float, mult: float, snapshot: str) -> str:
    # Janela ±X% do spot (real, antes do offset)
    s_lo = spot_local * (1 - _CFG["win_focus_pct"])
    s_hi = spot_local * (1 + _CFG["win_focus_pct"])

    # df_pine fresh: focada na janela, sem filtro de min_fin
    df_pine = calcular_v9(
        df_raw_local, spot_local, s_lo, s_hi,
        min_fin=0.0, mult=mult,
    )
    if df_pine is None or df_pine.empty:
        raise RuntimeError(
            f"Sem dados na janela ±{_CFG['win_focus_pct']*100:.0f}% "
            f"[{s_lo:.2f}, {s_hi:.2f}] do spot {spot_local:.2f}"
        )

    arrays_block, _ = _gp_build_arrays_block(
        df_pine, spot_local, s_lo, s_hi, cfd_off, snapshot,
    )
    niveis_block = _gp_build_niveis_block(df_pine, spot_local, cfd_off)

    # Constrói a expressão "ativo == 'X' or ativo == 'Y' or ..."
    is_active_expr = " or ".join(
        f"ativo == '{tk}'" for tk in _CFG["tickers"]
    )

    pine = _PINE_TEMPLATE
    pine = pine.replace("__ATIVO_NOME__",         _CFG["nome"])
    pine = pine.replace("__IS_ACTIVE_EXPR__",     is_active_expr)
    pine = pine.replace("__MEIA_ALTURA__",        f"{_CFG['meia_altura']}")
    pine = pine.replace("__ARRAYS_PLACEHOLDER__", arrays_block)
    pine = pine.replace("__NIVEIS_PLACEHOLDER__", niveis_block)
    return pine


# ─────────────────────────────────────────────────────────────────
# 17.7 · UI — BOTÃO + DOWNLOAD
# ─────────────────────────────────────────────────────────────────

st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
section(f"INDICADOR TRADINGVIEW — PINE SCRIPT ({_CFG['nome']})")

_s_lo_disp = spot * (1 - _CFG["win_focus_pct"])
_s_hi_disp = spot * (1 + _CFG["win_focus_pct"])
_cfd_msg = (f" · CFD offset <b style='color:#fa0;'>{cfd_offset:+.2f}</b>"
            if cfd_offset != 0.0 else "")

st.markdown(
    f"<div style='font-family:JetBrains Mono,monospace;font-size:13px;"
    f"color:#8a9bb5;margin-bottom:8px;'>"
    f"Gera o Pine personalizado para <b style='color:#0ff;'>{_CFG['nome']}</b> "
    f"com os dados atuais "
    f"(spot <b style='color:#fa0;'>{_fmt_strike_cfd(spot)}</b>, "
    f"janela <b style='color:#0ff;'>±{_CFG['win_focus_pct']*100:.0f}%</b> = "
    f"[{_fmt_strike_cfd(_s_lo_disp)}, {_fmt_strike_cfd(_s_hi_disp)}], "
    f"snapshot <b style='color:#0ff;'>{momento}</b>{_cfd_msg})."
    f"</div>",
    unsafe_allow_html=True,
)

_btn_key = f"gerar_pine_{_PINE_ATIVO}"
if st.button(f"🌲 Gerar Indicador TradingView ({_CFG['nome']})",
             use_container_width=True, type="primary", key=_btn_key):
    try:
        with st.spinner("⚙️ Gerando Pine Script..."):
            pine_final = _gp_gerar_pine_completo(
                df_raw, spot, cfd_offset,
                float(MULTIPLICADOR_FIXO), momento,
            )
        st.session_state[f"pine_final_{_PINE_ATIVO}"] = pine_final
        st.markdown(
            alert_box(
                f"✅ Pine gerado com sucesso "
                f"({len(pine_final):,} caracteres). "
                f"Clique no botão abaixo para baixar.",
                "success"
            ),
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.markdown(
            alert_box(f"❌ Erro ao gerar Pine: {e}", "danger"),
            unsafe_allow_html=True,
        )

_pine_key = f"pine_final_{_PINE_ATIVO}"
if _pine_key in st.session_state and st.session_state[_pine_key]:
    st.download_button(
        label=f"⬇️ Download — {_CFG['filename']}",
        data=st.session_state[_pine_key],
        file_name=_CFG["filename"],
        mime="text/plain",
        use_container_width=True,
        key=f"dl_pine_{_PINE_ATIVO}",
    )
    with st.expander("👀 Pré-visualizar Pine Script", expanded=False):
        st.code(st.session_state[_pine_key], language="pine")

# ══════════════════════════════════════════════════════════════════
# 19 · RODAPÉ
# ══════════════════════════════════════════════════════════════════
st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
st.markdown(f"<div style='text-align:center;font-size:13px;color:rgba(0,255,255,0.25);letter-spacing:2px;padding:8px 0;font-family:JetBrains Mono,monospace;'>◈  DASHBOARD INSTITUCIONAL MARKET MAKER  |  V9  |  {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}  ◈</div>", unsafe_allow_html=True)
