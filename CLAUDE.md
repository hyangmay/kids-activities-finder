# Kids Activities Finder

A small web app for finding kid-friendly activities near a home area over the next few days
(today / tomorrow / day-after). Built for parents of young children (initially a parent of a
2-year-old).

## Vision

Enter an approximate location → get a list of nearby activities happening today, tomorrow,
and the day after: library story times, park & rec programs, museum/zoo events, festivals,
and community happenings. Designed to be checked quickly (e.g. on a phone in the morning).

Started as a personal project but should be usable by **non-technical people** via a simple
shared link.

## Geographic scope

- The app is **location-agnostic by design** — the name and architecture are not tied to any
  one city.
- **Real data starts with the Portland, OR metro area** (the owner's location), because
  good toddler activity data comes from *city-specific* sources (local libraries, parks,
  museums) that don't generalize automatically.
- **Sources are region-scoped and pluggable.** Adding a new city = adding new source
  adapters for that city, without changing the core. Generic aggregator APIs
  (Eventbrite/Meetup) are a future way to get broader coverage anywhere.

## Owner / context

- Owner is a **data scientist**; primary language is **Python**.
- Dependency management & packaging via **Poetry**.
- Prefer Python-first tools; keep the stack simple.

## Privacy (important)

- **Never ask for an exact street address / house number.** Users have told us this feels
  insecure, especially on a publicly shared app.
- Location input is **coarse by design** — any of:
  - **ZIP code** (e.g. `97214`) — default, simplest, private.
  - **Neighborhood** (e.g. "Sellwood, Portland").
  - **Street name / cross-streets** (e.g. "SE Hawthorne & 39th") — no house number.
- A 10-mile search radius makes exact coordinates unnecessary; an approximate center point
  is plenty.
- **No location data is persisted.** The app keeps nothing on disk; in-memory data is
  discarded between sessions.

## Decisions made so far

| Area | Decision |
|---|---|
| **Interface** | **Streamlit** web app (deployable to a free shareable URL). FastAPI is a known future upgrade. |
| **Location input** | **Coarse only** — ZIP / neighborhood / street name. **Never** an exact address or house number. |
| **Geographic scope** | Location-agnostic architecture; **Portland, OR metro is the first region** with real data. |
| **Data sources (v1)** | Portland official sources (Multnomah County Library, Portland Parks & Rec, OMSI, Oregon Zoo) + parent/community calendars (e.g. PDX Parent). |
| **Freshness / storage** | **Live fetch on demand** + short-lived **in-memory** cache. No database, near-zero disk usage, nothing persisted. |
| **Geocoding** | OpenStreetMap **Nominatim** (free, no API key). |
| **Search radius** | Default **10 miles**, adjustable. |
| **Time window** | Today / tomorrow / day-after. |

## Architecture principles

- **Keep the data/logic layer separate from the UI** so the frontend can be swapped later.
- **Pluggable, region-scoped data sources** behind a common interface — adding or fixing a
  source (or adding a new city) is an isolated change. Sources are the most fragile part
  (HTML/APIs change).
- **Normalized activity model** that every source maps into.
- **Graceful degradation:** one broken source must not break the whole search.
- Be a polite scraper: descriptive User-Agent, respect rate limits, cache results.

## Still open (decide later, no rush)

- Results display / output format (list, cards, map, sort order, what each item shows).
- Exact set of fields shown per activity.
- Filters (free vs paid, indoor/outdoor, time of day, age range).
- How users pick/declare their region as more cities are added.
- Project file/module layout (will firm up as we build).

## Future ideas (not v1)

- More cities/regions; event-platform APIs (Eventbrite, Meetup); map view; saved favorites;
  configurable location & preferences; possible migration to FastAPI + frontend if usage grows.

## Status

Requirements being gathered. Project scaffolded (Poetry + Streamlit + Activity model);
no data sources wired yet.
