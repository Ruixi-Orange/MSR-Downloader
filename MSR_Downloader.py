import requests
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from rich import print
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://monster-siren.hypergryph.com/",
    "Connection": "keep-alive",
}


def sanitize(path: str):
    illegal_chars = r'[\\/:*?"<>|]'
    return re.sub(illegal_chars, " ", path).strip(" .")


def download(url: str, save_path: Path, file_name: str):
    with requests.get(url, stream=True) as r:
        with open(save_path / file_name, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def get_album_list():
    response = requests.get(
        "https://monster-siren.hypergryph.com/api/albums",
        headers=HEADERS,
    )
    album_list = response.json()["data"]
    for album in album_list:
        yield album


def get_album_detail(cid: str):
    response = requests.get(
        f"https://monster-siren.hypergryph.com/api/album/{cid}/detail",
        headers=HEADERS,
    )
    return response.json()["data"]


def save_album_info(path: Path, album_detail: dict) -> None:
    with open(path / "album_info.txt", "w", encoding="utf-8") as file:
        file.write(f"name: {album_detail['name']}\n")
        file.write(f"intro: \n{album_detail['intro']}\n")
        file.write(f"belong: {album_detail['belong']}\n")
        file.write("songs: \n")
        for song in album_detail["songs"]:
            file.write(f"{song['name']}\n")
            if song["artistes"]:
                file.write(f"   artistes: {'、'.join(song['artistes'])}\n")


def get_song_list(album_detail: dict):
    for song in album_detail["songs"]:
        response = requests.get(
            f"https://monster-siren.hypergryph.com/api/song/{song['cid']}",
            headers=HEADERS,
        )
        yield response.json()["data"]


def download_cover(path: Path, album_detail: dict) -> None:
    album_name = sanitize(album_detail["name"])
    download(
        album_detail["coverUrl"],
        path,
        f"{album_name}_Cover.{album_detail['coverUrl'].split('.')[-1]}",
    )
    download(
        album_detail["coverDeUrl"],
        path,
        f"{album_name}_CoverDe.{album_detail['coverDeUrl'].split('.')[-1]}",
    )


def download_song(path: Path, album_detail: dict):
    for song in get_song_list(album_detail):
        print(f"[bold yellow]Downloading {song['name']}[/bold yellow]", end="\r")
        download(
            song["sourceUrl"],
            path,
            f"{sanitize(song['name'])}.{song['sourceUrl'].split('.')[-1]}",
        )
        if song["lyricUrl"] is not None:
            download(
                song["lyricUrl"],
                path,
                f"{sanitize(song['name'])}.{song['lyricUrl'].split('.')[-1]}",
            )

        print(f"[bold green]{song['name']} Downloaded     [/bold green]")


if __name__ == "__main__":
    print("[bold blue]MSR_Downloader[/bold blue]")
    for album in get_album_list():
        album_path = Path("MSR_Albums") / sanitize(album["name"])
        album_path.mkdir(parents=True, exist_ok=True)
        album_detail = get_album_detail(album["cid"])
        save_album_info(album_path, album_detail)
        download_cover(album_path, album_detail)
        download_song(album_path, album_detail)
