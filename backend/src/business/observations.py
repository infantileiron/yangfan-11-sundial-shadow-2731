from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class ShadowPoint:
    sample_id: str
    minute: int
    azimuth: float
    pitch: float
    reference: float | None


def split_observations(rows):
    groups = defaultdict(list)
    for row in rows:
        minute = row["minute"]
        azimuth = row["azimuth_deg"] % 360
        reference = row["reference_deg"]
        split = row["split"]
        if int(minute) != minute:
            raise ValueError(f"{row['sample_id']} 的模拟分钟须为整数。")
        if (reference is None) != (split == "待放样"):
            raise ValueError("标定与留出点必须提供参考角，待放样点必须留空。")
        groups[split].append(ShadowPoint(row["sample_id"], int(minute), azimuth, row["pitch_deg"], reference))
    calibration, holdout, candidates = (groups[name] for name in ("标定", "留出", "待放样"))
    if len(calibration) < 36 or len(holdout) < 12 or not candidates:
        raise ValueError("至少需要 36 个标定点、12 个留出点与 1 个待放样点。")
    for name, group in (("标定", calibration), ("留出", holdout)):
        if len({point.minute // 360 for point in group}) != 4:
            raise ValueError(f"{name}测次须覆盖全部四个模拟时段（每段 6 小时）。")
        if len({int(point.azimuth // 90) for point in group}) != 4:
            raise ValueError(f"{name}测次须覆盖全部四个方位象限。")
    return calibration, holdout, candidates
