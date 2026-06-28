# 🧸 Kids Activities Finder

Find kid-friendly activities happening **near you** over the next few days
(today / tomorrow / day-after) — library story times, park & rec programs, museum/zoo
events, festivals, and community happenings.

The app is **location-agnostic** by design. The first supported region is the
**Portland, OR metro area**; more regions/sources can be added over time.

> You enter only an **approximate** location (ZIP, neighborhood, or street — never a full
> address). Nothing is stored.

See [CLAUDE.md](CLAUDE.md) for the full design decisions and architecture.

## Tech stack

- **Python 3.12** managed with **Poetry**
- **Streamlit** web UI
- Live data fetching with in-memory caching (no database)
- Geocoding via OpenStreetMap Nominatim

## Setup

Requires [Homebrew](https://brew.sh), Python 3.12, and Poetry:

```bash
brew install python@3.12 poetry
```

Then, from the project root:

```bash
poetry env use python3.12   # create the virtual environment on Python 3.12
poetry install              # install dependencies
```

## Run

```bash
poetry run streamlit run app.py
```

This opens the app in your browser.

## Develop

```bash
poetry run pytest           # run tests
```

## Project layout

```
app.py                    # Streamlit entry point (thin UI)
kids_activities_finder/   # reusable logic package (no UI)
  models.py               # Activity data model
  ...                     # geocoding, distance, sources, search (added incrementally)
tests/
```
