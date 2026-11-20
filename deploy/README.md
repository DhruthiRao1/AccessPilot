# Deploying AccessPilot

## 1. AlloyDB (optional; SQLite is the default)

1. Create an AlloyDB cluster and primary instance.
2. Turn on AlloyDB AI: set the instance flag `google_ml_integration.enable_model_support=on`
   and grant the AlloyDB service agent `roles/aiplatform.user` so the database can call Vertex AI embeddings.
3. Create a database called `accesspilot` and start the
   [AlloyDB Auth Proxy](https://cloud.google.com/alloydb/docs/auth-proxy/connect) locally.
4. Install the driver, then create the tables, demo data and embeddings:

```bash
pip install -e ".[alloydb]"
export ALLOYDB_DSN="postgresql://postgres:<password>@127.0.0.1:5432/accesspilot"
python scripts/init_alloydb.py
export ACCESSPILOT_DB=alloydb
```

## 2. Agent Runtime (Vertex AI Agent Engine)

```bash
gcloud auth application-default login
adk deploy agent_engine \
  --project=$GOOGLE_CLOUD_PROJECT \
  --region=$GOOGLE_CLOUD_LOCATION \
  --display_name="AccessPilot" \
  accesspilot
```

For an AlloyDB backend in the cloud, pass `ACCESSPILOT_DB` and `ALLOYDB_DSN` as environment
variables (store the password in Secret Manager) and connect over private IP.

## 3. Cloud Run (alternative)

```bash
adk deploy cloud_run \
  --project=$GOOGLE_CLOUD_PROJECT \
  --region=$GOOGLE_CLOUD_LOCATION \
  --service_name=accesspilot \
  --with_ui \
  accesspilot
```
