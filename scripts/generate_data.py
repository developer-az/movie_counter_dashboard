"""
Build the analysis catalog from published movie financials.

Source figures come from The Numbers (via TidyTuesday movie_profit) joined to
IMDb scores from a public IMDb 5000 extract. Daily ticket rows are a modeled
8-week theatrical run scaled so each film's ticket revenue equals its reported
domestic gross — not random adjective/noun titles.
"""

from __future__ import annotations

import math
import os
import random
import re
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

np.random.seed(42)
random.seed(42)

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROFIT_PATH = RAW_DIR / "movie_profit.csv"
IMDB_PATH = RAW_DIR / "imdb_movie_metadata.csv"

# Household-name films missing from the TidyTuesday extract, with widely
# published budget / box-office / IMDb figures (USD, rounded).
SUPPLEMENTAL_MOVIES = [
    # title, date, genre, mpaa, studio, runtime, budget, domestic, worldwide, imdb
    ("Avatar", "2009-12-18", "Action", "PG-13", "20th Century Fox", 162, 237_000_000, 785_221_649, 2_923_706_026, 7.9),
    ("Titanic", "1997-12-19", "Drama", "PG-13", "Paramount", 194, 200_000_000, 659_363_944, 2_264_743_305, 7.9),
    ("Star Wars: The Force Awakens", "2015-12-18", "Adventure", "PG-13", "Walt Disney", 138, 245_000_000, 936_662_225, 2_071_310_218, 7.8),
    ("Avengers: Endgame", "2019-04-26", "Action", "PG-13", "Walt Disney", 181, 356_000_000, 858_373_000, 2_799_439_100, 8.4),
    ("Avengers: Infinity War", "2018-04-27", "Action", "PG-13", "Walt Disney", 149, 325_000_000, 678_815_482, 2_048_359_754, 8.4),
    ("Spider-Man: No Way Home", "2021-12-17", "Action", "PG-13", "Sony Pictures", 148, 200_000_000, 814_115_070, 1_921_847_111, 8.2),
    ("Avatar: The Way of Water", "2022-12-16", "Action", "PG-13", "Walt Disney", 192, 350_000_000, 684_075_767, 2_320_251_420, 7.6),
    ("Jurassic World", "2015-06-12", "Action", "PG-13", "Universal Pictures", 124, 150_000_000, 652_270_625, 1_671_713_208, 6.9),
    ("The Lion King (2019)", "2019-07-19", "Adventure", "PG", "Walt Disney", 118, 260_000_000, 543_638_043, 1_662_899_438, 6.8),
    ("The Avengers", "2012-05-04", "Action", "PG-13", "Walt Disney", 143, 220_000_000, 623_357_910, 1_518_812_988, 8.0),
    ("Furious 7", "2015-04-03", "Action", "PG-13", "Universal Pictures", 137, 190_000_000, 353_007_020, 1_515_047_671, 7.1),
    ("Top Gun: Maverick", "2022-05-27", "Action", "PG-13", "Paramount", 130, 170_000_000, 718_732_821, 1_495_696_292, 8.2),
    ("Frozen II", "2019-11-22", "Adventure", "PG", "Walt Disney", 103, 150_000_000, 477_373_578, 1_450_026_933, 6.8),
    ("Barbie", "2023-07-21", "Comedy", "PG-13", "Warner Bros", 114, 145_000_000, 636_238_421, 1_447_038_421, 6.8),
    ("Avengers: Age of Ultron", "2015-05-01", "Action", "PG-13", "Walt Disney", 141, 250_000_000, 459_005_868, 1_405_403_694, 7.3),
    ("Black Panther", "2018-02-16", "Action", "PG-13", "Walt Disney", 134, 200_000_000, 700_426_566, 1_347_293_205, 7.3),
    ("Harry Potter and the Deathly Hallows – Part 2", "2011-07-15", "Adventure", "PG-13", "Warner Bros", 130, 125_000_000, 381_193_157, 1_342_359_942, 8.1),
    ("Star Wars: The Last Jedi", "2017-12-15", "Adventure", "PG-13", "Walt Disney", 152, 262_000_000, 620_181_382, 1_333_258_636, 6.9),
    ("Frozen", "2013-11-27", "Adventure", "PG", "Walt Disney", 102, 150_000_000, 400_953_009, 1_281_504_918, 7.4),
    ("Beauty and the Beast (2017)", "2017-03-17", "Adventure", "PG", "Walt Disney", 129, 160_000_000, 504_014_165, 1_266_115_964, 7.1),
    ("Incredibles 2", "2018-06-15", "Adventure", "PG", "Walt Disney", 118, 200_000_000, 608_581_744, 1_243_225_667, 7.6),
    ("The Fate of the Furious", "2017-04-14", "Action", "PG-13", "Universal Pictures", 136, 250_000_000, 226_008_385, 1_236_005_118, 6.6),
    ("Iron Man 3", "2013-05-03", "Action", "PG-13", "Walt Disney", 130, 200_000_000, 409_013_994, 1_214_811_252, 7.1),
    ("Captain America: Civil War", "2016-05-06", "Action", "PG-13", "Walt Disney", 147, 250_000_000, 408_084_349, 1_153_338_049, 7.8),
    ("The Dark Knight", "2008-07-18", "Action", "PG-13", "Warner Bros", 152, 185_000_000, 534_987_076, 1_006_234_241, 9.0),
    ("The Dark Knight Rises", "2012-07-20", "Action", "PG-13", "Warner Bros", 165, 250_000_000, 448_139_099, 1_081_142_612, 8.4),
    ("The Lord of the Rings: The Return of the King", "2003-12-17", "Adventure", "PG-13", "New Line", 201, 94_000_000, 377_845_905, 1_147_633_833, 9.0),
    ("The Lord of the Rings: The Two Towers", "2002-12-18", "Adventure", "PG-13", "New Line", 179, 94_000_000, 342_551_365, 938_399_699, 8.8),
    ("The Lord of the Rings: The Fellowship of the Ring", "2001-12-19", "Adventure", "PG-13", "New Line", 178, 93_000_000, 315_544_750, 898_204_420, 8.8),
    ("Skyfall", "2012-11-09", "Action", "PG-13", "Sony Pictures", 143, 200_000_000, 304_360_277, 1_142_471_295, 7.8),
    ("Toy Story 3", "2010-06-18", "Adventure", "G", "Walt Disney", 103, 200_000_000, 415_004_880, 1_066_969_703, 8.3),
    ("Toy Story 4", "2019-06-21", "Adventure", "G", "Walt Disney", 100, 200_000_000, 434_038_008, 1_073_394_593, 7.7),
    ("Rogue One: A Star Wars Story", "2016-12-16", "Adventure", "PG-13", "Walt Disney", 133, 200_000_000, 532_177_324, 1_058_687_902, 7.8),
    ("Aladdin (2019)", "2019-05-24", "Adventure", "PG", "Walt Disney", 128, 183_000_000, 355_559_216, 1_054_305_395, 6.9),
    ("Joker", "2019-10-04", "Drama", "R", "Warner Bros", 122, 55_000_000, 335_451_311, 1_078_958_629, 8.4),
    ("Finding Dory", "2016-06-17", "Adventure", "PG", "Walt Disney", 97, 200_000_000, 486_295_561, 1_028_570_889, 7.3),
    ("Harry Potter and the Philosopher's Stone", "2001-11-16", "Adventure", "PG", "Warner Bros", 152, 125_000_000, 317_575_550, 1_022_297_282, 7.6),
    ("Harry Potter and the Chamber of Secrets", "2002-11-15", "Adventure", "PG", "Warner Bros", 161, 100_000_000, 262_233_381, 879_043_351, 7.4),
    ("Harry Potter and the Prisoner of Azkaban", "2004-06-04", "Adventure", "PG", "Warner Bros", 142, 130_000_000, 249_541_069, 796_907_323, 7.9),
    ("Harry Potter and the Order of the Phoenix", "2007-07-11", "Adventure", "PG-13", "Warner Bros", 138, 150_000_000, 292_137_260, 942_172_396, 7.5),
    ("Harry Potter and the Half-Blood Prince", "2009-07-15", "Adventure", "PG", "Warner Bros", 153, 250_000_000, 302_089_278, 934_454_252, 7.6),
    ("Harry Potter and the Deathly Hallows – Part 1", "2010-11-19", "Adventure", "PG-13", "Warner Bros", 146, 250_000_000, 296_131_568, 977_043_483, 7.7),
    ("Inception", "2010-07-16", "Action", "PG-13", "Warner Bros", 148, 160_000_000, 292_576_195, 839_030_630, 8.8),
    ("Inside Out", "2015-06-19", "Adventure", "PG", "Walt Disney", 95, 175_000_000, 356_461_711, 858_848_019, 8.1),
    ("Inside Out 2", "2024-06-14", "Adventure", "PG", "Walt Disney", 96, 200_000_000, 652_980_194, 1_698_863_816, 7.6),
    ("The Matrix", "1999-03-31", "Action", "R", "Warner Bros", 136, 63_000_000, 171_479_930, 467_222_728, 8.7),
    ("Forrest Gump", "1994-07-06", "Drama", "PG-13", "Paramount", 142, 55_000_000, 330_252_182, 678_226_133, 8.8),
    ("The Godfather", "1972-03-24", "Drama", "R", "Paramount", 175, 6_000_000, 134_966_411, 250_341_816, 9.2),
    ("Jaws", "1975-06-20", "Horror", "PG", "Universal Pictures", 124, 7_000_000, 260_000_000, 470_653_000, 8.1),
    ("Jurassic Park", "1993-06-11", "Action", "PG-13", "Universal Pictures", 127, 63_000_000, 402_453_882, 1_104_046_930, 8.2),
    ("E.T. the Extra-Terrestrial", "1982-06-11", "Adventure", "PG", "Universal Pictures", 115, 10_500_000, 439_251_124, 797_307_407, 7.9),
    ("Bohemian Rhapsody", "2018-11-02", "Drama", "PG-13", "20th Century Fox", 134, 52_000_000, 216_668_970, 910_809_311, 7.9),
    ("La La Land", "2016-12-09", "Drama", "PG-13", "Lionsgate", 128, 30_000_000, 151_101_803, 447_284_649, 8.0),
    ("Parasite", "2019-10-11", "Drama", "R", "Neon", 132, 11_400_000, 53_369_745, 258_773_645, 8.5),
    ("Mad Max: Fury Road", "2015-05-15", "Action", "R", "Warner Bros", 120, 150_000_000, 154_058_340, 380_209_762, 8.1),
    ("Spider-Man: Into the Spider-Verse", "2018-12-14", "Adventure", "PG", "Sony Pictures", 117, 90_000_000, 190_241_310, 384_298_736, 8.4),
    ("Oppenheimer", "2023-07-21", "Drama", "R", "Universal Pictures", 180, 100_000_000, 329_862_540, 975_811_333, 8.3),
    ("Dune: Part Two", "2024-03-01", "Adventure", "PG-13", "Warner Bros", 166, 190_000_000, 282_709_823, 714_844_358, 8.5),
    ("Guardians of the Galaxy Vol. 3", "2023-05-05", "Action", "PG-13", "Walt Disney", 150, 250_000_000, 358_995_815, 845_555_777, 7.9),
    ("Super Mario Bros. Movie", "2023-04-05", "Adventure", "PG", "Universal Pictures", 92, 100_000_000, 574_934_330, 1_361_922_621, 7.0),
]
IMDB_OVERRIDES = {
    "jurassic world fallen kingdom": 6.2,
    "despicable me 3": 6.3,
    "star wars episode 1 the phantom menace": 6.5,
    "zootopia": 8.0,
    "jumanji welcome to the jungle": 6.9,
    "wonder woman": 7.4,
    "e t the extra terrestrial": 7.9,
    "et the extra terrestrial": 7.9,
    "fast and furious 6": 7.1,
    "star wars episode 4 a new hope": 8.6,
    "deadpool 2": 7.6,
    "it": 7.3,
    "doctor strange": 7.5,
    "sing": 7.1,
    "ant man and the wasp": 7.0,
    "logan": 8.1,
    "ready player one": 7.4,
    "mission impossible 2": 6.1,
    "the meg": 5.6,
    "the boss baby": 6.3,
    "dunkirk": 7.8,
    "war for the planet of the apes": 7.4,
    "mr and mrs smith": 6.5,
    "les intouchables": 8.5,
    "venom": 6.6,
    "tarzan": 7.3,
    "men in black 2": 6.2,
    "the mummy": 7.0,
    "kingsman the golden circle": 6.7,
    "kingsman the secret service": 7.7,
    "ice age collision course": 5.6,
    "fifty shades darker": 4.6,
    "godzilla": 5.4,
    "fifty shades freed": 4.5,
    "fast furious": 6.5,
    "the hangover 3": 5.8,
    "who framed roger rabbit": 7.7,
    "doctor seuss the lorax": 6.4,
    "peter rabbit": 6.6,
    "murder on the orient express": 6.5,
    "xxx return of xander cage": 5.2,
    "aquaman": 6.9,
    "black panther": 7.3,
    "incredibles 2": 7.6,
    "avengers infinity war": 8.4,
    "beauty and the beast": 7.1,
    "rogue one a star wars story": 7.8,
    "star wars the last jedi": 6.9,
    "guardians of the galaxy vol 2": 7.6,
    "spider man homecoming": 7.4,
    "thor ragnarok": 7.9,
    "coco": 8.4,
    "get out": 7.8,
    "a star is born": 7.6,
    "bohemian rhapsody": 7.9,
    "a quiet place": 7.5,
}

