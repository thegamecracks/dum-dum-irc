import pytest

from dumdum.protocol import bytearray_reader, byte_reader


def test_bytearray_reader_commit_and_rollback():
    data = bytearray(b"Hello world!\n")

    with bytearray_reader(data) as reader:
        assert reader.read(5) == b"Hello"

    assert data == b" world!\n"

    with pytest.raises(RuntimeError), bytearray_reader(data) as reader:
        assert reader.read() == b" world!\n"
        raise RuntimeError

    assert data == b" world!\n"


def test_reader_out_of_bounds():
    with byte_reader(b"Hello world!\n") as reader:
        with pytest.raises(ValueError):
            reader.readexactly(-1)

        assert reader.read(1000) == b"Hello world!\n"

        reader.readexactly(0)

        with pytest.raises(IndexError):
            reader.readexactly(1)


def test_reader_varchar():
    with byte_reader(b"\x05Hello\x08 world!\n") as reader:
        assert reader.read_varchar(max_length=5) == "Hello"
        assert reader.read_varchar(max_length=8) == " world!\n"


def test_reader_closed():
    with byte_reader(b"Hello world!\n") as reader:
        pass

    with pytest.raises(RuntimeError):
        reader.read()

    with pytest.raises(RuntimeError):
        reader.readexactly(1)
