import itsdangerous
import logging
from functools import wraps
from dataclasses import dataclass
from http_session.cookie import SameSite, HashAlgorithm, SignedCookieManager
from http_session import Store, Session
import svcs


logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class HTTPSession:
    store: Store
    secret: str
    samesite: SameSite = SameSite.lax
    httponly: bool = True
    digest: str = HashAlgorithm.sha1.name
    TTL: int = 3600
    cookie_name: str = "sid"
    secure: bool = True
    save_new_empty: bool = False
    salt: str | None = None
    domain: str | None = None

    def __post_init__(self):
        self.manager = SignedCookieManager(
            self.store,
            self.secret,
            salt=self.salt,
            digest=self.digest,
            TTL=self.TTL,
            cookie_name=self.cookie_name,
        )

    def __call__(self, handler):
        @wraps(handler)
        def http_session_middleware(request, *args, **kwargs):
            new = True
            if request.cookies:
                if sig := request.cookies.get(self.manager.cookie_name):
                    try:
                        sid = str(self.manager.verify_id(sig), "utf-8")
                    except itsdangerous.exc.SignatureExpired:
                        # Session expired. We generate a new one.
                        pass
                    except itsdangerous.exc.BadTimeSignature:
                        # Discrepancy in time signature.
                        # Invalid, generate a new one
                        pass
                    else:
                        new = False

            if new is True:
                sid = self.manager.generate_id()

            session: Session = self.manager.session_factory(
                sid, self.manager.store, new=new
            )
            request.context.register_local_value(Session, session)
            try:
                response = handler(request, *args, **kwargs)
            except Exception:
                # Maybe log.
                raise
            else:
                if not session.modified and (session.new and self.save_new_empty):
                    session.save()

                if session.modified:
                    if response.status < 400:
                        session.persist()

                elif session.new:
                    return response

                domain = self.domain or request.domain
                cookie = self.manager.cookie(
                    session.sid,
                    request.root_path or "/",
                    domain,
                    secure=self.secure,
                    samesite=self.samesite,
                    httponly=self.httponly,
                )
                response.cookies[self.manager.cookie_name] = cookie
                return response

        return http_session_middleware
