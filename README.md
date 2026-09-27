# Constellation Tracker — iPhone web app (PWA)

A mobile version of `Universal_Constellation_Tracker.html`. It uses the same SGP4, orbit-shell and Doppler engine, with a touch UI and offline caching. You install it on iPhone from Safari with **Add to Home Screen**. You don't need a Mac, Xcode or an Apple Developer account.

## Files
| File | Purpose |
|---|---|
| `index.html` | The app (CesiumJS globe + satellite.js SGP4) |
| `manifest.webmanifest` | App name, icons and standalone display for the home screen |
| `sw.js` | Service worker: offline app shell, CDN libraries and map tiles |
| `icons/` | Home-screen icons (180 px apple-touch, 192, 512, maskable) |
| `.github/workflows/tle-mirror.yml` | Optional: mirrors CelesTrak TLEs into `tle/` every 6 h as a fallback |

## Put it online (GitHub Pages, free, about 5 min)
The app must be served over **HTTPS**. Location, compass, the service worker and installing all need HTTPS.

1. Create a new **public** repo on github.com, e.g. `sat-tracker`.
2. Upload the *contents* of this folder to the repo root: **Add file → Upload files**, then drag everything in, including the `.github` and `icons` folders. If the web uploader skips the `.github` folder, create `.github/workflows/tle-mirror.yml` by hand with **Add file → Create new file**.
3. Go to **Settings → Pages → Build and deployment**, choose Source = *Deploy from a branch*, Branch = `main` / `(root)`, and click **Save**.
4. After about a minute the app is at `https://<your-user>.github.io/sat-tracker/`.
5. Optional: go to **Actions → Mirror CelesTrak TLEs → Run workflow** once to seed `tle/`. After that it runs every 6 h.

## Install on iPhone
1. Open the URL in **Safari**. Other browsers on iOS can't install web apps.
2. Tap **Share ⬆︎ → Add to Home Screen → Add**.
3. Launch it from the home screen. It runs full-screen with no browser bars, and reopens with your constellations, UE location and settings.

## Using it
* **Globe:** drag to rotate, pinch to zoom, **tap** a satellite to select it (tap radius about 24 px), **long-press** the ground to move the UE there.
* **Bottom sheet:** drag the handle between peek, half and full, or tap the handle to toggle.
  * **Link:** serving/selected satellite telemetry (el/az, range, delay, Doppler and Doppler rate, FSPL). A selected satellite also gets its pass Doppler curve and the next 24 h of passes; tap a pass to jump there.
  * **Sky:** polar sky plot, **Compass** mode (heading-up, hold the phone flat) and a list of what's above the mask.
  * **Layers:** tap constellations to add or remove them, search by name or NORAD ID, load a TLE file from the Files app, filter by shell, regime or plane (press and hold a chip = show only that one).
  * **Setup:** **Use my location**, mask, f_c presets (L, S n256, Ku, Ka), base map, keep screen awake, rendering quality.
* **Top bar:** play/pause, speed (tap to cycle 1–1200×), **Now**. Tap the clock for a date picker and a −12 h…+24 h scrubber.

## Notes and limits
* **TLE source order:** device cache (< 2 h old) → CelesTrak → the `tle/` mirror → any stale cache. It works offline with the last TLEs it downloaded.
* **Compass:** `webkitCompassHeading` on iOS is referenced to **magnetic** north, and no declination correction is applied (declination is about −6° in Shanghai).
* **Performance:** Starlink (about 9–10k objects) runs on recent iPhones at *Balanced* quality. Use *Battery* for long sessions.
* **Background:** iOS suspends web apps in the background, so there are no background pass alerts. That needs the native (SwiftUI) route.
* **Updating:** edit `index.html` and bump `VERSION` in `sw.js`. The installed app picks up the new build on its next launch.
* **Desktop:** the same file works on a desktop browser (the panel docks on the right) and still opens by double-click from disk. Offline caching and location only work when it's hosted over HTTPS.
