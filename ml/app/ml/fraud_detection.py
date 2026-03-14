def detect_fraud(claimed_experience, computed_experience):

    delta = claimed_experience - computed_experience
    
    if delta > 2:
        risk = "HIGH"
    elif delta > 1:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return {
        "risk": risk,
        "fraud_score": round(delta / 10, 2)
    }