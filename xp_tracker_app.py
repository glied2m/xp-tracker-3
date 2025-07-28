import streamlit as st
import json
import os
import pandas as pd
import datetime

# --- Datei-Pfade ---
TASKS_FILE = "tasks.json"           # Kategorien & Tasks
DAILY_LOG_FILE = "daily_log.json"  # Persistente Häkchen pro Datum

# --- Hilfsfunktionen ---
def load_json(path, default):
    """
    Lädt JSON aus Datei oder gibt default zurück, falls Fehler/Datei nicht existiert.
    """
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default
    return default


def save_json(path, data):
    """
    Speichert Daten als prettified JSON.
    """
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

# Session-State: bereits abgehakte Tasks
if "completed" not in st.session_state:
    # Set aus daily_log für ausgewähltes Datum
    st.session_state["completed"] = set(daily_log.get(selected_str, []))

# Speichern-Button
if st.sidebar.button("💾 Alles speichern"):
    # Schreibe aktuelle Häkchen in daily_log und speichere
    daily_log[selected_str] = sorted(st.session_state["completed"])
    save_json(DAILY_LOG_FILE, daily_log)
    st.sidebar.success(f"Status für {selected_date:%d.%m.%Y} gespeichert!")

# --- Hauptbereich ---
st.title("📋 Task XP Tracker")
st.subheader(f"Aufgaben für {selected_date:%d.%m.%Y}")

# --- Kategorien als Expander mit 2-Spalten-Layout ---
for cat, items in tasks_data.items():
    with st.expander(f"{cat} ({len(items)} Tasks)", expanded=False):
        cols = st.columns(2)
        for idx, task in enumerate(items):
            key = f"{cat}_{idx}_{selected_str}"
            checked = key in st.session_state["completed"]
            col = cols[idx % 2]
            new = col.checkbox(f"{task['task']} (+{task['xp']} XP)", value=checked, key=key)
            # Update state
            if new and not checked:
                st.session_state["completed"].add(key)
            if not new and checked:
                st.session_state["completed"].remove(key)

# --- XP-Berechnung für ein Datum ---
def calc_xp_for_date(date_str):
    """Berechnet XP-Summe für gegebenes Datum"""
    total = 0
    for key in daily_log.get(date_str, []):
        # key form: Kategorie_Idx_Datum
        cat, idx, _ = key.rsplit("_", 2)
        try:
            xp = tasks_data.get(cat, [])[int(idx)]["xp"]
            total += xp
        except Exception:
            continue
    return total

# Statistische Ansicht: letzte 30 Tage
st.header("📊 XP-Historie (letzte 30 Tage)")
# Erzeuge Liste von Daten (älteste → neueste)
dates = [today - datetime.timedelta(days=i) for i in range(29, -1, -1)]
hist = [{"Datum": d.strftime("%Y-%m-%d"), "XP": calc_xp_for_date(d.isoformat())} for d in dates]
# DataFrame
df_hist = pd.DataFrame(hist).set_index("Datum")
st.dataframe(df_hist, use_container_width=True)

# --- JSON-Editor für tasks.json ---
st.markdown("---")
st.header("🛠️ Kategorien & Tasks bearbeiten (tasks.json)")
current = json.dumps(tasks_data, ensure_ascii=False, indent=2)
edited = st.text_area("Bearbeite JSON:", current, height=300)
if st.button("📂 tasks.json speichern"):
    try:
        parsed = json.loads(edited)
        # Update tasks_data und speichere
        tasks_data.clear()
        tasks_data.update(parsed)
        save_json(TASKS_FILE, tasks_data)
        st.success("tasks.json gespeichert! Bitte Seite neu laden.")
    except Exception as e:
        st.error(f"Ungültiges JSON: {e}")
