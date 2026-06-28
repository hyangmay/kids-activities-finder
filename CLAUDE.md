# PDX Kids Activities

A small web app for finding toddler-friendly activities near a home area over the
next few days (today / tomorrow / day-after). Built for a parent of a 2-year-old in the
Portland, OR metro area.

## Vision

Enter an approximate location → get a list of nearby activities happening today, tomorrow,
and the day after: library story times, park & rec programs, museum/zoo events, festivals,
and community happenings. Designed to be checked quickly (e.g. on a phone in the morning).

Started as a personal project but should be usable by **non-technical people** via a simple
shared link.

## Owner / context

- Owner is a **data scientist**; primary language is **Python**.
- Dependency management & packaging via **Poetry**.
- Prefer Python-first tools; keep the stack simple.

## Decisions made so far

| Area | Decision |
|---|---|
| **Interface** | **Streamlit** web app (deployable to a free shareable URL). FastAPI is a known future upgrade. |
| **Location input** | **Coarse only** — ZIP / neighborhood / street name. **Never** an exact address or house number. (Privacy; exact location adds no value at a 10-mile radius.) |
| **Data sources (v1)** | Official local sources (Multnomah County Library, Portland Parks & Rec, OMSI, Oregon Zoo) + parent/community calendars (e.g. PDX Parent). |
| **Freshness / storage** | **Live fetch on demand** + short-lived **in-memory** cache. No database, near-zero disk usage, nothing persisted. |
| **Geocoding** | OpenStreetMap **Nominatim** (free, no API key). |
| **Search radius** | Default **10 miles**, adjustable. |
| **Time window** | Today / tomorrow / day-after. |
| **Geography** | Portland, OR metro to start. |

## Architecture principles

- **Keep the data/logic layer separate from the UI** so the frontend can be swapped later.
- **Pluggable data sources** behind a common interface — adding or fixing a source is an
  isolated change. Sources are the most fragile part (HTML/APIs change).
- **Normalized activity model** that every source maps into.
- **Graceful degradation:** one broken source must not break the whole search.
- Be a polite scraper: descriptive User-Agent, respect rate limits, cache results.

## Still open (decide later, no rush)

- Results display / output format (list, cards, map, sort order, what each item shows).
- Exact set of fields shown per activity.
- Filters (free vs paid, indoor/outdoor, time of day, age range).
- Project file/module layout (will firm up when we scaffold).

## Future ideas (not v1)

- Event-platform APIs (Eventbrite, Meetup); map view; saved favorites; configurable
  location & preferences; possible migration to FastAPI + frontend if usage grows.

## Status

Requirements being gathered. Not yet scaffolded.
