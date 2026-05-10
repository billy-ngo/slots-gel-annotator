# Branding assets

Drop these files in this directory to brand the desktop shortcut and
the app's window/title icon.

| Filename       | Purpose                                          | Recommended size  |
|----------------|--------------------------------------------------|-------------------|
| `icon.ico`     | Windows shortcut + window icon                   | 256×256 (multi-res `.ico` containing 16/32/48/64/128/256) |
| `icon.icns`    | macOS `.app` bundle icon (skip if absent — macOS will use `icon-512.png` via `sips`) | 1024×1024 |
| `icon-512.png` | High-resolution PNG used for Linux `.desktop`, web favicon, and macOS fallback | 512×512 |
| `icon-192.png` | Smaller PNG (web manifest, web favicon)         | 192×192 |
| `logo-wide.png` | Banner-style logo shown at the top of the README and (optionally) the in-app header | 1200×200 |

PNGs MUST be transparent-background. ICOs/ICNS should bundle multiple
resolutions. If a file is missing the loader silently substitutes a 1×1
transparent PNG and the OS falls back to its default app icon.

To regenerate `icon.icns` from `icon-1024.png` on macOS:

```
mkdir icon.iconset
sips -z 16   16   icon-1024.png --out icon.iconset/icon_16x16.png
sips -z 32   32   icon-1024.png --out icon.iconset/icon_16x16@2x.png
sips -z 32   32   icon-1024.png --out icon.iconset/icon_32x32.png
sips -z 64   64   icon-1024.png --out icon.iconset/icon_32x32@2x.png
sips -z 128  128  icon-1024.png --out icon.iconset/icon_128x128.png
sips -z 256  256  icon-1024.png --out icon.iconset/icon_128x128@2x.png
sips -z 256  256  icon-1024.png --out icon.iconset/icon_256x256.png
sips -z 512  512  icon-1024.png --out icon.iconset/icon_256x256@2x.png
sips -z 512  512  icon-1024.png --out icon.iconset/icon_512x512.png
cp                icon-1024.png         icon.iconset/icon_512x512@2x.png
iconutil -c icns icon.iconset
```
