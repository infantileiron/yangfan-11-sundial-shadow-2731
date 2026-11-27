from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .angles import features, signed_delta


def fit(calibration, holdout, periodic):
    model = make_pipeline(StandardScaler(), Ridge(alpha=0.35))
    targets = [signed_delta(point.azimuth, point.reference) for point in calibration]
    holdout_targets = [signed_delta(point.azimuth, point.reference) for point in holdout]
    if max(map(abs, targets + holdout_targets)) > 25:
        raise ValueError("参考角与刻度角偏离超过 25°，请核对灯臂及测角仪坐标口径。")
    model.fit([features(point, periodic) for point in calibration], targets)
    predictions = model.predict([features(point, periodic) for point in holdout])
    return model, float(mean_absolute_error(holdout_targets, predictions))
