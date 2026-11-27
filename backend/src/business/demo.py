from math import cos, sin, tau
from random import Random


def demo_rows():
    rng = Random(52111)
    rows = []
    for split, prefix, points in (("标定", "C", 120), ("留出", "H", 48)):
        for index in range(points):
            minute = (index * 1440 // points + rng.randrange(1440 // points)) % 1440
            azimuth = round(rng.randrange(36000) / 100, 2)
            pitch = rng.choice([-4, -2, 0, 2, 4])
            delta = (
                -1.6 + 2.9 * cos(tau * minute / 1440) + 1.1 * sin(tau * minute / 1440)
                + 1.5 * sin(tau * azimuth / 360) + 0.25 * pitch + rng.gauss(0, 0.09)
            )
            reference = round((azimuth + delta) % 360, 3) % 360
            rows.append(sample(f"YC-{prefix}{index + 1:03}", split, minute, azimuth, pitch, reference))
    pending = [
        (1439, 359.8, 0),
        (1, 359.8, 0),
        (720, 180, -4),
        (360, 85, 2),
        (1010, 245, 1),
        (1110, 268, -1),
    ]
    for index, (minute, azimuth, pitch) in enumerate(pending, 1):
        rows.append(sample(f"YC-P{index:02}", "待放样", minute, azimuth, pitch, None))
    return rows


def sample(sample_id, split, minute, azimuth, pitch, reference):
    return {
        "sample_id": sample_id, "split": split, "minute": minute, "azimuth_deg": azimuth,
        "pitch_deg": pitch, "reference_deg": reference,
    }
