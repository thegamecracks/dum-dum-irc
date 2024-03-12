import pytest

from dumdum.protocol import InvalidLengthError, byte_reader, varchar


def test_loads_unicode():
    message = b"\x17foobar2000 hamspam \xf0\x9f\x91\x80"
    assert varchar.loads(message, max_length=23) == "foobar2000 hamspam 👀"


def test_loads_extra_data():
    message = b"\x05Hello world!\n"
    assert varchar.loads(message, max_length=5) == "Hello"
    assert varchar.loads(message, max_length=13) == "Hello"


def test_loads_exceeds_max_length():
    message = b"\x05Hello world!\n"
    with pytest.raises(InvalidLengthError):
        varchar.loads(message, max_length=3)


def test_loads_insufficient_data():
    message = b"\xffThis message is too short!"
    with pytest.raises(IndexError):
        varchar.loads(message, max_length=255)


def test_loads_insufficient_length():
    message = b"\x01"
    with pytest.raises(IndexError):
        varchar.loads(message, max_length=256)


def test_loads_empty_message():
    message = b""
    assert varchar.loads(message, max_length=0) == ""
    with pytest.raises(IndexError):
        varchar.loads(message, max_length=1)


def test_loads_multi_byte_length():
    message = b"\x01\xff" + b"x" * (256 + 255)
    assert varchar.loads(message, max_length=511) == "x" * 511
    assert varchar.loads(message, max_length=65535) == "x" * 511

    with pytest.raises(InvalidLengthError):
        expected_length = int.from_bytes(message[:3], byteorder="big")
        assert expected_length > 65536
        assert varchar.loads(message, max_length=65536)


def test_load():
    with byte_reader(b"\x17foobar2000 hamspam \xf0\x9f\x91\x80") as reader:
        assert varchar.load(reader, max_length=23) == "foobar2000 hamspam 👀"


def test_dumps_unicode():
    message = "foobar2000 hamspam 👀"
    expected = b"\x17foobar2000 hamspam \xf0\x9f\x91\x80"
    assert varchar.dumps(message, max_length=len(message.encode())) == expected

    with pytest.raises(InvalidLengthError):
        varchar.dumps(message, max_length=len(message))


def test_dumps_empty_message():
    for i in range(5):
        length = 2 ** (8 * i)
        assert varchar.dumps("", max_length=length) == b"\x00" * (i + 1)