STUDIO_ALIASES = {
    "warner bros.": "Warner Bros",
    "warner bros": "Warner Bros",
    "walt disney": "Walt Disney",
    "sony pictures": "Sony Pictures",
    "sony pictures classics": "Sony Pictures Classics",
    "20th century fox": "20th Century Fox",
    "paramount pictures": "Paramount",
    "paramount": "Paramount",
    "universal": "Universal Pictures",
    "lionsgate": "Lionsgate",
    "mgm": "MGM",
    "new line": "New Line",
    "miramax": "Miramax",
    "fox searchlight": "Fox Searchlight",
    "weinstein co.": "Weinstein Co.",
    "focus features": "Focus Features",
    "dreamworks skg": "DreamWorks",
    "dreamworks": "DreamWorks",
    "columbia": "Columbia",
    "tristar": "TriStar",
    "metro goldwyn mayer": "MGM",
}

ROMAN = {
    r"\bi\b": "1",
    r"\bii\b": "2",
    r"\biii\b": "3",
    r"\biv\b": "4",
    r"\bv\b": "5",
    r"\bvi\b": "6",
    r"\bvii\b": "7",
    r"\bviii\b": "8",
}


def normalize_title(value: str) -> str:
    text = str(value).replace("\xa0", " ").replace("&", " and ").lower()
    text = re.sub(r"\bep\.?\s*", "episode ", text)
    text = re.sub(r"[:'\-]+", " ", text)
    for pattern, repl in ROMAN.items():
        text = re.sub(pattern, repl, text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\be t\b", "et", text)
    text = re.sub(r"\s+", " ", text).strip()
    if text.startswith("the "):
        text = text[4:]
    return text


def clean_studio(value) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "Independent"
    text = str(value).replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "Independent"
    return STUDIO_ALIASES.get(text.lower(), text)


def _load_imdb() -> pd.DataFrame:
    if not IMDB_PATH.exists():
        return pd.DataFrame(columns=["title_key", "imdb_rating", "runtime_minutes"])
    meta = pd.read_csv(IMDB_PATH)
    meta["title_key"] = meta["movie_title"].map(normalize_title)
    meta = meta.sort_values("num_voted_users", ascending=False).drop_duplicates("title_key")
    return meta.rename(columns={"imdb_score": "imdb_rating", "duration": "runtime_minutes"})[
        ["title_key", "imdb_rating", "runtime_minutes"]
    ]


def build_movie_catalog() -> pd.DataFrame:
    if not PROFIT_PATH.exists():
        raise FileNotFoundError(
            f"Missing {PROFIT_PATH}. Restore data/raw/movie_profit.csv (The Numbers / TidyTuesday)."
        )

    profit = pd.read_csv(PROFIT_PATH)
    profit["movie"] = profit["movie"].astype(str).str.replace("\xa0", " ", regex=False).str.strip()
    profit["release_date"] = pd.to_datetime(profit["release_date"], errors="coerce")
    profit = profit.dropna(subset=["movie", "release_date", "production_budget"])
    profit = profit[profit["production_budget"] > 0]
    profit = profit.drop_duplicates(subset=["movie", "release_date"], keep="first")

    profit["title_key"] = profit["movie"].map(normalize_title)
    imdb = _load_imdb()
    catalog = profit.merge(imdb, on="title_key", how="left")

    override_rating = catalog["title_key"].map(IMDB_OVERRIDES)
    catalog["imdb_rating"] = catalog["imdb_rating"].fillna(override_rating)

    genre_runtime = catalog.groupby("genre")["runtime_minutes"].transform("median")
    catalog["runtime_minutes"] = (
        catalog["runtime_minutes"].fillna(genre_runtime).fillna(110).round().astype(int)
    )
    catalog["runtime_minutes"] = catalog["runtime_minutes"].clip(70, 240)

    domestic = catalog["domestic_gross"].fillna(0).clip(lower=0)
    worldwide = catalog["worldwide_gross"].fillna(0).clip(lower=0)
    worldwide = np.maximum(worldwide, domestic)

    catalog = catalog.reset_index(drop=True)
    ticket_price = 9.5
    movies = pd.DataFrame(
        {
            "movie_id": np.arange(1, len(catalog) + 1),
            "title": catalog["movie"],
            "genre": catalog["genre"],
            "release_date": catalog["release_date"].dt.strftime("%Y-%m-%d"),
            "rating": catalog["mpaa_rating"].fillna("NR"),
            "studio": catalog["distributor"].map(clean_studio),
            "runtime_minutes": catalog["runtime_minutes"],
            "budget": catalog["production_budget"].astype(int),
            "domestic_gross": domestic.astype(int),
            "international_gross": (worldwide - domestic).astype(int),
            "total_gross": worldwide.astype(int),
            "imdb_rating": catalog["imdb_rating"].round(1),
            "tickets_sold": (domestic / ticket_price).round().astype(int),
            "tickets_available": 0,
        }
    )
    movies["title_key"] = movies["title"].map(normalize_title)

    extra_rows = []
    existing = set(movies["title_key"])
    for title, date, genre, mpaa, studio, runtime, budget, domestic_g, worldwide_g, imdb in SUPPLEMENTAL_MOVIES:
        key = normalize_title(title)
        if key in existing:
            continue
        existing.add(key)
        extra_rows.append(
            {
                "movie_id": 0,
                "title": title,
                "genre": genre,
                "release_date": date,
                "rating": mpaa,
                "studio": studio,
                "runtime_minutes": runtime,
                "budget": int(budget),
                "domestic_gross": int(domestic_g),
                "international_gross": int(max(worldwide_g - domestic_g, 0)),
                "total_gross": int(worldwide_g),
                "imdb_rating": imdb,
                "tickets_sold": int(round(domestic_g / ticket_price)),
                "tickets_available": 0,
                "title_key": key,
            }
        )
    if extra_rows:
        movies = pd.concat([movies, pd.DataFrame(extra_rows)], ignore_index=True)
    movies = movies.drop(columns=["title_key"])
    movies["movie_id"] = np.arange(1, len(movies) + 1)
    return movies


def generate_movie_data(n_movies: int | None = None) -> pd.DataFrame:
    """Return the published catalog, optionally truncated (used by tests)."""
    movies = build_movie_catalog()
    if n_movies is not None:
        return movies.head(int(n_movies)).copy()
    return movies


def generate_daily_sales_data(movies_df: pd.DataFrame, days_back: int = 56) -> pd.DataFrame:
    """
    Model an opening-to-week-8 theatrical curve for each title.

    Daily revenue is scaled so the run sums to reported domestic gross.
    Weekend/Friday weights stay in the shape, so weekday comparisons stay valid.
    """
    run_days = max(int(days_back), 7)
    rows = []
    for _, movie in movies_df.iterrows():
        domestic = float(movie.get("domestic_gross") or 0)
        if domestic <= 0:
            continue
        release = pd.to_datetime(movie["release_date"])
        if pd.isna(release):
            continue
        ticket_price = 8.5 + (int(movie["movie_id"]) % 8) * 0.4
        weights = []
        dates = []
        for offset in range(run_days):
            day = release + timedelta(days=offset)
            week = offset / 7.0
            weight = math.exp(-0.42 * week)
            weekday = day.weekday()
            if weekday >= 5:
                weight *= 1.55
            elif weekday == 4:
                weight *= 1.25
            weights.append(weight)
            dates.append(day)
        total_w = sum(weights)
        for day, weight in zip(dates, weights):
            revenue = domestic * (weight / total_w)
            tickets = max(0, int(round(revenue / ticket_price)))
            rows.append(
                {
                    "movie_id": int(movie["movie_id"]),
                    "movie_title": movie["title"],
                    "date": day.strftime("%Y-%m-%d"),
                    "tickets_sold": tickets,
                    "revenue": round(revenue, 2),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    print("Building catalog from The Numbers / IMDb extracts...")
    movies_df = generate_movie_data()

    top_for_sales = movies_df.nlargest(100, "domestic_gross")
    print(f"Modeling 8-week ticket runs for {len(top_for_sales)} highest domestic-gross titles...")
    sales_df = generate_daily_sales_data(top_for_sales, days_back=56)

    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(ROOT / "data" / "processed", exist_ok=True)

    movies_df.to_csv(RAW_DIR / "movies_raw.csv", index=False)
    sales_df.to_csv(RAW_DIR / "daily_sales_raw.csv", index=False)

    rated = movies_df["imdb_rating"].notna().mean() * 100
    print(f"Wrote {len(movies_df):,} movies and {len(sales_df):,} daily sales rows")
    print(f"IMDb coverage: {rated:.0f}% of titles")
    print(f"Date range: {movies_df['release_date'].min()} → {movies_df['release_date'].max()}")
    print(f"Genres: {', '.join(sorted(movies_df['genre'].unique()))}")
    print(f"Sample titles: {', '.join(movies_df.nlargest(5, 'total_gross')['title'].tolist())}")
    print("Raw files:")
    print(f"  {RAW_DIR / 'movies_raw.csv'}")
    print(f"  {RAW_DIR / 'daily_sales_raw.csv'}")


if __name__ == "__main__":
    main()
