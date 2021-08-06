class BotError(Exception):
    pass


class ReziApiRequestError(BotError):
    """Raised when requesting Rezi Score API endpoint returns a non OK status code.
    Args:
        statuscode: status code of the request response object
    """
    _MESSAGE = """Could not fetch your score! Please try again in a while.
If the problem persists feel free to mail us."""

    def __init__(self, statuscode):
        super().__init__(self._MESSAGE)


class FileTooSmall(BotError):
    """Raised when downloaded file has size 0bytes.
    Args:
        None
    """
    _MESSAGE = """The resume file is too small."""

    def __init__(self):
        super().__init__(self._MESSAGE)


class FileTooLarge(BotError):
    """The resume file too large.
    Args:
        sizeLimit: Size limit of resume file
    """
    _MESSAGE = """The resume file too large."""

    def __init__(self, sizeLimit):
        message = self._MESSAGE + f"The size limit of a good resume is {sizeLimit//1048576}MB."
        super().__init__(message)


class DriveFileNotFound(BotError):
    """Raised when the drive file URL is invalid.
    Args:
        None
    """
    _MESSAGE = """Could not find your resume! Please review your file URL. Try one of the following ways-
1. Go to your drive > Right click on resume pdf > Share > Change to anyone with this link > Copy Link
2. Go to your drive > Right click on resume pdf > Share > Add Rezi gmail > Share/Send
   Again right click on file > Get Link > Copy Link"""

    def __init__(self):
        super().__init__(self._MESSAGE)


class DriveFileAccessDenied(BotError):
    """Raised when the drive file is private and the file can't be accessed.
    Args:
        None
    """
    _MESSAGE = """Could not fetch your resume! Try one of the following ways-
1. Go to your drive > Right click on resume pdf > Share > Change to anyone with this link > Copy Link
2. Go to your drive > Right click on resume pdf > Share > Add Rezi gmail > Share/Send
   Again right click on file > Get Link > Copy Link"""

    def __init__(self):
        super().__init__(self._MESSAGE)


class DocdroidFileNotFound(BotError):
    """Raised when the docdroid file could not be fetched.
    Args:
        statuscode: status code of the request response object
    """
    _MESSAGE = """Could not find your resume! Please review your file URL."""

    def __init__(self, statuscode):
        super().__init__(self._MESSAGE)


if __name__ == '__main__':
    pass
