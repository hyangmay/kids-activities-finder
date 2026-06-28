"""Streamlit entry point — a thin UI over the kids_activities_finder package.

Run with:  poetry run streamlit run app.py
"""

import streamlit as st

st.set_page_config(page_title="Kids Activities Finder", page_icon="🧸")

st.title("🧸 Kids Activities Finder")
st.caption("Find kid-friendly activities near you over the next few days.")

st.info(
    "🚧 Just getting started. Next up: location input, the search engine, "
    "and live data sources."
)

# --- Placeholder controls (not wired up yet) ---
st.text_input(
    "Your area",
    placeholder="ZIP code, neighborhood, or street (no house number needed)",
    help="We only use an approximate location, and nothing is stored.",
)
st.slider("Search radius (miles)", min_value=1, max_value=25, value=10)
st.multiselect(
    "Which days?",
    options=["Today", "Tomorrow", "Day after"],
    default=["Today", "Tomorrow", "Day after"],
)
st.button("Find activities", type="primary", disabled=True)
