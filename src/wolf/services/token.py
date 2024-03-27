import pathlib
import jwt
import logging
from beartype import beartype
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from aioinject import Object
from wolf.pluggability import Installable


logger = logging.getLogger(__name__)


class InvalidSignature(Exception):
    pass


class ExpiredToken(Exception):
    pass


class InvalidToken(Exception):
    pass


class JWTManager:
    
    def __init__(self, private_key: bytes, public_key: bytes):
        self.private_key = private_key
        self.public_key = public_key

    def get_token(self, data: dict, delta: int = 60) -> str:
        logger.info("Got jwt request for a new token.")
        expires = datetime.now(tz=timezone.utc) + timedelta(minutes=delta)
        data = {**data, "exp": expires}
        token = jwt.encode(data, self.private_key, algorithm="RS256")
        return token

    def verify_token(self, token: str) -> dict:
        try:
            decoded = jwt.decode(token, self.public_key, algorithms=["RS256"])
            return decoded
        except jwt.exceptions.InvalidSignatureError:
            raise InvalidSignature()
        except jwt.ExpiredSignatureError:
            raise ExpiredToken()
        except jwt.exceptions.InvalidTokenError:
            raise InvalidToken()


@beartype
@dataclass(kw_only=True)
class JWTService(Installable):
    private_key: pathlib.Path
    public_key: pathlib.Path

    def __post_init__(self):
        assert self.private_key.is_file()
        assert self.public_key.is_file()

    def install(self, application):
        with self.private_key.open("rb") as f:
            private_key_pem = f.read()

        with self.public_key.open("rb") as f:
            public_key_pem = f.read()

        manager = JWTManager(private_key_pem, public_key_pem)
        application.services.register(Object(manager, type_=JWTManager))
