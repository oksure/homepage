from pathlib import Path
import csv
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / ".." / "melon_top100.csv"
CSV_PATH = CSV_PATH.resolve()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


@app.get("/")
@app.get("/api")
def health_check() -> dict:
  return {"ok": True}


def load_songs() -> list[dict]:
  if not CSV_PATH.exists():
    raise HTTPException(status_code=404, detail="melon_top100.csv not found")

  songs: list[dict] = []
  try:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as csvfile:
      reader = csv.DictReader(csvfile)
      for row in reader:
        rank_text = (row.get("순위") or "").strip()
        title = (row.get("곡명") or "").strip()
        artist = (row.get("가수") or "").strip()

        songs.append(
          {
            "rank": int(rank_text) if rank_text.isdigit() else rank_text,
            "title": title,
            "artist": artist,
          }
        )
  except UnicodeDecodeError:
    raise HTTPException(status_code=500, detail="Failed to decode CSV file")
  except csv.Error:
    raise HTTPException(status_code=500, detail="Invalid CSV format")

  return songs


@app.get("/songs")
@app.get("/api/songs")
def get_songs(
  search: str | None = Query(default=None, description="Search by title or artist"),
  sort_by: Literal["rank", "title", "artist"] = Query(default="rank"),
  order: Literal["asc", "desc"] = Query(default="asc"),
) -> list[dict]:
  songs = load_songs()

  if search:
    keyword = search.strip().lower()
    songs = [
      song
      for song in songs
      if keyword in str(song["title"]).lower() or keyword in str(song["artist"]).lower()
    ]

  reverse = order == "desc"
  if sort_by == "rank":
    songs.sort(
      key=lambda song: (
        song["rank"] if isinstance(song["rank"], int) else float("inf"),
        str(song["rank"]),
      ),
      reverse=reverse,
    )
  else:
    songs.sort(key=lambda song: str(song[sort_by]).lower(), reverse=reverse)

  return songs


@app.get("/artists")
@app.get("/api/artists")
def get_artists(
  search: str | None = Query(default=None, description="Search by artist name"),
  order: Literal["asc", "desc"] = Query(default="asc"),
) -> list[dict]:
  songs = load_songs()
  artist_counts: dict[str, int] = {}
  for song in songs:
    artist = str(song["artist"]).strip()
    if artist:
      artist_counts[artist] = artist_counts.get(artist, 0) + 1

  artists = [
    {"artist": artist, "song_count": count}
    for artist, count in artist_counts.items()
  ]

  if search:
    keyword = search.strip().lower()
    artists = [artist for artist in artists if keyword in artist["artist"].lower()]

  reverse = order == "desc"
  artists.sort(key=lambda item: item["artist"].lower(), reverse=reverse)
  return artists