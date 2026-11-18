"""A/B test significance: two-proportion z-test, confidence interval, sample size."""
import math


def _phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def _z_inv(p):
    """Inverse normal CDF by bisection (no scipy needed)."""
    lo, hi = -10.0, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if _phi(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def z_test(conv_a, n_a, conv_b, n_b, alpha=0.05):
    if min(n_a, n_b) <= 0 or conv_a > n_a or conv_b > n_b:
        raise ValueError("invalid counts")
    pa, pb = conv_a / n_a, conv_b / n_b
    pool = (conv_a + conv_b) / (n_a + n_b)
    se = math.sqrt(pool * (1 - pool) * (1 / n_a + 1 / n_b))
    z = (pb - pa) / se if se else 0.0
    p = 2 * (1 - _phi(abs(z)))
    se_d = math.sqrt(pa * (1 - pa) / n_a + pb * (1 - pb) / n_b)
    zc = _z_inv(1 - alpha / 2)
    d = pb - pa
    return {"rate_a": pa, "rate_b": pb, "lift": (d / pa if pa else None), "z": z, "p_value": p,
            "ci_diff": (d - zc * se_d, d + zc * se_d), "significant": p < alpha}


def sample_size(base_rate, mde_rel, alpha=0.05, power=0.8):
    """Per-variant n to detect a relative lift `mde_rel` over `base_rate`."""
    p1, p2 = base_rate, base_rate * (1 + mde_rel)
    za, zb = _z_inv(1 - alpha / 2), _z_inv(power)
    pbar = (p1 + p2) / 2
    num = (za * math.sqrt(2 * pbar * (1 - pbar)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return math.ceil(num / (p2 - p1) ** 2)
