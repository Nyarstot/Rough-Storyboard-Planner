

DEFAULT_FPS = 24
ROWS_PER_PAGE = 6
COLS = 4
TOTAL_PAGES = 20

class ProjectContext(object):

    def __init__(self, defaults:dict) -> None:
        self.fps = DEFAULT_FPS
        self.rowsPerPage = ROWS_PER_PAGE
        self.cols = COLS
        self.totalPages = TOTAL_PAGES

    def reset_defaults(self) -> None:
        self.fps = DEFAULT_FPS
        self.rowsPerPage = ROWS_PER_PAGE
        self.cols = COLS
        self.totalPages = TOTAL_PAGES
