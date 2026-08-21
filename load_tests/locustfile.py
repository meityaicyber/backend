from locust import HttpUser, task, between, events
import uuid
import random

# We want 0% 5xx errors. We'll mark 429s as successes from a testing framework perspective,
# because 429 means our admission control worked properly to PREVENT a 500 error.
# We explicitly want to ensure no 500s are returned.

class DocumentUploader(HttpUser):
    # Wait between 1 and 3 seconds between tasks if running continuously
    wait_time = between(1, 3)

    @task
    def upload_document(self):
        # Generate unique idempotency key per request
        idempotency_key = str(uuid.uuid4())
        
        # Pick a random agency to spread Kafka partitions
        agency_id = f"agency-{random.randint(1, 100)}"
        case_id = f"case-{random.randint(1000, 9999)}"
        doc_ref = f"doc-{random.randint(1000, 9999)}"

        headers = {
            "Idempotency-Key": idempotency_key
        }

        data = {
            "agency_id": agency_id,
            "case_id": case_id,
            "document_reference": doc_ref
        }

        # Use a dummy file for the upload
        with open("dummy.pdf", "rb") as f:
            files = {
                "file": ("dummy.pdf", f, "application/pdf")
            }
            
            with self.client.post("/documents", headers=headers, data=data, files=files, catch_response=True) as response:
                if response.status_code == 202:
                    response.success()
                elif response.status_code == 429:
                    # 429 is expected during overload and indicates our admission control works.
                    # We mark it as success to separate it from actual failures (500).
                    response.success()
                else:
                    response.failure(f"Unexpected status code: {response.status_code}")
