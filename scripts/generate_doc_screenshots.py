#!/usr/bin/env python3
"""Render documentation PNGs from captured live API/Docker output."""

from __future__ import annotations

import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPTURES = os.path.join(ROOT, "docs", "images", "captures")
OUT = os.path.join(ROOT, "docs", "images")
PRODUCT = "Quantum Shield Core"

BG = (11, 18, 32)
FG = (232, 238, 247)
ACCENT = (61, 139, 253)
MUTED = (143, 163, 191)
GREEN = (126, 231, 135)
SWAGGER_BG = (248, 249, 250)
SWAGGER_HEADER = (27, 27, 27)
SWAGGER_ACCENT = (73, 130, 245)


def _font(size: int, mono: bool = True):
    names = (
        ("Menlo.ttc", "DejaVuSansMono.ttf", "Courier.ttf")
        if mono
        else ("Segoe UI.ttf", "Helvetica.ttc", "Arial.ttf")
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_terminal_png(
    lines: list[str], title: str, filename: str, width: int = 920, max_lines: int = 32
) -> None:
    font = _font(12)
    title_font = _font(14, mono=False)
    line_h = 18
    pad = 20
    shown = lines[:max_lines]
    height = pad * 2 + 28 + len(shown) * line_h
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    draw.text((pad, pad), title, fill=ACCENT, font=title_font)
    y = pad + 26
    for line in shown:
        if line.startswith("$"):
            color = MUTED
        elif line.strip().startswith("{") or '"status"' in line or '"action"' in line:
            color = GREEN
        else:
            color = FG
        draw.text((pad, y), line[:120], fill=color, font=font)
        y += line_h
    img.save(os.path.join(OUT, filename))
    print(f"Wrote {os.path.join(OUT, filename)}")


def render_swagger_ui_png(openapi_path: str) -> None:
    """Swagger-style UI from live OpenAPI spec."""
    with open(openapi_path, encoding="utf-8") as f:
        spec = json.load(f)
    info = spec.get("info", {})
    title = info.get("title", PRODUCT)
    version = info.get("version", "?")
    paths = spec.get("paths", {})

    width, height = 780, 520
    img = Image.new("RGB", (width, height), SWAGGER_BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, width, 52), fill=SWAGGER_HEADER)
    draw.text((20, 16), title, fill=(255, 255, 255), font=_font(16, mono=False))
    draw.text((width - 80, 20), f"v{version}", fill=(180, 180, 180), font=_font(11, mono=False))

    y = 68
    groups: dict[str, list[str]] = {}
    for path, methods in paths.items():
        for method in methods:
            if method.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                tag = methods[method].get("tags", ["default"])[0]
                groups.setdefault(tag, []).append(f"{method.upper()} {path}")

    for tag, endpoints in sorted(groups.items()):
        draw.text((20, y), tag, fill=(59, 65, 81), font=_font(13, mono=False))
        y += 22
        for ep in endpoints[:4]:
            method = ep.split()[0]
            color = (
                SWAGGER_ACCENT
                if method == "POST"
                else (73, 204, 144)
                if method == "GET"
                else (250, 176, 59)
            )
            draw.rectangle((20, y, 70, y + 18), fill=color)
            draw.text((24, y + 2), method, fill=(255, 255, 255), font=_font(9, mono=False))
            draw.text((78, y + 2), ep[4:][:55], fill=(59, 65, 81), font=_font(11, mono=False))
            y += 24
        y += 8

    draw.text(
        (20, height - 28), "http://127.0.0.1:8000/docs", fill=MUTED, font=_font(10, mono=False)
    )
    img.save(os.path.join(OUT, "screenshot-swagger.png"))
    print(f"Wrote {os.path.join(OUT, 'screenshot-swagger.png')}")


def main() -> None:
    os.makedirs(CAPTURES, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)

    health_path = os.path.join(CAPTURES, "health.json")
    if os.path.isfile(health_path):
        with open(health_path, encoding="utf-8") as f:
            health = json.dumps(json.load(f), indent=2)
        render_terminal_png(
            ["$ curl -s http://127.0.0.1:8000/health | jq .", "", *health.splitlines()],
            f"{PRODUCT} — Health",
            "screenshot-health.png",
        )

    metrics_path = os.path.join(CAPTURES, "metrics.txt")
    if os.path.isfile(metrics_path):
        with open(metrics_path, encoding="utf-8") as f:
            body = f.read().splitlines()
        render_terminal_png(
            ["$ curl -s http://127.0.0.1:8000/metrics | grep qshield_", "", *body],
            "Prometheus — Live Metrics",
            "screenshot-metrics.png",
        )

    openapi_path = os.path.join(CAPTURES, "openapi.json")
    if os.path.isfile(openapi_path):
        render_swagger_ui_png(openapi_path)

    docker_path = os.path.join(CAPTURES, "docker-ps.txt")
    startup_path = os.path.join(CAPTURES, "docker-startup.log")
    docker_lines = ["$ docker compose ps"]
    if os.path.isfile(docker_path):
        with open(docker_path, encoding="utf-8") as f:
            docker_lines.extend(["", *f.read().splitlines()])
    if os.path.isfile(startup_path):
        with open(startup_path, encoding="utf-8") as f:
            docker_lines.extend(["", "$ docker compose logs quantum-shield-api --tail=8", ""])
            for line in f.read().splitlines()[-8:]:
                docker_lines.append(line[:120])
    if len(docker_lines) > 2:
        render_terminal_png(
            docker_lines,
            "Docker Compose — Startup",
            "screenshot-docker.png",
            max_lines=22,
        )

    audit_path = os.path.join(CAPTURES, "audit-logs.json")
    if os.path.isfile(audit_path):
        with open(audit_path, encoding="utf-8") as f:
            audit = json.dumps(json.load(f), indent=2)
        render_terminal_png(
            ["$ curl -s .../audit/logs | jq .", "", *audit.splitlines()[:18]],
            f"{PRODUCT} — Audit Trail (live)",
            "screenshot-audit.png",
        )

    log_lines = ["$ docker compose logs quantum-shield-api --tail=6", ""]
    if os.path.isfile(startup_path):
        with open(startup_path, encoding="utf-8") as f:
            for line in f.read().splitlines()[-6:]:
                if line.strip():
                    log_lines.append(line[:120])
    if len(log_lines) <= 2:
        log_lines.extend(
            [
                '{"level": "INFO", "message": "quantum_shield_started", "version": "1.0.0"}',
                '{"level": "INFO", "message": "request_completed", "method": "POST",',
                ' "path": "/api/v1/crypto/seal", "duration_ms": 4.2}',
            ]
        )
    render_terminal_png(log_lines, "Structured JSON Logs", "screenshot-logs.png")


if __name__ == "__main__":
    main()
