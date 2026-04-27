#!/usr/bin/env python3
"""
Gestor de Calendario - Facultad de Ciencias Biológicas
=======================================================
Instrucciones:
  1. Coloca este script en la misma carpeta que tu archivo .ics
  2. Ejecuta: python3 gestionar_calendario.py   (Mac)
              python gestionar_calendario.py    (Windows)
  3. Usa el menú para agregar, editar o eliminar eventos
  4. Al guardar, sube el archivo .ics actualizado a GitHub

IMPORTANTE: Este script solo edita el calendario de tu unidad.
"""

import os
import uuid
from datetime import datetime

# ─────────────────────────────────────────────────────────────
#  CONFIGURACIÓN — Edita esta sección con tus datos
# ─────────────────────────────────────────────────────────────

# Nombre del archivo .ics que editarás (debe estar en la misma carpeta)
ARCHIVO_ICS = "decanatura.ics"   # <-- CAMBIA ESTO según tu unidad

# Nombre y correo que aparecerá como organizador en los eventos
ORGANIZADOR_NOMBRE = "Decanatura FCB"        # <-- CAMBIA ESTO
ORGANIZADOR_EMAIL  = "decanatura@fcb.cl"     # <-- CAMBIA ESTO

ZONA_HORARIA = "America/Santiago"

# ─────────────────────────────────────────────────────────────


def leer_eventos(archivo: str) -> list:
    if not os.path.exists(archivo):
        print(f"\n⚠  No se encontró '{archivo}'. Se creará uno nuevo al guardar.")
        return []

    with open(archivo, "r", encoding="utf-8") as f:
        contenido = f.read()

    eventos = []
    for bloque in contenido.split("BEGIN:VEVENT")[1:]:
        bloque = bloque.split("END:VEVENT")[0].strip()
        ev = {}
        for linea in bloque.splitlines():
            if   linea.startswith("UID:"):        ev["uid"]         = linea[4:]
            elif linea.startswith("SUMMARY:"):    ev["summary"]     = linea[8:]
            elif linea.startswith("DESCRIPTION:"): ev["description"] = linea[12:].replace("\\n", "\n")
            elif linea.startswith("LOCATION:"):   ev["location"]    = linea[9:]
            elif linea.startswith("CATEGORIES:"): ev["categories"]  = linea[11:]
            elif "DTSTART" in linea:
                ev["dtstart_raw"] = linea
                try:    ev["dtstart"] = datetime.strptime(linea.split(":")[1], "%Y%m%dT%H%M%S")
                except: ev["dtstart"] = None
            elif "DTEND" in linea:
                ev["dtend_raw"] = linea
                try:    ev["dtend"] = datetime.strptime(linea.split(":")[1], "%Y%m%dT%H%M%S")
                except: ev["dtend"] = None
        if ev:
            eventos.append(ev)
    return eventos


def generar_ics(eventos: list, nombre_calendario: str) -> str:
    ahora = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    cabecera = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Facultad de Ciencias Biológicas//{nombre_calendario}//ES
X-WR-CALNAME:{nombre_calendario}
X-WR-CALDESC:Calendario de {nombre_calendario} - Facultad de Ciencias Biológicas
X-WR-TIMEZONE:{ZONA_HORARIA}
CALSCALE:GREGORIAN
METHOD:PUBLISH
REFRESH-INTERVAL;VALUE=DURATION:PT1H
X-PUBLISHED-TTL:PT1H

BEGIN:VTIMEZONE
TZID:{ZONA_HORARIA}
BEGIN:STANDARD
TZOFFSETFROM:-0300
TZOFFSETTO:-0400
TZNAME:CLT
DTSTART:19700405T000000
RRULE:FREQ=YEARLY;BYDAY=1SU;BYMONTH=4
END:STANDARD
BEGIN:DAYLIGHT
TZOFFSETFROM:-0400
TZOFFSETTO:-0300
TZNAME:CLST
DTSTART:19701011T000000
RRULE:FREQ=YEARLY;BYDAY=2SU;BYMONTH=10
END:DAYLIGHT
END:VTIMEZONE"""

    bloques = []
    for ev in eventos:
        uid         = ev.get("uid") or f"fcb-{uuid.uuid4()}@facultad.cl"
        summary     = ev.get("summary", "(sin título)")
        descripcion = ev.get("description", "").replace("\n", "\\n")
        categoria   = ev.get("categories", nombre_calendario.upper())
        location    = f"LOCATION:{ev['location']}\n" if ev.get("location") else ""
        dtstart     = ev.get("dtstart_raw") or f"DTSTART;TZID={ZONA_HORARIA}:{ev['dtstart'].strftime('%Y%m%dT%H%M%S')}"
        dtend       = ev.get("dtend_raw")   or f"DTEND;TZID={ZONA_HORARIA}:{ev['dtend'].strftime('%Y%m%dT%H%M%S')}"

        bloques.append(f"""BEGIN:VEVENT
