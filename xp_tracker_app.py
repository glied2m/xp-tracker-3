import streamlit as st
import json
import os
import pandas as pd
import datetime

# --- Datei-Pfade ---
TASKS_FILE = "tasks.json"           # Enthält Kategorien und Tasks
DAILY_LOG_FILE = "daily_log.json"  # Speichert abgehakte Tasks pro Tag

# --- Hilfsfunktionen ---
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Daten laden ---
tasks_data = load_json(TASKS_FILE, {})
daily_log = load_json(DAILY_LOG_FILE, {})  # Format: {"YYYY-MM-DD": ["Kategorie_i_j", ...]}

# --- Streamlit Setup ---
st.set_page_config(page_title="TOO DOOO Felix", layout="wide")

# --- Sidebar: Datum & Save ---
st.sidebar.title("Einstellungen")
today = datetime.date.today()
selected_date = st.sidebar.date_input("Datum auswählen", value=today)
selected_str = selected_date.isoformat()

if "completed" not in st.session_state:
    st.session_state["completed"] = set(daily_log.get(selected_str, []))

if st.sidebar.button("💾 Alles speichern"):
    daily_log[selected_str] = sorted(st.session_state["completed"])
    save_json(DAILY_LOG_FILE, daily_log)
    st.sidebar.success(f"Status für {selected_date:%d.%m.%Y} gespeichert!")

# --- Hauptbereich ---
st.title("📋 Task XP Tracker")
st.caption(f"Aufgaben für {selected_date:%d.%m.%Y}")

# --- Tasks mit Expandern ---
for cat, items in tasks_data.items():
    with st.expander(f"{cat} ({len(items)})", expanded=False):
        cols = st.columns(2)
        for idx, task in enumerate(items):
            key = f"{cat}_{idx}"
            checked = key in st.session_state["completed"]
            col = cols[idx % 2]
            new = col.checkbox(f"{task['task']} (+{task['xp']} XP)", value=checked, key=key)
            if new and not checked:
                st.session_state["completed"].add(key)
            if not new and checked:
                st.session_state["completed"].remove(key)

# --- XP-Berechnung & Statistik ---
def calc_xp(date_str):
    xp = 0
    for key in daily_log.get(date_str, []):
        cat, idx = key.rsplit("_", 1)
        xp += tasks_data.get(cat, [])[int(idx)]["xp"]
    return xp

st.header("📊 XP Historie (letzte 30 Tage)")
dates = [today - datetime.timedelta(days=i) for i in range(30)]
hist = [{"Datum": d, "XP": calc_xp(d.isoformat())} for d in sorted(dates)]
# Korrigierte Zuweisung ohne führendes '='
df_hist = pd.DataFrame(hist).set_index("Datum")
st.dataframe(df_hist, use_container_width=True)

# --- JSON-Editor unten ---
st.markdown("---")
st.header("🛠️ Aufgaben-Datei (tasks.json)")
tasks_json = json.dumps(tasks_data, ensure_ascii=False, indent=2)
new_tasks_json = st.text_area("Bearbeite Kategorien & Tasks (JSON):", tasks_json, height=300)
if st.button("📂 tasks.json speichern"):
    try:
        parsed = json.loads(new_tasks_json)
        save_json(TASKS_FILE, parsed)
        st.success("tasks.json gespeichert! Bitte Seite neu laden.")
    except Exception as e:
        st.error(f"JSON Fehler: {e}")
