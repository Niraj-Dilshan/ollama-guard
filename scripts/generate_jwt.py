import argparse
import time
import jwt

def generate_jwt(secret: str, aud: str = None, iss: str = None) -> str:
    """
    Generates a HS256 JWT.
    """
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,  # 1 hour expiration
    }
    if aud:
        payload["aud"] = aud
    if iss:
        payload["iss"] = iss
    
    return jwt.encode(payload, secret, algorithm="HS256")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a HS256 JWT.")
    parser.add_argument("--secret", required=True, help="The JWT secret.")
    parser.add_argument("--aud", help="The JWT audience.")
    parser.add_argument("--iss", help="The JWT issuer.")
    args = parser.parse_args()

    token = generate_jwt(args.secret, args.aud, args.iss)
    print(token)
