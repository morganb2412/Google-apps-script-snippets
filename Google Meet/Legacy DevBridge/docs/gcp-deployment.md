# GCP deployment

Target project: `moesautomationweekly`; default region: `us-central1`; Cloud Run service: `legacy-devbridge-api`.

Prerequisites are an Artifact Registry Docker repository named `legacy-devbridge`, enabled Cloud Build/Run/Artifact Registry APIs, and a deployer identity with scoped permissions. The service is private by default. Run from `legacy-devbridge/`:

```bash
gcloud builds submit --project=moesautomationweekly --config=cloudbuild.yaml .
```

Configure a deliberate caller identity or API gateway before granting public access. Future secrets are added as Secret Manager references, not plaintext environment variables.
