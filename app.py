from pathlib import Path
from elfannan.config import ROOT, load_artist

artist_file = ROOT / "artists" / "_template" / "artist.json"
artist = load_artist(artist_file)

print("ElFannan / الفنان")
print(f"Root: {ROOT}")
print(f"Artist template: {artist_file}")
print(f"Stage name: {artist.get('stage_name') or '[not set yet]'}")
