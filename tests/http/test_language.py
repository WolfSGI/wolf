from wolf.http.datastructures import Language


def test_language():
    lang = Language('en-EN;q=0.5')
    assert lang.locale == "en-EN"
    assert lang == "en-EN"
    assert lang.options == {"q": "0.5"}