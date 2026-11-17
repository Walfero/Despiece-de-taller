"""Comprueba los precios de prices.json en las webs de las tiendas.

- Lee la ficha de cada producto y saca el precio (datos estructurados de la página).
- Actualiza prices.json y añade una línea por producto a history.csv.
- Si algún precio cambia, o alguna ficha deja de leerse, avisa por Telegram
  (variables de entorno TELEGRAM_TOKEN y TELEGRAM_CHAT_ID; si faltan, solo lo imprime).

Uso: python scripts/update_prices.py [--dry-run]
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import re
import sys
import time
from html import unescape
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
PRICES = ROOT / "prices.json"
HISTORY = ROOT / "history.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
}
# Un cambio menor que esto se guarda pero no se avisa (céntimos de redondeo).
UMBRAL_AVISO_EUR = 0.10


def to_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace("\xa0", "").replace("€", "").replace(" ", "")
    if not s:
        return None
    # "1.234,56" -> 1234.56 ; "12,60" -> 12.60 ; "12.60" -> 12.60
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _walk_jsonld(node, found: list[float]):
    if isinstance(node, list):
        for n in node:
            _walk_jsonld(n, found)
        return
    if not isinstance(node, dict):
        return
    types = node.get("@type")
    types = types if isinstance(types, list) else [types]
    if "Offer" in types or "AggregateOffer" in types:
        for key in ("price", "lowPrice"):
            p = to_float(node.get(key))
            if p:
                found.append(p)
                break
        ps = node.get("priceSpecification")
        if isinstance(ps, dict):
            p = to_float(ps.get("price"))
            if p:
                found.append(p)
    for key in ("offers", "@graph", "mainEntity", "itemOffered"):
        if key in node:
            _walk_jsonld(node[key], found)


def extract_price(html: str) -> tuple[float | None, str]:
    """Devuelve (precio, método). Prueba primero los datos estructurados."""
    # 1) JSON-LD de producto (lo usan Leroy Merlin, Obramat y Brico Depôt)
    for block in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S | re.I
    ):
        try:
            data = json.loads(unescape(block.strip()))
        except json.JSONDecodeError:
            continue
        found: list[float] = []
        _walk_jsonld(data, found)
        if found:
            return found[0], "json-ld"
    # 2) Metadatos
    for pattern in (
        r'<meta[^>]+(?:property|name)=["\'](?:product:price:amount|og:price:amount)["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+itemprop=["\']price["\'][^>]+content=["\']([^"\']+)',
        r'itemprop=["\']price["\'][^>]*content=["\']([^"\']+)',
        r'data-price=["\']([\d.,]+)',
    ):
        m = re.search(pattern, html, re.I)
        if m and (p := to_float(m.group(1))):
            return p, "meta"
    return None, "sin precio"


def fetch(url: str) -> tuple[str | None, str]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
    except requests.RequestException as e:
        return None, f"error de red ({e.__class__.__name__})"
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    return r.text, "ok"


def eur(x: float) -> str:
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def telegram(text: str):
    token, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    print("---- aviso ----\n" + text)
    if not token or not chat:
        print("(Sin TELEGRAM_TOKEN/TELEGRAM_CHAT_ID: no se envía)")
        return
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
        timeout=30,
    )
    if r.status_code != 200:
        print(f"Telegram respondió {r.status_code}: {r.text[:200]}")


def main(dry_run: bool = False):
    data = json.loads(PRICES.read_text(encoding="utf-8"))
    today = dt.date.today().isoformat()
    cambios, fallos, filas = [], [], []

    for rol, ofertas in data["productos"].items():
        for o in ofertas:
            html, status = fetch(o["url"])
            precio, metodo = (extract_price(html) if html else (None, status))
            if precio is None:
                o["estado"] = f"fallo: {metodo}"
                fallos.append(f"• {o['tienda']} · {o['producto']}: {metodo}")
                print(f"[FALLO] {o['id']}: {metodo}")
            else:
                anterior = o.get("precio")
                if anterior is not None and abs(precio - anterior) >= UMBRAL_AVISO_EUR:
                    o["precio_anterior"] = anterior
                    flecha = "🔻" if precio < anterior else "🔺"
                    cambios.append(
                        f"{flecha} {o['tienda']} · {o['producto']}: {eur(anterior)} → <b>{eur(precio)}</b>"
                    )
                o["precio"] = round(precio, 2)
                o["comprobado"] = today
                o["estado"] = "ok"
                print(f"[OK] {o['id']}: {eur(precio)} ({metodo})")
            filas.append([today, o["id"], o["tienda"], o["producto"], o.get("precio") if precio else "", o["estado"]])
            time.sleep(2)  # sin prisas con las webs de las tiendas

    data["actualizado"] = today
    if dry_run:
        print("Dry run: no se guarda nada.")
    else:
        PRICES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        nuevo = not HISTORY.exists()
        with HISTORY.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if nuevo:
                w.writerow(["fecha", "id", "tienda", "producto", "precio", "estado"])
            w.writerows(filas)

    if cambios or fallos:
        partes = ["<b>Precios del taller</b>"]
        if cambios:
            partes += ["", "Cambios:", *cambios]
        if fallos:
            partes += ["", "No he podido leer:", *fallos, "(Mira el enlace a mano o actualiza la URL en prices.json)"]
        app = os.environ.get("APP_URL")
        if app:
            partes += ["", app]
        telegram("\n".join(partes))
    else:
        print("Sin cambios de precio.")

    # Falla el job solo si no se ha podido leer ninguna ficha (algo gordo pasa).
    total = sum(len(v) for v in data["productos"].values())
    if len(fallos) == total:
        sys.exit("No se ha podido leer ninguna ficha.")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
