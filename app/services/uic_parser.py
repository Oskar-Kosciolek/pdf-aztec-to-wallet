import re
from typing import Any

# PKP-specific diacritic encoding: bytes 0x01-0x09 = lowercase ą-ż, 0x0A-0x12 = uppercase Ą-Ż
_PKP_DIACRITICS: dict[int, str] = {
    0x01: "ą", 0x02: "ć", 0x03: "ę", 0x04: "ł", 0x05: "ń",
    0x06: "ó", 0x07: "ś", 0x08: "ź", 0x09: "ż",
    0x0A: "Ą", 0x0B: "Ć", 0x0C: "Ę", 0x0D: "Ł", 0x0E: "Ń",
    0x0F: "Ó", 0x10: "Ś", 0x11: "Ź", 0x12: "Ż",
}


def decode_pkp_text(data: bytes) -> str:
    return "".join(
        _PKP_DIACRITICS.get(b, chr(b) if 32 <= b <= 126 else " ")
        for b in data
    )


def parse_fields(decompressed: bytes) -> dict[str, Any]:
    # ascii_text: only printable ASCII preserved, control bytes (incl. PKP diacritics) → space
    # Used for all structure-dependent patterns so PKP diacritic bytes don't corrupt digit sequences
    ascii_text = "".join(chr(b) if 32 <= b <= 126 else " " for b in decompressed)
    fields: dict[str, Any] = {}

    # Times HH:MM — first = departure, second = arrival
    times = re.findall(r"\b(\d{2}:\d{2})\b", ascii_text)
    if times:
        fields["departure_time"] = times[0]
    if len(times) >= 2:
        fields["arrival_time"] = times[1]

    # Date DD.MM.YYYY
    dates = re.findall(r"\b(\d{2}\.\d{2}\.\d{4})\b", ascii_text)
    if dates:
        fields["date"] = dates[0]

    # Price: decimal not followed by another dot (to exclude dates like 30.12.2025)
    for m in re.finditer(r"(?<!\d)(\d{1,4}\.\d{2})(?!\d)(?!\.)", ascii_text):
        fields["price_pln"] = m.group(1)
        break

    # Station names: 8 zeros + 2-digit length + uppercase ASCII name
    # e.g. 0000000007BOCHNIA, 0000000009KRAKOW GL
    for m in re.finditer(r"0{8}(\d{2})([A-Z][A-Z ]+)", ascii_text):
        length = int(m.group(1))
        name = m.group(2)[:length].strip()
        if len(name) >= 3 and name.replace(" ", "").isalpha():
            if "from" not in fields:
                fields["from"] = name
            elif fields.get("from") != name and "to" not in fields:
                fields["to"] = name
                break

    # Seat: digits before OKNO or KORYTARZ
    seat_m = re.search(r"(\d+)\s*(OKNO|KORYTARZ)", ascii_text)
    if seat_m:
        fields["seat"] = f"{seat_m.group(1)} {seat_m.group(2)}"

    # Ticket type: locate "BILET" in ascii_text, decode raw bytes with PKP mapping
    bilet_start = ascii_text.find("BILET")
    if bilet_start != -1:
        end_m = re.search(r"\d{5}", ascii_text[bilet_start:])
        if end_m:
            bilet_end = bilet_start + end_m.start()
            fields["ticket_type"] = decode_pkp_text(decompressed[bilet_start:bilet_end]).strip()

    # Passenger name: locate 000433 marker in ascii_text, decode raw bytes with PKP mapping
    marker_m = re.search(r"000433\d{6}", ascii_text)
    if marker_m:
        name_start = marker_m.end()
        end_marker = ascii_text.find("000443", name_start)
        if end_marker != -1:
            fields["passenger"] = decode_pkp_text(decompressed[name_start:end_marker]).strip()

    return fields
