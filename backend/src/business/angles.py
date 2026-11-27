from math import cos, sin, tau


def cycle(value, period):
    radians = tau * value / period
    return sin(radians), cos(radians)


def signed_delta(origin, destination):
    return (destination - origin + 180) % 360 - 180


def features(point, periodic):
    if periodic:
        return (*cycle(point.minute, 1440), *cycle(point.azimuth, 360), point.pitch)
    return point.minute, point.azimuth, point.pitch


def display_azimuth(angle):
    return round(angle % 360, 3) % 360


def clock_label(minute):
    hours, minutes = divmod(minute, 60)
    return f"{hours:02d}:{minutes:02d}"