UID:{uid}
SUMMARY:{summary}
DESCRIPTION:{descripcion}
{dtstart}
{dtend}
CATEGORIES:{categoria}
STATUS:CONFIRMED
{location}ORGANIZER;CN={ORGANIZADOR_NOMBRE}:mailto:{ORGANIZADOR_EMAIL}
LAST-MODIFIED:{ahora}
DTSTAMP:{ahora}
END:VEVENT""")

    return cabecera + "\n\n" + "\n\n".join(bloques) + "\n\nEND:VCALENDAR\n"


def pedir_fecha_hora(etiqueta: str) -> datetime:
    while True:
        try:
            fecha = input(f"  {etiqueta} — Fecha (DD/MM/AAAA): ").strip()
            hora  = input(f"  {etiqueta} — Hora  (HH:MM, 24h): ").strip()
            return datetime.strptime(f"{fecha} {hora}", "%d/%m/%Y %H:%M")
        except ValueError:
            print("  ⚠  Formato inválido. Ejemplo: 15/06/2026  09:00")


def listar(eventos: list):
    if not eventos:
        print("\n  (El calendario está vacío)")
        return
    print("\n── EVENTOS ─────────────────────────────────────────")
    for i, ev in enumerate(eventos, 1):
        fecha = ev["dtstart"].strftime("%d/%m/%Y %H:%M") if ev.get("dtstart") else "?"
        print(f"  {i:>2}. {fecha}  │  {ev.get('summary','')}")
    print()


def agregar(eventos: list):
    print("\n── AGREGAR EVENTO ───────────────────────────────────")
    titulo      = input("  Título del evento: ").strip()
    descripcion = input("  Descripción (opcional): ").strip()
    lugar       = input("  Lugar (opcional): ").strip()
    dtstart     = pedir_fecha_hora("Inicio")
    dtend       = pedir_fecha_hora("Término")

    eventos.append({
        "uid":         f"fcb-{uuid.uuid4()}@facultad.cl",
        "summary":     titulo,
        "description": descripcion,
        "location":    lugar,
        "dtstart":     dtstart,
        "dtend":       dtend,
        "dtstart_raw": f"DTSTART;TZID={ZONA_HORARIA}:{dtstart.strftime('%Y%m%dT%H%M%S')}",
        "dtend_raw":   f"DTEND;TZID={ZONA_HORARIA}:{dtend.strftime('%Y%m%dT%H%M%S')}",
        "categories":  ORGANIZADOR_NOMBRE.upper(),
    })
    print(f"  ✅ Evento '{titulo}' agregado.")


def editar(eventos: list):
    listar(eventos)
    if not eventos:
        return
    try:
        ev = eventos[int(input("  Número de evento a editar: ")) - 1]
    except (ValueError, IndexError):
        print("  ⚠  Número inválido."); return

    print(f"\n  Editando: {ev['summary']}")
    print("  (Deja en blanco para mantener el valor actual)\n")

    t = input(f"  Título [{ev['summary']}]: ").strip()
    if t: ev["summary"] = t

    d = input(f"  Descripción [{ev.get('description','')[:40]}]: ").strip()
    if d: ev["description"] = d

    l = input(f"  Lugar [{ev.get('location','')}]: ").strip()
    if l: ev["location"] = l

    if input("  ¿Cambiar fecha/hora? (s/n): ").strip().lower() == "s":
        ev["dtstart"] = pedir_fecha_hora("Nuevo inicio")
        ev["dtend"]   = pedir_fecha_hora("Nuevo término")
        ev["dtstart_raw"] = f"DTSTART;TZID={ZONA_HORARIA}:{ev['dtstart'].strftime('%Y%m%dT%H%M%S')}"
        ev["dtend_raw"]   = f"DTEND;TZID={ZONA_HORARIA}:{ev['dtend'].strftime('%Y%m%dT%H%M%S')}"

    print("  ✅ Evento actualizado.")


def eliminar(eventos: list):
    listar(eventos)
    if not eventos:
        return
    try:
        idx = int(input("  Número de evento a eliminar: ")) - 1
        ev  = eventos[idx]
    except (ValueError, IndexError):
        print("  ⚠  Número inválido."); return

    if input(f"  ¿Eliminar '{ev['summary']}'? (s/n): ").strip().lower() == "s":
        eventos.pop(idx)
        print("  ✅ Evento eliminado.")
    else:
        print("  Cancelado.")


def guardar(eventos: list):
    nombre_cal = ORGANIZADOR_NOMBRE
    contenido  = generar_ics(eventos, nombre_cal)
    with open(ARCHIVO_ICS, "w", encoding="utf-8") as f:
        f.write(contenido)
    print(f"\n✅ Guardado: '{ARCHIVO_ICS}'  ({len(eventos)} eventos)")
    print("   → Sube este archivo a GitHub para que los cambios")
    print("     se reflejen automáticamente en todos los calendarios.\n")


def main():
    print("=" * 52)
    print(f"  Calendario — {ORGANIZADOR_NOMBRE}")
    print("=" * 52)

    eventos = leer_eventos(ARCHIVO_ICS)
    print(f"  Archivo: {ARCHIVO_ICS}  ({len(eventos)} eventos cargados)")

    while True:
        print("\n─── MENÚ ────────────────────────────────────────")
        print("  1. Ver eventos")
        print("  2. Agregar evento")
        print("  3. Editar evento")
        print("  4. Eliminar evento")
        print("  5. Guardar y salir")
        print("  6. Salir sin guardar")

        op = input("\nOpción: ").strip()
        if   op == "1": listar(eventos)
        elif op == "2": agregar(eventos)
        elif op == "3": editar(eventos)
        elif op == "4": eliminar(eventos)
        elif op == "5": guardar(eventos); break
        elif op == "6": print("\n  Saliendo sin guardar.\n"); break
        else:           print("  ⚠  Opción inválida.")


if __name__ == "__main__":
    main()
