"""
OrangeHRM Integration Service — pushes valid candidates to OrangeHRM recruitment module.
Uses the OrangeHRM REST API (v2) with cookie/session-based auth.
Reads configuration from environment variables.
"""

import logging
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger("orangehrm")

ORANGEHRM_BASE = settings.ORANGEHRM_BASE_URL
ORANGEHRM_API = f"{ORANGEHRM_BASE}/web/index.php/api/v2"
ORANGEHRM_USER = settings.ORANGEHRM_USERNAME
ORANGEHRM_PASS = settings.ORANGEHRM_PASSWORD


async def _get_session() -> Optional[httpx.AsyncClient]:
    """Login to OrangeHRM and return an authenticated client with cookies."""
    try:
        client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        # Get login page to get CSRF token
        login_page = await client.get(f"{ORANGEHRM_BASE}/web/index.php/auth/login")
        
        # Extract CSRF token from cookies or page
        cookies = dict(client.cookies)
        
        # Post login credentials
        login_resp = await client.post(
            f"{ORANGEHRM_BASE}/web/index.php/auth/validate",
            data={
                "_token": cookies.get("_token", ""),
                "username": ORANGEHRM_USER,
                "password": ORANGEHRM_PASS,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        if login_resp.status_code in (200, 302):
            logger.info("OrangeHRM login successful")
            return client
        else:
            logger.warning(f"OrangeHRM login failed: {login_resp.status_code}")
            await client.aclose()
            return None
    except Exception as e:
        logger.error(f"OrangeHRM connection failed: {e}")
        return None


async def push_candidate_to_orangehrm(candidate_data: dict[str, Any]) -> dict[str, Any]:
    """
    Push a validated candidate to OrangeHRM as a recruitment candidate.
    Returns status of the push operation.
    """
    result = {
        "pushed": False,
        "orangehrm_id": None,
        "message": "",
    }

    client = await _get_session()
    if not client:
        result["message"] = "Failed to connect to OrangeHRM"
        return result

    try:
        # Try to create candidate via OrangeHRM API
        full_name = candidate_data.get("full_name", "Unknown")
        name_parts = full_name.split()
        
        candidate_payload = {
            "firstName": candidate_data.get("first_name", name_parts[0] if name_parts else "Unknown"),
            "middleName": "",
            "lastName": candidate_data.get("last_name", name_parts[-1] if len(name_parts) > 1 else ""),
            "email": candidate_data.get("email", ""),
            "contactNumber": candidate_data.get("phone", "") or candidate_data.get("mobile_number", ""),
            "keywords": ", ".join(candidate_data.get("skills", [])[:10]),
            "comment": f"Auto-imported from HireAI. ATS Score: {candidate_data.get('ats_score', 'N/A')}",
            "consentToKeepData": True,
        }

        resp = await client.post(
            f"{ORANGEHRM_API}/recruitment/candidates",
            json=candidate_payload,
            headers={"Accept": "application/json"},
        )

        if resp.status_code in (200, 201):
            data = resp.json()
            result["pushed"] = True
            result["orangehrm_id"] = data.get("data", {}).get("id")
            result["message"] = "Candidate pushed to OrangeHRM successfully"
            logger.info(f"Pushed {candidate_data.get('full_name')} to OrangeHRM")
        else:
            result["message"] = f"OrangeHRM API returned {resp.status_code}: {resp.text[:200]}"
            logger.warning(result["message"])
    except Exception as e:
        result["message"] = f"OrangeHRM push failed: {str(e)}"
        logger.error(result["message"])
    finally:
        await client.aclose()

    return result


async def sync_all_candidates_to_orangehrm(candidates: list[dict]) -> dict[str, Any]:
    """Batch sync multiple candidates to OrangeHRM."""
    results = {"pushed": 0, "failed": 0, "skipped": 0, "details": []}

    for c in candidates:
        # Skip flagged candidates
        if c.get("is_flagged") or c.get("fraud_score", 0) >= 60:
            results["skipped"] += 1
            results["details"].append({"name": c.get("full_name"), "status": "skipped_flagged"})
            continue

        # Skip invalid names
        name = c.get("full_name", "")
        if not name or name in ("Unknown", "null", "undefined") or len(name) < 2:
            results["skipped"] += 1
            results["details"].append({"name": name, "status": "skipped_invalid_name"})
            continue

        push_result = await push_candidate_to_orangehrm(c)
        if push_result["pushed"]:
            results["pushed"] += 1
        else:
            results["failed"] += 1
        results["details"].append({
            "name": c.get("full_name"),
            "status": "pushed" if push_result["pushed"] else "failed",
            "message": push_result["message"],
        })

    return results
