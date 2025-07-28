import streamlit as st
import json
import os
import pandas as pd
import datetime

# --- Datei-Pfade ---
TASKS_FILE = "tasks.json"
DAILY_LOG_FILE = "daily_log.json"

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

# --- Dateninitialisierung ---
tasks_data = load_json(TASKS_FILE, {})
daily_log = load_json(DAILY_LOG_FILE, {})  # Format: {"YYYY-MM-DD": ["Kategorie_Idx_Datum", ...]}

# --- Streamlit Setup ---
st.set_page_config(page_title="Task XP Tracker", layout="wide")

# --- Sidebar: Datumsauswahl & Speichern ---
st.sidebar.title("Einstellungen")
today = datetime.date.today()
selected_date = st.sidebar.date_input("Datum auswählen", value=today)
selected_str = selected_date.isoformat()

# Session-State: bereits abgehakte Tasks für ausgewähltes Datum
state_key = f"completed_{selected_str}"
if state_key not in st.session_state:
    st.session_state[state_key] = set(daily_log.get(selected_str, []))

# Speichern-Button
if st.sidebar.button("💾 Alles speichern"):
    daily_log[selected_str] = sorted(st.session_state[state_key])
    save_json(DAILY_LOG_FILE, daily_log)
    st.sidebar.success(f"Status für {selected_date:%d.%m.%Y} gespeichert!")

# --- Hauptbereich ---
st.title("📋 Task XP Tracker")

# --- XP-Berechnung für heute ohne String-Splitting ---
# Erzeuge map von key zu xp für aktuelle Auswahl
xp_map = {}
for cat, items in tasks_data.items():
    for idx, task in enumerate(items):
        key = f"{cat}_{idx}_{selected_str}"
        xp_map[key] = task.get("xp", 0)

def calc_xp_current():
    # Summiere alle abgehakten XP aus session_state
    return sum(xp_map.get(k, 0) for k in st.session_state[state_key])

xp_today = calc_xp_current()
st.markdown(
    f"<h1 style='text-align:center; font-size:3rem; color:#4CAF50;'>Heutige XP: {xp_today}</h1>",
    unsafe_allow_html=True
)
st.subheader(f"Aufgaben für {selected_date:%d.%m.%Y}")

# --- Kategorien als Expander ---
for cat, items in tasks_data.items():
    with st.expander(f"{cat} ({len(items)} Tasks)", expanded=False):
        for idx, task in enumerate(items):
            key = f"{cat}_{idx}_{selected_str}"
            checked = key in st.session_state[state_key]
            new = st.checkbox(f"{task['task']} (+{task['xp']} XP)", value=checked, key=key)
            if new and not checked:
                st.session_state[state_key].add(key)
            if not new and checked:
                st.session_state[state_key].remove(key)

# --- Statistik: letzte 30 Tage ---
def calc_xp_for_date(date_str):
    # Baue xp_map für dieses Datum
    tmp_map = {}
    for cat, items in tasks_data.items():
        for idx, task in enumerate(items):
            tmp_key = f"{cat}_{idx}_{date_str}"
            tmp_map[tmp_key] = task.get("xp", 0)
    return sum(tmp_map.get(k, 0) for k in daily_log.get(date_str, []))

st.header("📊 XP-Historie (letzte 30 Tage)")
dates = [today - datetime.timedelta(days=i) for i in range(29, -1, -1)]
history = [{"Datum": d.strftime("%Y-%m-%d"), "XP": calc_xp_for_date(d.isoformat())} for d in dates]
df_history = pd.DataFrame(history).set_index("Datum")
st.dataframe(df_history, use_container_width=True)

# --- JSON-Editor für tasks.json ---
st.markdown("---")
st.header("🛠️ Kategorien & Tasks bearbeiten (tasks.json)")
tasks_json = json.dumps(tasks_data, ensure_ascii=False, indent=2)
edited = st.text_area("Bearbeite JSON:", tasks_json, height=300)
if st.button("📂 tasks.json speichern"):
    try:
        parsed = json.loads(edited)
        tasks_data.clear()
        tasks_data.update(parsed)
        save_json(TASKS_FILE, tasks_data)
        st.success("tasks.json gespeichert! Bitte Seite neu laden.")
    except Exception as e:
        st.error(f"Ungültiges JSON: {e}")
