"""Streamlit entry point — a thin UI over the kids_activities_finder package.

All real logic (geocoding, sources, distance, search) lives in the package so the UI can
be swapped later (e.g. FastAPI). This file only collects input, calls ``search``, and
renders the result.

Run with:  poetry run streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from kids_activities_finder.geocoding import GeocodingError
from kids_activities_finder.models import Activity
from kids_activities_finder.search import DEFAULT_RADIUS_MILES, SearchResult, search
from kids_activities_finder.timewindow import ALL_DAYS, label_to_day

st.set_page_config(page_title="Kids Activities Finder", page_icon="🧸")

st.title("🧸 Kids Activities Finder")
st.caption("Find kid-friendly activities near you over the next few days.")


def _format_time_range(activity: Activity) -> str:
    """A compact 'Mon · 10:30 AM – 11:00 AM' style label."""
    if activity.start is None:
        return "Time TBD"
    start = activity.start.strftime("%a · %-I:%M %p")
    if activity.end is not None and activity.end.date() == activity.start.date():
        return f"{start} – {activity.end.strftime('%-I:%M %p')}"
    return start


def _badges(activity: Activity) -> str:
    """Small inline metadata line (cost, age, distance)."""
    parts: list[str] = []
    if activity.is_free is True:
        parts.append("🆓 Free")
    elif activity.is_free is False:
        parts.append("🎟️ Paid")
    if activity.age_suitability:
        parts.append(f"👶 {activity.age_suitability}")
    if activity.distance_miles is not None:
        parts.append(f"📍 {activity.distance_miles:.1f} mi")
    return "  ·  ".join(parts)


def _render_activity(activity: Activity) -> None:
    with st.container(border=True):
        if activity.url:
            st.markdown(f"#### [{activity.title}]({activity.url})")
        else:
            st.markdown(f"#### {activity.title}")
        st.caption(_format_time_range(activity))
        where = activity.location_name or activity.address
        if where:
            st.write(f"**Where:** {where}")
        if activity.description:
            st.write(activity.description)
        badges = _badges(activity)
        if badges:
            st.caption(badges)
        st.caption(f"Source: {activity.source}")


def _render_result(result: SearchResult) -> None:
    st.success(f"Searching near **{result.center.display_name}**")

    for err in result.errors:
        st.warning(f"⚠️ Couldn't load **{err.source}** ({err.message}). Showing the rest.")

    if not result.activities:
        st.info(
            "No activities found in this area and time window. Try a larger radius or "
            "different days."
        )
        return

    st.write(f"Found **{len(result.activities)}** activities:")
    for activity in result.activities:
        _render_activity(activity)


# --- Input controls ---
with st.form("search"):
    location = st.text_input(
        "Your area",
        placeholder="ZIP code, neighborhood, or street (no house number needed)",
        help="We only use an approximate location, and nothing is stored.",
    )
    radius = st.slider(
        "Search radius (miles)",
        min_value=1,
        max_value=25,
        value=int(DEFAULT_RADIUS_MILES),
    )
    day_labels = st.multiselect(
        "Which days?",
        options=[d.label for d in ALL_DAYS],
        default=[d.label for d in ALL_DAYS],
    )
    submitted = st.form_submit_button("Find activities", type="primary")

if submitted:
    if not location.strip():
        st.error("Please enter a ZIP code, neighborhood, or street.")
    elif not day_labels:
        st.error("Please pick at least one day.")
    else:
        days = [label_to_day(label) for label in day_labels]
        with st.spinner("Looking for activities…"):
            try:
                result = search(location, days, radius_miles=float(radius))
            except GeocodingError as exc:
                st.error(str(exc))
            else:
                _render_result(result)
else:
    st.info("Enter your area above and pick which days to see what's happening.")
