"""Recordatorio semanal para revisar a mano los precios de prices.json.

Las webs de Obramat, Leroy Merlin y Brico Depôt bloquean las consultas automáticas
(DataDome y Cloudflare piden un navegador real), así que el precio no se puede leer
solo. En su lugar, este script manda por Telegram la lista de fichas con el último
precio guardado y el enlace para cambiarlos en prices.json.

Variables de entorno: TELEGRAM_TOKEN y TELEGRAM_CHAT_ID (si faltan, solo lo imprime),
APP_URL y EDIT_URL (opcionales, se añaden al final del mensaje).

Uso: python scripts/recordatorio_precios.py
"""
from __future__ import annotations

import datetime as dt
import json
import os
from html import escape
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
PRICES = ROOT / "prices.json"
# Las fichas revisadas hace más de esto se marcan en el mensaje.
DIAS_ANTIGUO = 30


def eur(x: float) -> str:
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def fecha(iso: str | None) -> str:
    try:
        return dt.date.fromisoformat(iso).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return "sin fecha"


def antiguo(iso: str | None, hoy: dt.date) -> bool:
    try:
        return (hoy - dt.date.fromisoformat(iso)).days > DIAS_ANTIGUO
    except (TypeError, ValueError):
        return True


def mensaje(data: dict, hoy: dt.date) -> str:
    partes = [
        "<b>Precios del taller: revisión semanal</b>",
        f"Última actualización de prices.json: {fecha(data.get('actualizado'))}",
        "Abre cada ficha y comprueba el precio:",
    ]
    for ofertas in data["productos"].values():
        for o in ofertas:
            marca = " ⏳" if antiguo(o.get("comprobado"), hoy) else ""
            enlace = f'<a href="{escape(o["url"], quote=True)}">{escape(o["tienda"])} · {escape(o["producto"])}</a>'
            partes.append(f"• {enlace}: {eur(o['precio'])} ({fecha(o.get('comprobado'))}){marca}")
    partes += [
        "",
        f"⏳ = revisado hace más de {DIAS_ANTIGUO} días.",
        "Si alguno ha cambiado, pon el precio nuevo en prices.json (y la fecha en «comprobado» y «actualizado»).",
    ]
    if edit := os.environ.get("EDIT_URL"):
        partes.append(f'<a href="{escape(edit, quote=True)}">Editar prices.json</a>')
    if app := os.environ.get("APP_URL"):
        partes.append(f'<a href="{escape(app, quote=True)}">Abrir la app</a>')
    return "\n".join(partes)


def telegram(text: str) -> bool:
    token, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    print("---- aviso ----\n" + text)
    if not token or not chat:
        print("::warning::Faltan los secretos TELEGRAM_TOKEN/TELEGRAM_CHAT_ID: no se envía el recordatorio.")
        return False
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
        timeout=30,
    )
    if r.status_code != 200:
        raise SystemExit(f"Telegram respondió {r.status_code}: {r.text[:200]}")
    return True


def main():
    data = json.loads(PRICES.read_text(encoding="utf-8"))
    telegram(mensaje(data, dt.date.today()))


if __name__ == "__main__":
    main()
