# V Menu for IngeTrazo

Radial (pie) menu extension for the [IngeTrazo](https://github.com/IngeTrazo/IngeTrazo) 3D CAD/BIM modeler.

Pressing **`V`** opens a 10-tool circular menu directly under the cursor.

<p align="center">
  <img src="ss_dark.png" alt="V Menu Dark Theme" width="48%" />
  <img src="ss_light.png" alt="V Menu Light Theme" width="48%" />
</p>

## Usage

1. Press **`V`** anywhere in the viewport or window.
2. Hover over a tool and left-click to select it.
3. Left-click the **center hub** to toggle Clean Screen mode (`Ctrl+0`).
4. To cancel, press **`Esc`**, press **`V`** again, or right-click.

## Installation

Clone the repository into your IngeTrazo plugins folder:

```powershell
cd "$env:APPDATA\ingetrazo\plugins"
git clone https://github.com/priit123/ingetrazo-v-menu.git v_menu
```

Or link an existing folder using a junction:

```powershell
New-Item -ItemType Junction -Path (Join-Path $env:APPDATA "ingetrazo\plugins\v_menu") -Target "C:\Path\To\ingetrazo-v-menu"
```

Restart IngeTrazo to load the plugin.

## Customization

The tool list can be customized by editing `PIE_ITEMS` in `__init__.py`.

## License

GPL-3.0-or-later
