from .. import config
from .repository import AlloyDBRepository, SqliteRepository


def make_repository():
    if config.DB_BACKEND == "alloydb":
        if not config.ALLOYDB_DSN:
            raise RuntimeError("ACCESSPILOT_DB=alloydb needs ALLOYDB_DSN to be set.")
        return AlloyDBRepository(config.ALLOYDB_DSN, config.ALLOYDB_EMBEDDING_MODEL)
    return SqliteRepository(config.SQLITE_PATH)
