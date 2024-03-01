from enum import IntEnum


class ExitCode(IntEnum):
    """Exit codes as defined by BSD sysexits.h.

    Values are the same as the exit codes defined in sysexits.h.
    https://man.freebsd.org/cgi/man.cgi?query=sysexits

    Values:
        OK: Successful termination.
        ERR: Catchall for general errors.
        DATAERR: The input data was incorrect in some way. This should only be used
          for user's data and not system files.
        NOINPUT: An	input file (not	a system file) did  not	 exist or was not readable.
        NOHOST: The host specified did not exist.
        UNAVAILABLE: A service is unavailable. This can occur if a support program or
          file does not exist.
        SOFTWARE: An internal software error has been detected.
        IOERR: An error occurred while doing I/O on some file.
        TEMPFAIL: Temporary failure, indicating something that is not really an error.
        PROTOCOL: The remote system returned something that was "not possible" during
          a protocol exchange.
        NOPERM: You did not have sufficient permission to perform the operation. This
            is not intended for file system problems.
        CONFIG: Something was found in an unconfigured or misconfigured state.
    """

    OK = 0
    ERR = 1
    DATAERR = 65
    NOINPUT = 66
    NOHOST = 68
    UNAVAILABLE = 69
    SOFTWARE = 70
    IOERR = 74
    TEMPFAIL = 75
    PROTOCOL = 76
    NOPERM = 77
    CONFIG = 78
