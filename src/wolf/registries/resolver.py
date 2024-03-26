import typing as t
from plum import Signature


class SignatureResolver:
    def __init__(
        self,
        signatures: t.Iterable[Signature] | None = None,
        restrict: t.Iterable[Signature] | None = None,
    ):
        self.signatures: t.Set[Signature] = signatures and set(signatures) or set()
        self.is_faithful: bool = True
        self.restrict: t.Set[Signature] = restrict and set(restrict) or set()

    def set_restrictions(self, *signatures):
        self.restrict |= set(signatures)

    def register(self, signature: Signature) -> None:
        existing = [s == signature for s in self.signatures]
        if any(existing):
            raise AssertionError(f"This exact signature already exists : {signature}.")
        else:
            self.signatures.add(signature)

        # Use a double negation for slightly better performance.
        self.is_faithful = not any(not s.is_faithful for s in self.signatures)

    def __len__(self) -> int:
        return len(self.signatures)

    def resolve(self, target: t.Tuple[object, ...] | Signature) -> Signature:
        if isinstance(target, tuple):

            def check(s):
                return s.match(target)

        else:

            def check(s):
                return target <= s

        candidates = []
        for signature in [s for s in self.signatures if check(s)]:
            # If none of the candidates are comparable,
            # then add the method as a new candidate and continue.
            if not any(c.is_comparable(signature) for c in candidates):
                candidates += [signature]
                continue

            # The signature under consideration is comparable
            # with at least one of the candidates.
            # First, filter any strictly more general candidates.
            new_candidates = [c for c in candidates if not signature < c]

            # If the signature under consideration is as specific
            # as at least one candidate, then and only then add
            # it as a candidate.
            if any(signature <= c for c in candidates):
                candidates = new_candidates + [signature]
            else:
                candidates = new_candidates

        if len(candidates) == 0:
            # There is no matching signature.
            raise LookupError(target, self.signatures)

        elif len(candidates) == 1:
            # There is exactly one matching signature. Success!
            return candidates[0]
        else:
            # There are multiple matching signatures.
            # Before raising an exception, attempt to resolve
            # the ambiguity using the precedence of the signatures.
            precedences = [c.precedence for c in candidates]
            max_precendence = max(precedences)
            if sum([p == max_precendence for p in precedences]) == 1:
                return candidates[precedences.index(max_precendence)]
            else:
                # Could not resolve the ambiguity, so error.
                raise LookupError(target, candidates)
