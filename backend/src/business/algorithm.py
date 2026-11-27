from .angles import features
from .calibration import fit
from .observations import split_observations
from .stencil import correction_row


def analyze(rows, parameter):
    calibration, holdout, candidates = split_observations(rows)
    _, baseline_error = fit(calibration, holdout, periodic=False)
    model, periodic_error = fit(calibration, holdout, periodic=True)
    predictions = model.predict([features(point, periodic=True) for point in candidates])
    output = [correction_row(point, prediction, parameter) for point, prediction in zip(candidates, predictions)]
    output.sort(key=lambda row: (-abs(row["correction_deg"]), row["sample_id"]))
    rechecks = sum(row["decision"] == "转台返校" for row in output)
    return {
        "summary": f"{len(output)} 条待放样影线，{rechecks} 条返校。",
        "rows": output,
        "metrics": [
            {"label": "原始分钟与方位角留出 MAE（°）", "value": round(baseline_error, 4)},
            {"label": "周期特征留出 MAE（°）", "value": round(periodic_error, 4)},
            {"label": "跨正北待放样点", "value": sum(row["crosses_north"] for row in output)},
        ],
        "notes": [
            "模拟时钟对应馆内投影灯顺序，整圈标定使用人工光源。",
            "同一夹具的角度校订可复用。更换灯臂或基座后需重新标定。",
        ],
    }
