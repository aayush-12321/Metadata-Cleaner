"""
Metadata analysis: filter technical fields, classify sensitivity, and
produce before/after diffs for the preview UI.
"""

import logging
from flask import current_app

logger = logging.getLogger(__name__)

# Categories shown in the UI grouped summary
CATEGORY_MAP = {
    "GPS": ["GPSLatitude", "GPSLongitude", "GPSAltitude", "GPSPosition",
            "GPSLatitudeRef", "GPSLongitudeRef", "GPSTimeStamp", "GPSDateStamp",
            "GPSStatus", "GPSMeasureMode", "GPSDOP", "GPSSpeed", "GPSTrack",
            "GPSImgDirection", "GPSDestBearing", "GPSHPositioningError"],
    "Author / Identity": ["Author", "Creator", "Artist", "OwnerName", "By-line",
                          "XPAuthor", "LastModifiedBy", "Manager", "Company"],
    "Device": ["Make", "Model", "SerialNumber", "CameraSerialNumber",
               "LensSerialNumber", "InternalSerialNumber", "LensID",
               "LensModel", "LensMake"],
    "Software": ["Software", "ProcessingSoftware", "CreatorTool", "HistorySoftwareAgent"],
    "Dates": ["CreateDate", "DateTimeOriginal", "ModifyDate", "MetadataDate",
              "DigitizedDate", "DateCreated", "TimeCreated"],
    "Comments": ["Comment", "UserComment", "XPComment", "Description",
                 "ImageDescription", "Caption-Abstract", "SpecialInstructions"],
    "Copyright": ["Copyright", "CopyrightNotice", "Rights", "UsageTerms",
                  "WebStatement"],
    "Other": [],
}

_REVERSE_CATEGORY = {
    field: cat for cat, fields in CATEGORY_MAP.items() for field in fields
}


def filter_metadata(raw: dict) -> dict:
    """
    Remove purely technical fields that add noise but carry no privacy risk.
    Returns the filtered dict.
    """
    excluded = current_app.config["EXCLUDED_METADATA_FIELDS"]
    return {k: v for k, v in raw.items() if k not in excluded}


def categorize_metadata(filtered: dict) -> dict[str, dict]:
    """
    Group metadata fields into human-readable categories.

    Returns:
        Dict of {category_name: {field: value, ...}}
    """
    result: dict[str, dict] = {cat: {} for cat in CATEGORY_MAP}

    for field, value in filtered.items():
        cat = _REVERSE_CATEGORY.get(field, "Other")
        result[cat][field] = value

    # Drop empty categories
    return {k: v for k, v in result.items() if v}


def compute_risk(filtered: dict) -> dict:
    """
    Assign a risk level to a metadata set.

    Returns:
        {"level": "high"|"medium"|"low", "score": int, "reasons": [str]}
    """
    high_fields = current_app.config["HIGH_SENSITIVITY_FIELDS"]
    hits = [f for f in filtered if f in high_fields]

    gps_present = any(f.startswith("GPS") for f in filtered)
    score = len(hits) + (5 if gps_present else 0)

    reasons = []
    if gps_present:
        reasons.append("GPS location data detected")
    for f in hits:
        if not f.startswith("GPS"):
            reasons.append(f"Personal field: {f}")

    if score >= 6:
        level = "high"
    elif score >= 2:
        level = "medium"
    else:
        level = "low"

    return {"level": level, "score": score, "reasons": reasons[:5]}


def build_diff(before: dict, after: dict) -> list[dict]:
    """
    Produce a list of changed/removed fields between two metadata snapshots.

    Returns:
        List of {"field": str, "before": str, "after": str|None, "status": "removed"|"changed"|"kept"}
    """
    all_fields = set(before) | set(after)
    diff = []

    for field in sorted(all_fields):
        b_val = str(before.get(field, "")) if field in before else None
        a_val = str(after.get(field, "")) if field in after else None

        if b_val is not None and a_val is None:
            status = "removed"
        elif b_val != a_val:
            status = "changed"
        else:
            status = "kept"

        diff.append({"field": field, "before": b_val, "after": a_val, "status": status})

    return diff
