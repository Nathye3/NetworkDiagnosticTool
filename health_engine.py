def calculate_health_score(ping_ok, dns_ok, port_ok, packet_loss=0):
    score = 0

    if ping_ok:
        score += 30
    if dns_ok:
        score += 20
    if port_ok:
        score += 20

    if packet_loss < 1:
        score += 30
    elif packet_loss < 10:
        score += 15

    if score >= 80:
        status = "HEALTHY"
    elif score >= 50:
        status = "DEGRADED"
    else:
        status = "CRITICAL"

    return score, status
