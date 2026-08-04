import os
import httpx

TURNSTILE_SECRET = os.getenv("TURNSTILE_SECRET_KEY")


async def verify_turnstile(token: str, remote_ip: str | None = None) -> bool:
    """
    Verify a Cloudflare Turnstile token.
    """

    if not TURNSTILE_SECRET:
        # Don't block local development
        return True

    data = {
        "secret": TURNSTILE_SECRET,
        "response": token,
    }

    if remote_ip:
        data["remoteip"] = remote_ip

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data=data,
        )

    result = response.json()

    return result.get("success", False)