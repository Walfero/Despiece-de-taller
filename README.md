# Despiece de taller

App web para sacar el despiece de un mueble, el plan de cortes, los planos de cada pieza con sus medidas, cantos y veta (y del mueble montado, de frente y de lado), los pasos de montaje con la tornillería, la lista para la tienda y el coste. La «Hoja de taller» lo imprime todo o lo guarda en PDF. 

Cada lunes llega un recordatorio por Telegram con las fichas de Obramat, Leroy Merlin y Brico Depôt y su último precio, para revisarlos a mano.

- `index.html`: la app. Se publica con GitHub Pages y lee `prices.json`.
- `prices.json`: los productos de cada tienda con su precio y la fecha en que se revisó.
- `scripts/recordatorio_precios.py`: manda por Telegram la lista de fichas con su precio y su enlace.
- `.github/workflows/precios.yml`: lo ejecuta cada lunes. También puedes lanzarlo a mano.

Tus piezas y materiales se guardan solo en tu navegador; el repositorio no los guarda. Puedes descargar un proyecto (o una copia de todos) en un archivo `.json` y abrirlo en otro sitio, o compartirlo con un enlace que lleva el proyecto dentro.

## Puesta en marcha (una vez)

1. **Bot de Telegram**
   - En Telegram, habla con **@BotFather**, envía `/newbot` y sigue los pasos. Te dará un *token*.
   - Escribe cualquier cosa a tu bot nuevo.
   - Abre `https://api.telegram.org/bot<TOKEN>/getUpdates` en el navegador y copia el número de `"chat":{"id": ...}`. Ese es tu *chat id*.
2. **Secretos del repositorio**: en *Settings → Secrets and variables → Actions → New repository secret*, crea:
   - `TELEGRAM_TOKEN` con el token del bot
   - `TELEGRAM_CHAT_ID` con tu chat id
3. **GitHub Pages**: en *Settings → Pages*, en *Source* elige *Deploy from a branch*, la rama `main` y la carpeta `/ (root)`. La app quedará en `https://<tu-usuario>.github.io/<repo>/`.
4. **Primera prueba**: en *Actions → Recordatorio de precios → Run workflow*. Te llegará el mensaje a Telegram; si faltan los secretos, el registro lo avisa.

## Añadir o cambiar productos

En `prices.json`, cada material (`pata`, `trav`, `tapa`, `balda`, `rueda`, `melamina`, `dm`, `trasera`, `guias`, `tirador`) tiene una lista de ofertas. La app elige la lista por el nombre del material: «Melamina…», «DM…» o «MDF…», un tablero de 5 mm o menos (trasera), «Contrachapado…» (tapa), «OSB…» (balda), «Guías…» y «Tirador». Para añadir otra, copia una entrada, cambia `id`, `tienda`, `producto`, `url` y `precio`. En los tableros indica también `largo` y `ancho` en mm.

## Revisar los precios

Las tres tiendas bloquean las consultas automáticas (Obramat y Leroy Merlin con DataDome, Brico Depôt con Cloudflare), incluso desde una conexión doméstica, así que los precios se revisan a mano. Cuando llegue el recordatorio:

1. Abre las fichas del mensaje. Las marcadas con ⏳ llevan más de 30 días sin revisar.
2. Si un precio ha cambiado, pulsa «Editar prices.json» en el mensaje y cambia `precio`. Si quieres que la app enseñe si ha subido o bajado, copia el precio viejo en `precio_anterior`.
3. Pon la fecha de hoy en `comprobado` de esa ficha y en `actualizado` arriba del todo, y guarda (*Commit changes*). La app usa los precios nuevos en cuanto se publica.
