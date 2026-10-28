# V Menu — Pie / Radial Menu for IngeTrazo

Sleek, fast circular tool menu (Pie / Radial Menu) for the **IngeTrazo** 3D CAD/BIM modeler.

---

## How to Use

1. Launch IngeTrazo.
2. Press **`V`** on your keyboard (anywhere in the viewport or window).
3. A 10-slice radial menu appears directly under your cursor.
4. Move your mouse over the desired tool (the slice highlights in IngeTrazo orange) and click.
5. The menu automatically closes and the selected tool is immediately active!

> [!TIP]
> - You can dismiss the menu without picking a tool by pressing **`V`** again, pressing **`Esc`**, or **right-clicking**.

---

## Tool Layout (Clockwise from North / 12:00)

| # | Slice Position | Tool | Key | Description |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **North (12:00)** | **Push/Pull** | `P` | Extrude and push/pull faces into 3D geometry |
| **2** | **North-East (01:12)** | **Move** | `M` | Move selected geometry or objects |
| **3** | **East-North-East (02:24)** | **Rotate** | `Q` | Rotate geometry around an axis |
| **4** | **East-South-East (03:36)** | **Scale** | `S` | Scale selected geometry |
| **5** | **South-East (04:48)** | **Offset** | `F` | Offset edges and contours |
| **6** | **South (06:00)** | **Delete** | `Del` | Delete selected entities (one Undo step) |
| **7** | **South-West (07:12)** | **Line** | `L` | Draw straight lines and edges |
| **8** | **West-South-West (08:24)** | **Rectangle** | `R` | Draw planar rectangular faces |
| **9** | **West-North-West (09:36)** | **Circle** | `C` | Draw circular faces and polygons |
| **10** | **North-North-West (10:48)** | **Tape Measure** | `T` | Measure distances and create guides |

---

## Customizing Tools

At the top of [`__init__.py`](file:///c:/Users/shrek/kDrive/KOOD/Google%20Antigravity/IngeT%20menu/__init__.py), you will find the `PIE_ITEMS` list. You can easily add, remove, or swap tools.

---

## Installation

Create a directory junction into your IngeTrazo plugins directory:
```powershell
New-Item -ItemType Junction -Path (Join-Path $env:APPDATA "ingetrazo\plugins\v_menu") -Target "c:\Users\shrek\kDrive\KOOD\Google Antigravity\IngeT menu"
```
Then restart IngeTrazo.
