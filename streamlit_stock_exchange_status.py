import subprocess, sys, os
import streamlit as st

# Check packages in the ACTUAL Python environment running this script
installed = subprocess.check_output([sys.executable, "-m", "pip", "list"]).decode()
st.text(f"Python executable: {sys.executable}")
st.text("Installed packages:")
st.code(installed)

# Also check if requirements.txt is even visible to the app
req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
st.text(f"requirements.txt path: {req_path}")
st.text(f"requirements.txt exists: {os.path.exists(req_path)}")
if os.path.exists(req_path):
    with open(req_path) as f:
        st.code(f.read())

st.stop()

import json
from datetime import datetime, time
from pathlib import Path
import pytz

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="World Stock Exchange Status",
    page_icon="📈",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
        background-color: #0d0d0d;
        color: #e8e8e8;
    }
    .main { background-color: #0d0d0d; }

    /* ── Header block ── */
    .header-box {
        background-color: #141414;
        border: 1px solid #2a2a2a;
        border-radius: 6px;
        padding: 18px 28px;
        margin-bottom: 22px;
        text-align: center;
    }
    .header-box h2 {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.45rem;
        font-weight: 600;
        color: #f0f0f0;
        margin: 0;
        letter-spacing: 0.03em;
    }
    .header-box .ist-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        color: #888;
        margin-top: 4px;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    /* ── Exchange table: use CSS table layout so columns size to content ── */
    .exchange-list {
        background-color: #141414;
        border: 1px solid #2a2a2a;
        border-radius: 6px;
        margin: 0 auto 22px auto;
        display: table;
        width: auto;
        border-collapse: collapse;
    }

    /* Header row */
    .ex-header {
        display: table-row;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        color: #555;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        background: #111;
        border-radius: 6px 6px 0 0;
    }
    .ex-header > span {
        display: table-cell;
        padding: 8px 14px 8px 0;
        border-bottom: 1px solid #333;
        white-space: nowrap;
    }
    .ex-header > span:first-child { padding-left: 22px; }
    .ex-header > span:last-child  { padding-right: 22px; }

    /* Data rows */
    .ex-row {
        display: table-row;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.82rem;
        transition: background 0.12s;
    }
    .ex-row:last-child > span { border-bottom: none; }
    .ex-row:hover > span { background: #1a1a1a; }
    .ex-row > span {
        display: table-cell;
        padding: 9px 14px 9px 0;
        border-bottom: 1px solid #1f1f1f;
        vertical-align: middle;
        white-space: nowrap;
    }
    .ex-row > span:first-child { padding-left: 22px; }
    .ex-row > span:last-child  { padding-right: 22px; }

    /* rank — shrink to content */
    .rank-badge {
        color: #555;
        font-size: 0.68rem;
        text-align: right;
    }

    /* status pill column — cell shrinks, inner span carries the visual pill */
    .pill-cell {
        white-space: nowrap;
        text-align: center;
    }
    .pill-open {
        display: inline-block;
        background-color: #0d2b0d;
        color: #4cff6e;
        border: 1px solid #1a5e1a;
        border-radius: 4px;
        padding: 2px 9px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        min-width: 58px;
        text-align: center;
    }
    .pill-closed {
        display: inline-block;
        background-color: #2b0d0d;
        color: #ff5555;
        border: 1px solid #5e1a1a;
        border-radius: 4px;
        padding: 2px 9px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        min-width: 58px;
        text-align: center;
    }

    /* exchange name — shrink to content */
    .ex-name {
        color: #d8d8d8;
        font-weight: 600;
        white-space: nowrap;
    }

    /* country/city — shrink to content */
    .ex-meta {
        color: #777;
        white-space: nowrap;
    }

    /* time column — shrink to content, NO stretching */
    .ex-time {
        color: #aaa;
        font-size: 0.78rem;
        white-space: nowrap;
    }

    /* ── Summary bar ── */
    .summary-bar {
        display: flex;
        gap: 18px;
        margin-bottom: 0;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.8rem;
    }
    .summary-open {
        background: #0d2b0d; border: 1px solid #1a5e1a;
        border-radius: 5px; padding: 8px 18px; color: #4cff6e;
    }
    .summary-closed {
        background: #2b0d0d; border: 1px solid #5e1a1a;
        border-radius: 5px; padding: 8px 18px; color: #ff5555;
    }
    .summary-total {
        background: #1a1a1a; border: 1px solid #2a2a2a;
        border-radius: 5px; padding: 8px 18px; color: #aaa;
    }
    .refresh-status {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        color: #555;
        margin-left: auto;
        align-self: center;
    }
    .refresh-on  { color: #4cff6e; }
    .refresh-off { color: #ff5555; }

    /* ── Footer ── */
    .footer-note {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.65rem;
        color: #444;
        text-align: center;
        margin-top: 10px;
        letter-spacing: 0.05em;
    }

    /* ── Streamlit widget overrides ── */
    div[data-testid="stSelectbox"] label { color: #888 !important; font-size: 0.78rem; }
    .stCheckbox > label > div { color: #999 !important; font-size: 0.78rem !important;
        font-family: 'IBM Plex Mono', monospace !important; }
    div.stButton > button {
        background-color: #1a1a1a; border: 1px solid #333;
        color: #ccc; font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem; border-radius: 4px; padding: 5px 14px;
    }
    div.stButton > button:hover {
        background-color: #252525; border-color: #555; color: #fff;
    }
</style>
""", unsafe_allow_html=True)


# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=0)
def load_exchanges(json_path: str) -> dict:
    with open(json_path, "r") as f:
        return json.load(f)


_script_dir = Path(__file__).parent
_candidates = [
    _script_dir / "top_20_exchanges_utc_city.json",
    Path("top_20_exchanges_utc_city.json"),
]
_json_path = next((str(p) for p in _candidates if p.exists()), None)

if _json_path is None:
    st.error(
        "⚠️  **Data file not found.**\n\n"
        "Place `top_20_exchanges_utc_city.json` in the same folder as this script and restart."
    )
    st.stop()

data      = load_exchanges(_json_path)
exchanges = data["exchanges"]


# ── Time helpers ──────────────────────────────────────────────────────────────
IST      = pytz.timezone("Asia/Kolkata")
DAY_ABBR = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}


def get_ist_now() -> datetime:
    return datetime.now(IST)


def is_open(exchange: dict, ist_now: datetime):
    local_dt  = ist_now.astimezone(pytz.timezone(exchange["local_timezone"]))
    local_day = DAY_ABBR[local_dt.weekday()]
    cur_time  = local_dt.time()
    if local_day not in exchange["trading_days"]:
        return False, local_dt, exchange["sessions"]
    for s in exchange["sessions"]:
        if time(*map(int, s["local_open"].split(":"))) <= cur_time \
                <= time(*map(int, s["local_close"].split(":"))):
            return True, local_dt, exchange["sessions"]
    return False, local_dt, exchange["sessions"]


def fmt_sessions(sessions: list) -> str:
    return " / ".join(f"{s['local_open']}-{s['local_close']}" for s in sessions)


# ── Session-state defaults ────────────────────────────────────────────────────
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True


# ── Auto-refresh ──────────────────────────────────────────────────────────────
if st.session_state.auto_refresh:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=60_000, key="autorefresh_ticker")
    except ImportError:
        # Fallback if streamlit-autorefresh not installed
        st.markdown('<meta http-equiv="refresh" content="60">', unsafe_allow_html=True)


# ── Current IST time ──────────────────────────────────────────────────────────
now_ist     = get_ist_now()
ist_display = now_ist.strftime("%A, %d %B %Y, %H:%M").replace(" 0", " ")


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="header-box">
  <h2>My Current Date &amp; Time &nbsp;:&nbsp; {ist_display}</h2>
  <div class="ist-label">Indian Standard Time (IST / UTC+5:30)</div>
</div>
""", unsafe_allow_html=True)


# ── Controls row (centered) ───────────────────────────────────────────────────
# Use equal side spacers so the 4 active controls sit in the middle
_, col_f1, col_f2, col_toggle, col_btn, _ = st.columns([2, 1.2, 1.2, 1.3, 0.8, 2])

with col_f1:
    filter_status = st.selectbox("Filter by status", ["All", "Open", "Closed"])

with col_f2:
    sort_by = st.selectbox("Sort by", ["Rank", "Name", "Status", "Local Time"])

with col_toggle:
    new_val = st.toggle(
        "Auto-refresh every 60s",
        value=st.session_state.auto_refresh,
        key="toggle_ar",
    )
    if new_val != st.session_state.auto_refresh:
        st.session_state.auto_refresh = new_val
        st.rerun()

with col_btn:
    st.markdown("<div style='margin-top:26px'>", unsafe_allow_html=True)
    if st.button("⟳  Refresh"):
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ── Build row data ────────────────────────────────────────────────────────────
rows = []
for ex in exchanges:
    status, local_dt, sessions = is_open(ex, now_ist)
    rows.append({
        "rank":         ex["rank"],
        "name":         ex["name"],
        "country_city": f"{ex['country']} / {ex['city']}",
        "status":       status,
        "local_day":    DAY_ABBR[local_dt.weekday()],
        "local_time":   local_dt.strftime("%H:%M"),
        "sessions":     fmt_sessions(sessions),
    })

# Filter
if filter_status == "Open":
    rows = [r for r in rows if r["status"]]
elif filter_status == "Closed":
    rows = [r for r in rows if not r["status"]]

# Sort
if sort_by == "Name":
    rows.sort(key=lambda r: r["name"])
elif sort_by == "Status":
    rows.sort(key=lambda r: (not r["status"], r["rank"]))
elif sort_by == "Local Time":
    rows.sort(key=lambda r: r["local_time"])


# ── Summary + refresh status bar ─────────────────────────────────────────────
all_statuses = [is_open(ex, now_ist)[0] for ex in exchanges]
n_open   = sum(all_statuses)
n_closed = len(all_statuses) - n_open
n_total  = len(all_statuses)

ar_badge = (
    '<span class="refresh-on">● AUTO-REFRESH ON</span>'
    if st.session_state.auto_refresh
    else '<span class="refresh-off">● AUTO-REFRESH OFF</span>'
)

st.markdown(f"""
<div style="display:flex; flex-direction:column; align-items:center; margin-bottom:14px; gap:8px;">
  <div class="summary-bar" style="justify-content:center;">
    <div class="summary-open">● &nbsp;OPEN &nbsp; {n_open}</div>
    <div class="summary-closed">● &nbsp;CLOSED &nbsp; {n_closed}</div>
    <div class="summary-total">TOTAL &nbsp; {n_total}</div>
  </div>
  <div class="refresh-status" style="text-align:center;">
    {ar_badge} &nbsp;&nbsp; Last updated: {now_ist.strftime("%H:%M:%S")} IST
  </div>
</div>
""", unsafe_allow_html=True)


# ── Exchange list ─────────────────────────────────────────────────────────────
if not rows:
    st.info("No exchanges match the selected filter.")
else:
    header_html = (
        '<div class="ex-header">'
        '<span class="rank-badge">#</span>'
        '<span class="pill-cell">Status</span>'
        '<span>Exchange</span>'
        '<span>Country / City</span>'
        '<span>Local Day &amp; Time &nbsp; [Session Hours]</span>'
        '</div>'
    )

    rows_html = ""
    for r in rows:
        pill_cls  = "pill-open"  if r["status"] else "pill-closed"
        pill_text = "OPEN"       if r["status"] else "CLOSED"
        rows_html += (
            f'<div class="ex-row">'
            f'<span class="rank-badge">#{r["rank"]}</span>'
            f'<span class="pill-cell"><span class="{pill_cls}">{pill_text}</span></span>'
            f'<span class="ex-name">{r["name"]}</span>'
            f'<span class="ex-meta">{r["country_city"]}</span>'
            f'<span class="ex-time">{r["local_day"]} {r["local_time"]} &nbsp; [{r["sessions"]}]</span>'
            f'</div>'
        )

    st.markdown(
        f'<div class="exchange-list">{header_html}{rows_html}</div>',
        unsafe_allow_html=True,
    )


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer-note">'
    'Data source: top_20_exchanges_utc_city.json &nbsp;·&nbsp; '
    'Standard UTC times — no DST adjustments &nbsp;·&nbsp; '
    'For reliable auto-refresh: <code>pip install streamlit-autorefresh</code>'
    '</div>',
    unsafe_allow_html=True,
)