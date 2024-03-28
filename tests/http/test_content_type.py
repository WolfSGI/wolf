from wolf.http.datastructures import ContentType


def test_content_type():

    header = (
        '''Message/Partial; number=2; total=3; '''
        '''id="oc=jpbe0M2Yt4s@thumper.bellcore.com";'''
    )

    ct = ContentType.from_string(header)
    assert ct.mimetype == "Message/Partial"
    assert ct.options == {
        'number': '2',
        'total': '3',
        'id': 'oc=jpbe0M2Yt4s@thumper.bellcore.com'
    }

    ct = ContentType.from_string('')
    assert ct.mimetype == ""
    assert ct.options == {}
