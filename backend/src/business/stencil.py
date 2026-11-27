from .angles import clock_label, display_azimuth


def correction_row(point, correction, tolerance):
    corrected = point.azimuth + correction
    return {
        "sample_id": point.sample_id,
        "clock": clock_label(point.minute),
        "original_deg": display_azimuth(point.azimuth),
        "corrected_deg": display_azimuth(corrected),
        "correction_deg": round(float(correction), 3),
        "crosses_north": bool(not 0 <= corrected < 360),
        "decision": "转台返校" if abs(correction) >= tolerance else "按角放样",
    }


def workshop_stencil(rows):
    stencil = sorted(rows, key=lambda row: (row["clock"], row["sample_id"]))
    return {
        "layout": [row for row in stencil if row["decision"] == "按角放样"],
        "recheck": [row for row in stencil if row["decision"] == "转台返校"],
        "north_crossings": [row["sample_id"] for row in stencil if row["crosses_north"]],
        "angle_unit": "degree_clockwise_from_north",
    }
