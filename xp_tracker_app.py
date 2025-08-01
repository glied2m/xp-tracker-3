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

# --- Daten initialisieren ---
tasks_data = load_json(TASKS_FILE, {})
daily_log = load_json(DAILY_LOG_FILE, {})
# Sicherstellen, dass daily_log.json existiert und initial ein leeres Dict enthält
if not os.path.exists(DAILY_LOG_FILE):
    save_json(DAILY_LOG_FILE, {})
    daily_log = {}

# --- Streamlit Setup ---
st.set_page_config(page_title="Task List", layout="wide")

# --- Datum auswählen ---
today = datetime.date.today()
selected_date = st.sidebar.date_input("Datum auswählen", value=today)
selected_str = selected_date.isoformat()

# --- Session State für Häkchen ---
state_key = f"completed_{selected_str}"
if state_key not in st.session_state:
    st.session_state[state_key] = set(daily_log.get(selected_str, []))

# --- Speichern Button im Header ---
col1, col2 = st.columns([3,1])
with col1:
    st.title("📋 Aufgaben")
with col2:
    if st.button("💾 Speichern"):
        daily_log[selected_str] = list(st.session_state[state_key])
        save_json(DAILY_LOG_FILE, daily_log)
        st.success(f"Status für {selected_date:%d.%m.%Y} gespeichert!")

# --- Aufgaben anzeigen ---
st.subheader(f"Aufgaben für {selected_date:%d.%m.%Y}")
for category, tasks in tasks_data.items():
    # Wenn Wochenplan als Unterkategorien
    if isinstance(tasks, dict):
        with st.expander(category):
            for day, day_tasks in tasks.items():
                with st.expander(f"{day} ({len(day_tasks)} Tasks)", expanded=False):
                    for idx, task in enumerate(day_tasks):
                        key = f"{category}_{day}_{idx}_{selected_str}"
                        checked = key in st.session_state[state_key]
                        new = st.checkbox(f"{task['task']} (+{task['xp']} XP)", value=checked, key=key)
                        if new and not checked:
                            st.session_state[state_key].add(key)
                        if not new and checked:
                            st.session_state[state_key].remove(key)
    # Reguläre Listen-Kategorie
    elif isinstance(tasks, list):
        with st.expander(f"{category} ({len(tasks)} Tasks)", expanded=False):
            for idx, task in enumerate(tasks):
                key = f"{category}_{idx}_{selected_str}"
                checked = key in st.session_state[state_key]
                new = st.checkbox(f"{task['task']} (+{task['xp']} XP)", value=checked, key=key)
                if new and not checked:
                    st.session_state[state_key].add(key)
                if not new and checked:
                    st.session_state[state_key].remove(key)

# --- Historie als Tabelle ---
st.markdown("---")
st.subheader("Historie (letzte 30 Tage)")
hist = []
for i in range(29, -1, -1):
    d = today - datetime.timedelta(days=i)
    date_str = d.isoformat()
    # Anzahl erledigter Aufgaben
    keys = daily_log.get(date_str, [])
    count = len(keys)
    # Summe der XP für diesen Tag
    xp_sum = 0
    for key in keys:
        parts = key.split("_")
        # Identify if weekly subcategory includes day
        if parts[0] == "Wochenplan":
            # Wochenplan_{Tag}_{idx}_{date}
            _, day, idx, _ = parts
            task = tasks_data.get("Wochenplan", {}).get(day, [])[int(idx)]
        else:
            cat = parts[0]
            idx = parts[1]
            task = tasks_data.get(cat, [])[int(idx)]
        xp_sum += task.get("xp", 0)
    hist.append({"Datum": d.strftime("%d.%m.%Y"), "Erledigte Aufgaben": count, "XP gesamt": xp_sum})
df_hist = pd.DataFrame(hist).set_index("Datum")
st.dataframe(df_hist, use_container_width=True)

# --- JSON Editor für tasks.json ---
st.markdown("---")
st.subheader("🛠️ Bearbeite tasks.json")
raw = json.dumps(tasks_data, ensure_ascii=False, indent=2)
edited = st.text_area("JSON:", raw, height=200)
if st.button("📂 tasks.json speichern (neu laden)"):
    try:
        parsed = json.loads(edited)
        save_json(TASKS_FILE, parsed)
        st.success("tasks.json gespeichert! Bitte Seite neu laden.")
    except Exception as e:
        st.error(f"Fehler: {e}")
