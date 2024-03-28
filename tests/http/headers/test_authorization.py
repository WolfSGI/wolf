from wolf.http.headers import Authorization


def test_authorization_header():
    auth = Authorization.from_string('Token SomeTokenValue')
    assert auth == ('token', 'SomeTokenValue')

    auth = Authorization.from_string('  Token   SomeTokenValue')
    assert auth == ('token', 'SomeTokenValue')

    auth = Authorization.from_string('  Token   Some Token Value     ')
    assert auth == ('token', 'Some Token Value')
