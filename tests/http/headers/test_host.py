from wolf.http.headers.utils import parse_host


def test_host():
    hostname, port = parse_host('www.google.com')
    assert (hostname, port) == ("www.google.com", None)
    hostname, port = parse_host('google.com:80')
    assert (hostname, port) == ("google.com", 80)
    hostname, port = parse_host('test.google.com:443')
    assert (hostname, port) == ("test.google.com", 443)


def test_ipv4_host():
    hostname, port = parse_host('127.0.0.1')
    assert (hostname, port) == ("127.0.0.1", None)
    hostname, port = parse_host('192.168.1.99:80')
    assert (hostname, port) == ("192.168.1.99", 80)
    hostname, port = parse_host('10.0.0.5:443')
    assert (hostname, port) == ("10.0.0.5", 443)


def test_ipv6_host():
    hostname, port = parse_host('[fe80::ca1f:eaff:fe69:2501]')
    assert (hostname, port) == ("[fe80::ca1f:eaff:fe69:2501]", None)
    hostname, port = parse_host('[2a01:8790:16d:0:218:de87:164:8745]:80')
    assert (hostname, port) == ("[2a01:8790:16d:0:218:de87:164:8745]", 80)
    hostname, port = parse_host('[::1]:5555')
    assert (hostname, port) == ("[::1]", 5555)
