from hashids import Hashids
from fastapi import HTTPException, status

hashids = Hashids(salt="your_salt_here", min_length=8)

def encode_id(id: int) -> str:
    return hashids.encode(id)

def decode_id(hashid: str) -> int | None:
    decoded = hashids.decode(hashid)
    return decoded[0] if decoded else None

def decode_id_or_404(hashid: str) -> int:
    """Decode a hashid path param; raise 404 if invalid."""
    decoded = hashids.decode(hashid)
    if not decoded:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return decoded[0]
