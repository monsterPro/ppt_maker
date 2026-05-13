"""Master/layout enhancement helpers for generated PPTX packages."""

from __future__ import annotations

import re
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path


P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

ET.register_namespace("p", P_NS)
ET.register_namespace("a", A_NS)
ET.register_namespace("r", R_NS)


def _q(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


def _next_shape_id(sp_tree: ET.Element) -> int:
    max_id = 1
    for c_nv_pr in sp_tree.findall(f".//{_q(P_NS, 'cNvPr')}"):
        value = c_nv_pr.get("id")
        if value and value.isdigit():
            max_id = max(max_id, int(value))
    return max_id + 1


def _remove_named_shapes(sp_tree: ET.Element, names: set[str]) -> None:
    for shape in list(sp_tree.findall(_q(P_NS, "sp"))):
        c_nv_pr = shape.find(f"./{_q(P_NS, 'nvSpPr')}/{_q(P_NS, 'cNvPr')}")
        if c_nv_pr is not None and c_nv_pr.get("name") in names:
            sp_tree.remove(shape)


def _remove_all_shapes(sp_tree: ET.Element) -> None:
    """Remove inherited default-template shapes from the master/layout."""
    for shape in list(sp_tree.findall(_q(P_NS, "sp"))):
        sp_tree.remove(shape)


def _hex_token(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    color = value.strip().lstrip("#").upper()
    return color if re.fullmatch(r"[0-9A-F]{6}", color) else fallback


def _font_token(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    first = value.split(",", 1)[0].strip().strip('"').strip("'")
    return first or fallback


def _size_token(value: str | None, fallback_px: int) -> int:
    try:
        px = float(value) if value else fallback_px
    except ValueError:
        px = fallback_px
    # SVG px to DrawingML hundredths of a point: px * 0.75pt * 100.
    return max(800, int(round(px * 75)))


def _def_rpr_xml(
    font_size: int,
    color: str,
    typeface: str,
    bold: bool = False,
    tag: str = "a:defRPr",
) -> str:
    bold_attr = ' b="1"' if bold else ""
    return f"""
<{tag} sz="{font_size}"{bold_attr} kern="1200">
  <a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
  <a:latin typeface="{typeface}"/>
  <a:ea typeface="{typeface}"/>
  <a:cs typeface="{typeface}"/>
</{tag}>
"""


def _shape_xml(
    shape_id: int,
    name: str,
    x: int,
    y: int,
    w: int,
    h: int,
    body_xml: str,
) -> ET.Element:
    xml = f"""
<p:sp xmlns:p="{P_NS}" xmlns:a="{A_NS}" xmlns:r="{R_NS}">
  <p:nvSpPr>
    <p:cNvPr id="{shape_id}" name="{name}"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm>
      <a:off x="{x}" y="{y}"/>
      <a:ext cx="{w}" cy="{h}"/>
    </a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  {body_xml}
</p:sp>
"""
    return ET.fromstring(xml)


def _solid_rect_xml(
    shape_id: int,
    name: str,
    x: int,
    y: int,
    w: int,
    h: int,
    color: str,
    alpha: int = 100000,
) -> ET.Element:
    alpha = max(0, min(alpha, 100000))
    alpha_xml = f'<a:alpha val="{alpha}"/>' if alpha < 100000 else ""
    xml = f"""
<p:sp xmlns:p="{P_NS}" xmlns:a="{A_NS}" xmlns:r="{R_NS}">
  <p:nvSpPr>
    <p:cNvPr id="{shape_id}" name="{name}"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm>
      <a:off x="{x}" y="{y}"/>
      <a:ext cx="{w}" cy="{h}"/>
    </a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:solidFill>
      <a:srgbClr val="{color}">{alpha_xml}</a:srgbClr>
    </a:solidFill>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
</p:sp>
"""
    return ET.fromstring(xml)


def _add_header_accent(
    sp_tree: ET.Element,
    width_emu: int,
    height_emu: int,
    design_tokens: dict[str, dict[str, str]],
) -> None:
    """Add the standard content-slide header accent to the master."""
    primary = _hex_token(design_tokens.get("colors", {}).get("primary"), "A855F7")
    sx = width_emu / 1280
    sy = height_emu / 720
    next_id = _next_shape_id(sp_tree)

    sp_tree.append(
        _solid_rect_xml(
            next_id,
            "PPT Master Header Accent Bar",
            round(60 * sx),
            round(67 * sy),
            max(1, round(3 * sx)),
            max(1, round(40 * sy)),
            primary,
        )
    )
    next_id += 1
    sp_tree.append(
        _solid_rect_xml(
            next_id,
            "PPT Master Header Underline",
            round(81 * sx),
            round(118 * sy),
            max(1, round(1118 * sx)),
            max(1, round(1 * sy)),
            primary,
            20000,
        )
    )


def _layout_uses_content_header(layout_num: int) -> bool:
    """Return True for layouts that should mimic regular content-slide chrome."""
    return layout_num not in {1, 3, 7}


def _header_title_textbox(width_emu: int, height_emu: int) -> tuple[int, int, int, int]:
    """Match the SVG-to-PPTX textbox created for x=81, y=100, font-size=43."""
    sx = width_emu / 1280
    sy = height_emu / 720
    return (
        round(76.7 * sx),
        round(63.45 * sy),
        round(1122.6 * sx),
        round(68.8 * sy),
    )


def _svg_box(
    width_emu: int,
    height_emu: int,
    x: float,
    y: float,
    w: float,
    h: float,
) -> tuple[int, int, int, int]:
    sx = width_emu / 1280
    sy = height_emu / 720
    return (round(x * sx), round(y * sy), round(w * sx), round(h * sy))


def _centered_textbox(
    width_emu: int,
    height_emu: int,
    cx: float,
    baseline_y: float,
    box_w: float,
    font_px: float,
    lines: int = 1,
) -> tuple[int, int, int, int]:
    x = cx - box_w / 2
    y = baseline_y - font_px * 0.85
    h = font_px * (1.3 * max(1, lines) + 0.2)
    return _svg_box(width_emu, height_emu, x, y, box_w, h)


def _placeholder_body(
    label: str,
    font_size: int,
    color: str,
    typeface: str,
    bold: bool = False,
    insets: tuple[int, int, int, int] | None = None,
) -> str:
    bold_attr = ' b="1"' if bold else ''
    l_ins, t_ins, r_ins, b_ins = insets or (91440, 45720, 91440, 45720)
    def_rpr = _def_rpr_xml(font_size, color, typeface, bold).strip()
    end_rpr = _def_rpr_xml(font_size, color, typeface, bold, tag="a:endParaRPr").strip()
    escaped = (
        label.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return f"""
<p:txBody xmlns:p="{P_NS}" xmlns:a="{A_NS}">
  <a:bodyPr wrap="square" lIns="{l_ins}" tIns="{t_ins}" rIns="{r_ins}" bIns="{b_ins}" anchor="t">
    <a:normAutofit/>
  </a:bodyPr>
  <a:lstStyle>
    <a:lvl1pPr algn="l">
      {def_rpr}
    </a:lvl1pPr>
  </a:lstStyle>
  <a:p>
    <a:pPr algn="l">
      {def_rpr}
    </a:pPr>
    <a:r>
      <a:rPr lang="en-US" sz="{font_size}"{bold_attr} dirty="0">
        <a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
        <a:latin typeface="{typeface}"/>
        <a:ea typeface="{typeface}"/>
        <a:cs typeface="{typeface}"/>
      </a:rPr>
      <a:t>{escaped}</a:t>
    </a:r>
    {end_rpr}
  </a:p>
</p:txBody>
"""


def _placeholder_shape_xml(
    shape_id: int,
    name: str,
    ph_type: str,
    idx: int | None,
    x: int,
    y: int,
    w: int,
    h: int,
    label: str,
    font_size: int,
    text_color: str,
    border_color: str,
    typeface: str,
    bold: bool = False,
    body_insets: tuple[int, int, int, int] | None = None,
) -> ET.Element:
    idx_attr = f' idx="{idx}"' if idx is not None else ""
    xml = f"""
<p:sp xmlns:p="{P_NS}" xmlns:a="{A_NS}" xmlns:r="{R_NS}">
  <p:nvSpPr>
    <p:cNvPr id="{shape_id}" name="{name}"/>
    <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
    <p:nvPr><p:ph type="{ph_type}"{idx_attr}/></p:nvPr>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm>
      <a:off x="{x}" y="{y}"/>
      <a:ext cx="{w}" cy="{h}"/>
    </a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  {_placeholder_body(label, font_size, text_color, typeface, bold, body_insets)}
</p:sp>
"""
    return ET.fromstring(xml)


def _footer_text_body(text: str, color: str, typeface: str, font_size: int) -> str:
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return f"""
<p:txBody xmlns:p="{P_NS}" xmlns:a="{A_NS}">
  <a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"/>
  <a:lstStyle/>
  <a:p>
    <a:pPr algn="l"/>
    <a:r>
      <a:rPr lang="en-US" sz="{font_size}" dirty="0">
        <a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
        <a:latin typeface="{typeface}"/>
        <a:ea typeface="{typeface}"/>
        <a:cs typeface="{typeface}"/>
      </a:rPr>
      <a:t>{escaped}</a:t>
    </a:r>
  </a:p>
</p:txBody>
"""


def _slide_number_body(color: str, typeface: str, font_size: int) -> str:
    field_id = "{" + str(uuid.uuid4()).upper() + "}"
    return f"""
<p:txBody xmlns:p="{P_NS}" xmlns:a="{A_NS}">
  <a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"/>
  <a:lstStyle/>
  <a:p>
    <a:pPr algn="r"/>
    <a:fld id="{field_id}" type="slidenum">
      <a:rPr lang="en-US" sz="{font_size}" dirty="0">
        <a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
        <a:latin typeface="{typeface}"/>
        <a:ea typeface="{typeface}"/>
        <a:cs typeface="{typeface}"/>
      </a:rPr>
      <a:t>#</a:t>
    </a:fld>
  </a:p>
</p:txBody>
"""


def _glow_shape_xml(
    shape_id: int,
    name: str,
    color: str,
    alpha: int,
    x: int,
    y: int,
    w: int,
    h: int,
) -> ET.Element:
    alpha = max(0, min(alpha, 100000))
    mid_alpha = max(0, min(round(alpha * 0.35), 100000))
    xml = f"""
<p:sp xmlns:p="{P_NS}" xmlns:a="{A_NS}" xmlns:r="{R_NS}">
  <p:nvSpPr>
    <p:cNvPr id="{shape_id}" name="{name}"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm>
      <a:off x="{x}" y="{y}"/>
      <a:ext cx="{w}" cy="{h}"/>
    </a:xfrm>
    <a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>
    <a:gradFill flip="none" rotWithShape="1">
      <a:gsLst>
        <a:gs pos="0">
          <a:srgbClr val="{color}"><a:alpha val="{alpha}"/></a:srgbClr>
        </a:gs>
        <a:gs pos="52000">
          <a:srgbClr val="{color}"><a:alpha val="{mid_alpha}"/></a:srgbClr>
        </a:gs>
        <a:gs pos="100000">
          <a:srgbClr val="{color}"><a:alpha val="0"/></a:srgbClr>
        </a:gs>
      </a:gsLst>
      <a:path path="circle">
        <a:fillToRect l="50000" t="50000" r="50000" b="50000"/>
      </a:path>
      <a:tileRect/>
    </a:gradFill>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
</p:sp>
"""
    return ET.fromstring(xml)


def _svg_radial_gradient_ellipse_xml(
    shape_id: int,
    name: str,
    width_emu: int,
    height_emu: int,
    cx_pct: float,
    cy_pct: float,
    r_pct: float,
    stops: list[tuple[int, str, int]],
) -> ET.Element:
    """Create an OOXML ellipse matching an SVG objectBoundingBox radialGradient."""
    cx = width_emu * cx_pct
    cy = height_emu * cy_pct
    rx = width_emu * r_pct
    ry = height_emu * r_pct
    x = round(cx - rx)
    y = round(cy - ry)
    w = round(rx * 2)
    h = round(ry * 2)

    stops_xml = "\n".join(
        f'<a:gs pos="{pos}"><a:srgbClr val="{color}"><a:alpha val="{alpha}"/></a:srgbClr></a:gs>'
        for pos, color, alpha in stops
    )
    xml = f"""
<p:sp xmlns:p="{P_NS}" xmlns:a="{A_NS}" xmlns:r="{R_NS}">
  <p:nvSpPr>
    <p:cNvPr id="{shape_id}" name="{name}"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm>
      <a:off x="{x}" y="{y}"/>
      <a:ext cx="{w}" cy="{h}"/>
    </a:xfrm>
    <a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>
    <a:gradFill flip="none" rotWithShape="1">
      <a:gsLst>
        {stops_xml}
      </a:gsLst>
      <a:path path="circle">
        <a:fillToRect l="50000" t="50000" r="50000" b="50000"/>
      </a:path>
    </a:gradFill>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
</p:sp>
"""
    return ET.fromstring(xml)


def _set_master_background(master_root: ET.Element, background_color: str | None) -> None:
    if not background_color:
        return
    color = background_color.lstrip("#").upper()
    if not re.fullmatch(r"[0-9A-F]{6}", color):
        return

    c_sld = master_root.find(_q(P_NS, "cSld"))
    if c_sld is None:
        return

    bg = c_sld.find(_q(P_NS, "bg"))
    if bg is None:
        bg = ET.Element(_q(P_NS, "bg"))
        c_sld.insert(0, bg)
    for child in list(bg):
        bg.remove(child)

    bg_pr = ET.SubElement(bg, _q(P_NS, "bgPr"))
    solid = ET.SubElement(bg_pr, _q(A_NS, "solidFill"))
    ET.SubElement(solid, _q(A_NS, "srgbClr"), {"val": color})
    ET.SubElement(bg_pr, _q(A_NS, "effectLst"))


def _set_master_text_styles(
    master_root: ET.Element,
    title_font: str,
    title_size: int,
    title_color: str,
    body_font: str,
    body_size: int,
    body_color: str,
) -> None:
    """Replace master txStyles so new placeholder text follows deck tokens."""
    for existing in list(master_root.findall(_q(P_NS, "txStyles"))):
        master_root.remove(existing)

    def lvl_style(tag: str, size: int, color: str, typeface: str, bold: bool = False) -> str:
        return f"""
<p:{tag} xmlns:p="{P_NS}" xmlns:a="{A_NS}">
  <a:lvl1pPr marL="0" algn="l" defTabSz="457200" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1">
    {_def_rpr_xml(size, color, typeface, bold).strip()}
  </a:lvl1pPr>
  <a:lvl2pPr marL="457200" algn="l" defTabSz="457200" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1">
    {_def_rpr_xml(body_size, body_color, body_font).strip()}
  </a:lvl2pPr>
</p:{tag}>
"""

    tx_styles = ET.fromstring(f"""
<p:txStyles xmlns:p="{P_NS}" xmlns:a="{A_NS}">
  {lvl_style("titleStyle", title_size, title_color, title_font, True)}
  {lvl_style("bodyStyle", body_size, body_color, body_font)}
  {lvl_style("otherStyle", body_size, body_color, body_font)}
</p:txStyles>
""")

    ext_lst = master_root.find(_q(P_NS, "extLst"))
    if ext_lst is not None:
        index = list(master_root).index(ext_lst)
        master_root.insert(index, tx_styles)
    else:
        master_root.append(tx_styles)


def _add_layout_placeholders(
    sp_tree: ET.Element,
    layout_num: int,
    width_emu: int,
    height_emu: int,
    design_tokens: dict[str, dict[str, str]],
) -> None:
    colors = design_tokens.get("colors", {})
    typography = design_tokens.get("typography", {})
    primary = _hex_token(colors.get("primary"), "A855F7")
    title_color = _hex_token(colors.get("text"), "FFFFFF")
    body_color = _hex_token(colors.get("text_secondary"), "94A3B8")
    title_font = _font_token(typography.get("title_family"), "Poppins")
    body_font = _font_token(typography.get("body_family"), "Lato")
    title_size = _size_token(typography.get("title"), 43)
    body_size = _size_token(typography.get("body"), 20)
    subtitle_size = _size_token(typography.get("subtitle"), 24)

    title_x, title_y, title_w, title_h = _header_title_textbox(width_emu, height_emu)
    left = round(81 * width_emu / 1280)
    top = title_y
    full_w = round(1118 * width_emu / 1280)
    body_top = int(height_emu * 0.24)
    body_h = int(height_emu * 0.56)
    gap = int(width_emu * 0.035)
    col_w = int((full_w - gap) / 2)

    next_id = _next_shape_id(sp_tree)

    if _layout_uses_content_header(layout_num):
        _add_header_accent(sp_tree, width_emu, height_emu, design_tokens)
        next_id = _next_shape_id(sp_tree)

    def add(
        ph_type: str,
        idx: int | None,
        x: int,
        y: int,
        w: int,
        h: int,
        label: str,
        size: int,
        color: str,
        typeface: str,
        bold: bool = False,
        body_insets: tuple[int, int, int, int] | None = None,
    ) -> None:
        nonlocal next_id
        sp_tree.append(
            _placeholder_shape_xml(
                next_id,
                f"{label} Placeholder",
                ph_type,
                idx,
                x,
                y,
                w,
                h,
                label,
                size,
                color,
                primary,
                typeface,
                bold,
                body_insets,
            )
        )
        next_id += 1

    def add_rect(name: str, x: float, y: float, w: float, h: float, alpha: int = 100000) -> None:
        nonlocal next_id
        sp_tree.append(
            _solid_rect_xml(
                next_id,
                name,
                *_svg_box(width_emu, height_emu, x, y, w, h),
                primary,
                alpha,
            )
        )
        next_id += 1

    if layout_num == 1:
        add("body", 2, *_centered_textbox(width_emu, height_emu, 640, 218, 620, 24), "Category Label", _size_token("24", 24), primary, title_font, True, (0, 0, 0, 0))
        add_rect("Title Slide Center Divider", 580, 234, 120, 1, 55000)
        add("title", None, *_centered_textbox(width_emu, height_emu, 640, 326, 1120, 58), "Presentation Title", _size_token("58", 58), title_color, title_font, True, (0, 0, 0, 0))
        add("subTitle", 1, *_centered_textbox(width_emu, height_emu, 640, 378, 1040, 28, 2), "Subtitle", subtitle_size, title_color, body_font, False, (0, 0, 0, 0))
        add("body", 3, *_centered_textbox(width_emu, height_emu, 640, 460, 620, 23, 2), "Author / Date", _size_token("23", 23), body_color, body_font, False, (0, 0, 0, 0))
    elif layout_num == 3:
        add("body", 2, *_centered_textbox(width_emu, height_emu, 640, 248, 520, 24), "Chapter Label", _size_token("24", 24), primary, title_font, True, (0, 0, 0, 0))
        add_rect("Section Header Center Divider", 580, 264, 120, 1, 55000)
        add("title", None, *_centered_textbox(width_emu, height_emu, 640, 370, 1120, 72), "Section Title", _size_token("72", 72), title_color, title_font, True, (0, 0, 0, 0))
        add("subTitle", 1, *_centered_textbox(width_emu, height_emu, 640, 428, 940, 28), "Section Subtitle", subtitle_size, body_color, body_font, False, (0, 0, 0, 0))
    elif layout_num in {4, 5}:
        add("title", None, title_x, top, title_w, title_h, "Title", title_size, title_color, title_font, True, (0, 0, 0, 0))
        add("body", 1, left, body_top, col_w, body_h, "Left Content", body_size, body_color, body_font)
        add("body", 2, left + col_w + gap, body_top, col_w, body_h, "Right Content", body_size, body_color, body_font)
    elif layout_num == 6:
        add("title", None, title_x, top, title_w, title_h, "Title", title_size, title_color, title_font, True, (0, 0, 0, 0))
    elif layout_num == 7:
        # Keep the generated deck's assigned Blank layout clean.
        return
    else:
        add("title", None, title_x, top, title_w, title_h, "Title", title_size, title_color, title_font, True, (0, 0, 0, 0))
        add("body", 1, left, body_top, full_w, body_h, "Content", body_size, body_color, body_font)


def _add_master_style_placeholders(
    sp_tree: ET.Element,
    width_emu: int,
    height_emu: int,
    design_tokens: dict[str, dict[str, str]],
) -> None:
    """Add visible style placeholders to the top Slide Master itself."""
    colors = design_tokens.get("colors", {})
    typography = design_tokens.get("typography", {})
    primary = _hex_token(colors.get("primary"), "A855F7")
    title_color = _hex_token(colors.get("text"), "FFFFFF")
    body_color = _hex_token(colors.get("text_secondary"), "94A3B8")
    muted_color = _hex_token(colors.get("text_muted"), "64748B")
    title_font = _font_token(typography.get("title_family"), "Poppins")
    body_font = _font_token(typography.get("body_family"), "Lato")
    title_size = _size_token(typography.get("title"), 43)
    body_size = _size_token(typography.get("body"), 20)

    title_x, title_top, title_w, title_h = _header_title_textbox(width_emu, height_emu)
    left = round(81 * width_emu / 1280)
    body_top = int(height_emu * 0.285)
    body_w = round(1118 * width_emu / 1280)
    body_h = int(height_emu * 0.46)

    next_id = _next_shape_id(sp_tree)
    sp_tree.append(
        _placeholder_shape_xml(
            next_id,
            "Master Title Style Placeholder",
            "title",
            None,
            title_x,
            title_top,
            title_w,
            title_h,
            "Click to edit master title style",
            title_size,
            title_color,
            primary,
            title_font,
            True,
            (0, 0, 0, 0),
        )
    )
    next_id += 1
    sp_tree.append(
        _placeholder_shape_xml(
            next_id,
            "Master Body Style Placeholder",
            "body",
            1,
            left,
            body_top,
            body_w,
            body_h,
            "Click to edit master body style",
            body_size,
            body_color,
            muted_color,
            body_font,
        )
    )


def _clean_slide_layouts(
    extract_dir: Path,
    width_emu: int,
    height_emu: int,
    design_tokens: dict[str, dict[str, str]],
) -> None:
    layouts_dir = extract_dir / "ppt" / "slideLayouts"
    if not layouts_dir.exists():
        return

    for layout_path in layouts_dir.glob("slideLayout*.xml"):
        tree = ET.parse(layout_path)
        root = tree.getroot()
        c_sld = root.find(_q(P_NS, "cSld"))
        sp_tree = c_sld.find(_q(P_NS, "spTree")) if c_sld is not None else None
        if sp_tree is None:
            continue

        _remove_all_shapes(sp_tree)
        match = re.search(r"slideLayout(\d+)\.xml$", layout_path.name)
        layout_num = int(match.group(1)) if match else 0
        _add_layout_placeholders(sp_tree, layout_num, width_emu, height_emu, design_tokens)
        tree.write(layout_path, encoding="UTF-8", xml_declaration=True)


def enhance_existing_master(
    extract_dir: Path,
    width_emu: int,
    height_emu: int,
    footer_text: str = "",
    background_color: str | None = None,
    design_tokens: dict[str, dict[str, str]] | None = None,
    master_glows: list[dict[str, object]] | None = None,
) -> None:
    """Add reusable deck chrome to the existing python-pptx master.

    The base package already contains a valid master/layout relationship graph.
    We intentionally modify that graph in place instead of inserting a new
    master, which avoids the fragile OOXML bookkeeping that caused repair
    prompts in earlier post-processing attempts.
    """
    master_path = extract_dir / "ppt" / "slideMasters" / "slideMaster1.xml"
    if not master_path.exists():
        return

    tree = ET.parse(master_path)
    root = tree.getroot()
    c_sld = root.find(_q(P_NS, "cSld"))
    sp_tree = c_sld.find(_q(P_NS, "spTree")) if c_sld is not None else None
    if sp_tree is None:
        return

    design_tokens = design_tokens or {'colors': {}, 'typography': {}}
    colors = design_tokens.get("colors", {})
    typography = design_tokens.get("typography", {})
    footer_color = _hex_token(colors.get("text_muted"), "64748B")
    title_color = _hex_token(colors.get("text"), "FFFFFF")
    body_color = _hex_token(colors.get("text_secondary"), "94A3B8")
    title_font = _font_token(typography.get("title_family"), "Poppins")
    body_font = _font_token(typography.get("body_family"), "Lato")
    title_size = _size_token(typography.get("title"), 43)
    body_size = _size_token(typography.get("body"), 20)
    footer_size = _size_token(typography.get("label"), 13)

    _set_master_background(root, background_color)
    _set_master_text_styles(
        root,
        title_font=title_font,
        title_size=title_size,
        title_color=title_color,
        body_font=body_font,
        body_size=body_size,
        body_color=body_color,
    )
    _remove_all_shapes(sp_tree)

    margin_x = 580000
    footer_y = max(0, height_emu - 520000)
    footer_h = 180000

    next_id = _next_shape_id(sp_tree)
    for glow in master_glows or []:
        stops = glow.get("stops")
        if not isinstance(stops, list) or not stops:
            continue
        sp_tree.append(
            _svg_radial_gradient_ellipse_xml(
                next_id,
                f"PPT Master SVG {glow.get('id') or 'radialGradient'}",
                width_emu,
                height_emu,
                float(glow.get("cx", 0.5)),
                float(glow.get("cy", 0.5)),
                float(glow.get("r", 0.5)),
                stops,
            )
        )
        next_id += 1

    _add_master_style_placeholders(
        sp_tree,
        width_emu=width_emu,
        height_emu=height_emu,
        design_tokens=design_tokens,
    )
    next_id = _next_shape_id(sp_tree)

    if footer_text:
        sp_tree.append(
            _shape_xml(
                next_id,
                "PPT Master Footer Text",
                margin_x,
                footer_y,
                int(width_emu * 0.45),
                footer_h,
                _footer_text_body(footer_text, footer_color, body_font, footer_size),
            )
        )
        next_id += 1

    sp_tree.append(
        _shape_xml(
            next_id,
            "PPT Master Slide Number",
            max(0, width_emu - margin_x - 700000),
            footer_y,
            700000,
            footer_h,
            _slide_number_body(footer_color, body_font, footer_size),
        )
    )

    tree.write(master_path, encoding="UTF-8", xml_declaration=True)
    _clean_slide_layouts(extract_dir, width_emu, height_emu, design_tokens)
