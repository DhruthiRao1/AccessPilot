"""Create the AccessPilot schema in AlloyDB, load demo data and generate embeddings.

Usage (with the AlloyDB Auth Proxy running locally):
    export ALLOYDB_DSN="postgresql://postgres:<password>@127.0.0.1:5432/accesspilot"
    python scripts/init_alloydb.py
"""
from accesspilot import config
from accesspilot.db.repository import ALLOYDB_SCHEMA_FILE, AlloyDBRepository, load_seed


def main():
    if not config.ALLOYDB_DSN:
        raise SystemExit("Set ALLOYDB_DSN first.")
    repo = AlloyDBRepository(config.ALLOYDB_DSN, config.ALLOYDB_EMBEDDING_MODEL)
    repo.conn.execute(ALLOYDB_SCHEMA_FILE.read_text())
    repo.conn.commit()

    if not repo._one("SELECT 1 AS x FROM employees LIMIT 1"):
        load_seed(repo)
        print("Loaded demo data.")

    # AlloyDB AI calls Vertex AI from inside the database to embed each catalog item.
    repo._exec(
        "UPDATE catalog SET embedding = embedding(?, name || '. ' || description)::vector",
        (config.ALLOYDB_EMBEDDING_MODEL,),
    )
    print("Embeddings generated with", config.ALLOYDB_EMBEDDING_MODEL)
    print("Test search:", [i["id"] for i in repo.search_catalog("laptop for coding")])


if __name__ == "__main__":
    main()
