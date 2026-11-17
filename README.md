# Despiece de taller

App web para sacar el despiece de un mueble, el plan de cortes, la lista para la tienda y el coste. Los precios de los materiales se revisan solos cada lunes en las webs de Obramat, Leroy Merlin y Brico Depôt, y si cambian llega un aviso por Telegram.

- `index.html`: la app. Se publica con GitHub Pages y lee `prices.json`.
- `prices.json`: los productos de cada tienda con su precio actual y el anterior.
- `history.csv`: histórico de precios. Cada semana se añade una línea por producto.
- `scripts/update_prices.py`: lee el precio de cada ficha de producto y avisa por Telegram.
- `.github/workflows/precios.yml`: lo ejecuta cada lunes. También puedes lanzarlo a mano.

Tus piezas y materiales se guardan solo en tu navegador; el repositorio no los guarda.

## Puesta en marcha (una vez)

1. **Bot de Telegram**
   - En Telegram, habla con **@BotFather**, envía `/newbot` y sigue los pasos. Te dará un *token*.
   - Escribe cualquier cosa a tu bot nuevo.
   - Abre `https://api.telegram.org/bot<TOKEN>/getUpdates` en el navegador y copia el número de `"chat":{"id": ...}`. Ese es tu *chat id*.
2. **Secretos del repositorio**: en *Settings → Secrets and variables → Actions → New repository secret*, crea:
   - `TELEGRAM_TOKEN` con el token del bot
   - `TELEGRAM_CHAT_ID` con tu chat id
3. **GitHub Pages**: en *Settings → Pages*, en *Source* elige *Deploy from a branch*, la rama `main` y la carpeta `/ (root)`. La app quedará en `https://<tu-usuario>.github.io/<repo>/`.
4. **Primera prueba**: en *Actions → Comprobar precios → Run workflow*. En el registro verás `[OK]` o `[FALLO]` por cada producto.

## Añadir o cambiar productos

En `prices.json`, cada material (`pata`, `trav`, `tapa`, `balda`, `rueda`) tiene una lista de ofertas. Para añadir otra, copia una entrada, cambia `id`, `tienda`, `producto`, `url` y `precio` (el aproximado vale; se corrige en la siguiente comprobación). En los tableros indica también `largo` y `ancho` en mm.

## Si una tienda falla

Algunas webs bloquean las consultas automáticas o cambian sus fichas. Si una falla, el aviso de Telegram te lo dirá, la app la marcará como «no se pudo comprobar» y se mantendrá el último precio conocido. Lo normal es que baste con poner la URL nueva de la ficha.
