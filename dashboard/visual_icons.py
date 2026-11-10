"""Small, self-contained, professional outline icons for Quant Intelligence.

Icons are inline SVG (no downloaded fonts, JavaScript, or external icon service).
The icon name is always a key from the built-in catalog, not arbitrary markup.
"""
from __future__ import annotations

# 24-pixel viewBox, consistent 1.8px outline strokes.
_SHAPES = {
    "radar": '<path d="M20.2 15A9 9 0 1 1 9 3.5"/><path d="M21 3 12 12"/><path d="M17 3h4v4"/><circle cx="12" cy="12" r="2"/>',
    "book-open": '<path d="M12 7v14"/><path d="M12 7C9.5 4.5 6 4 3 5v14c3-1 6.5-.5 9 2"/><path d="M12 7c2.5-2.5 6-3 9-2v14c-3-1-6.5-.5-9 2"/>',
    "chart-line": '<path d="M3 3v18h18"/><path d="m6 16 5-5 4 3 5-7"/><path d="M17 7h3v3"/>',
    "briefcase": '<rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M3 12a23 23 0 0 0 18 0"/><path d="M10 12v2h4v-2"/>',
    "credit-card": '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/><path d="M6 15h4"/>',
    "landmark": '<path d="m3 10 9-6 9 6"/><path d="M4 10h16"/><path d="M6 10v9M10 10v9M14 10v9M18 10v9"/><path d="M3 19h18M2 22h20"/>',
    "chart-pie": '<path d="M21 12A9 9 0 1 1 12 3v9z"/><path d="M12 2a10 10 0 0 1 10 10H12z"/>',
    "activity": '<path d="M2 12h4l3-7 5 14 4-7h4"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/><path d="M5 7h14M5 17h14"/>',
    "building": '<rect x="4" y="3" width="16" height="18" rx="1"/><path d="M9 21v-4h6v4M8 7h2M14 7h2M8 11h2M14 11h2"/>',
    "newspaper": '<path d="M4 4h14v16H6a2 2 0 0 1-2-2V4Z"/><path d="M18 8h2v10a2 2 0 0 1-2 2"/><path d="M8 9h6M8 13h6M8 17h4"/><path d="M8 6h6"/>',
    "flask": '<path d="M9 3h6M10 3v7l-6 9a2 2 0 0 0 2 3h12a2 2 0 0 0 2-3l-6-9V3"/><path d="M7 16h10"/>',
    "gem": '<path d="M6 3h12l4 6-10 12L2 9l4-6Z"/><path d="M2 9h20M6 3l3 6 3 12 3-12 3-6"/>',
    "hourglass": '<path d="M5 3h14M5 21h14M7 3v4l5 5-5 5v4M17 3v4l-5 5 5 5v4"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v6l4 2"/>',
    "lightbulb": '<path d="M9 18h6M10 21h4M8 15a7 7 0 1 1 8 0l-1 3H9l-1-3Z"/>',
    "shield": '<path d="m12 2 9 4v5c0 6-4 9-9 11-5-2-9-5-9-11V6l9-4Z"/><path d="m8 12 3 3 5-6"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    "calculator": '<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M8 6h8v4H8zM8 14h1M12 14h1M16 14h1M8 18h1M12 18h1M16 18h1"/>',
    "layers": '<path d="m12 2 9 5-9 5-9-5 9-5ZM3 12l9 5 9-5M3 17l9 5 9-5"/>',
    "waves": '<path d="M2 7c3-4 5 4 8 0s5 4 8 0 4 0 4 0M2 14c3-4 5 4 8 0s5 4 8 0 4 0 4 0M2 21c3-4 5 4 8 0s5 4 8 0 4 0 4 0"/>',
    "sparkles": '<path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z"/><path d="m20 17 .7 2.3L23 20l-2.3.7L20 23l-.7-2.3L17 20l2.3-.7L20 17Z"/><path d="M4 2v4M2 4h4"/>',
}


def icon_svg(name: str, size: int = 24) -> str:
    """Return a self-contained SVG image compatible with Streamlit HTML."""
    from base64 import b64encode

    if name not in _SHAPES:
        raise ValueError(f"Unknown Quant Intelligence icon: {name!r}")
    if not isinstance(size, int) or not 12 <= size <= 64:
        raise ValueError("Icon size must be between 12 and 64")

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{size}" height="{size}" '
        'viewBox="0 0 24 24" fill="none" '
        'stroke="#FF78B7" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round">'
        f'{_SHAPES[name]}</svg>'
    )

    encoded = b64encode(svg.encode("utf-8")).decode("ascii")

    return (
        f'<img class="qi-vector-icon" '
        f'src="data:image/svg+xml;base64,{encoded}" '
        f'width="{size}" height="{size}" '
        'alt="" aria-hidden="true" draggable="false">'
    )
