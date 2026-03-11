from wolf.pipeline import chain_wrap


def handler(value: str):
    return f"I got {value}"


def capitalize(wrapped):
    def capitalize_middleware(value: str):
        result: str = wrapped(value)
        return result.upper()
    return capitalize_middleware


def suffix(wrapped):
    def suffix_middleware(value: str):
        result = wrapped(value)
        return f"{result} my suffix"
    return suffix_middleware


def test_chained_pipeline():
    pipeline = chain_wrap((capitalize, suffix), handler)
    result = pipeline("42")
    assert result == 'I GOT 42 MY SUFFIX'
