provider google {
  credentials  = file(var.credentials_file_name)
  project      = var.project_id
  region       = var.region_gcp
  zone         = var.zone_gcp
}

terraform {
  backend "gcs" {
    bucket      = "[TERRAFORM-STATE-BUCKET]"
    prefix      = "state"
    credentials = "./terraform.json"
  }
}

provider "archive" {
}

resource "google_project_service" "cf-service" {
  project = var.project_id
  service = "bigqueryreservation.googleapis.com"
}

resource "google_project_service" "reservation-service" {
  project = var.project_id
  service = "cloudfunctions.googleapis.com"
}

resource "google_project_service" "iam-service" {
  project = var.project_id
  service = "iam.googleapis.com"
}

// Create a service account for the two cloud functions
resource "google_service_account" "bq-flex-slots" {
  account_id   = "sa-bq-flex-slots"
  display_name = "service account used by the two Cloud Functions related to BigQuery flex slots."
  project      = var.project_id
}

resource "null_resource" "delay_iam_0" {
  provisioner "local-exec" {
    command = "sleep 10"
  }
  depends_on = [google_service_account.bq-flex-slots, google_service_account.iam-service]
}

// Assign roles to this service account
resource "google_project_iam_member" "cf-sa-access" {
  for_each   = var.cf_roles
  project    = var.project_id
  member     = "serviceAccount:${google_service_account.bq-flex-slots.email}"
  role       = each.value
  depends_on = [null_resource.delay_iam_0]
}

// Allow terraform service account to deploy Cloud Functions with the newly created service account
resource "google_service_account_iam_member" "terraform-impersonation-cf-sa" {
  service_account_id = google_service_account.bq-flex-slots.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${var.terraform_service_account_email}"
  depends_on = [null_resource.delay_iam_0]
}

// Create a bucket to store the cloud function code
resource "google_storage_bucket" "cf_code" {
  project            = var.project_id
  name               = "${var.project_id}-cf-bq-flex-slots"
  location           = "EU"
  bucket_policy_only = true
  force_destroy      = true
}

// Archive the start bq flex cloud function code and upload it as a zip on a bucket
data "archive_file" "function_start_flex_slots" {
  type        = "zip"
  source_dir  = "${path.module}/start_flex"
  output_path = "${path.module}/start_flex_zip/CF.zip"
}

resource "google_storage_bucket_object" "zip_file_start_flex" {
  name   = "CF/start-flex-slots-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  bucket = google_storage_bucket.cf_code.name
  source = data.archive_file.function_start_flex_slots.output_path
  lifecycle {
    ignore_changes = [name]
  }
}

// Deploy the start bq flex slots Cloud Function
resource "google_cloudfunctions_function" "start_flex_slots" {
  name                  = "start_bq_flex"
  description           = "[Managed by Terraform] This function gets triggered by a http GET call and will start BigQuery flex slots."
  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket_object.zip_file_start_flex.bucket
  source_archive_object = google_storage_bucket_object.zip_file_start_flex.name
  entry_point           = "main"
  region                = var.region_gcp
  runtime               = "python37"
  service_account_email = google_service_account.bq-flex-slots.email
  trigger_http          = true

  environment_variables = {
    LOCATION     = var.location_flex_slots
  }

  depends_on = [google_project_service.cf-service]

}

// Archive the stop bq flex cloud function code and upload it as a zip on a bucket
data "archive_file" "function_stop_flex_slots" {
  type        = "zip"
  source_dir  = "${path.module}/stop_flex"
  output_path = "${path.module}/stop_flex_zip/CF.zip"
}

resource "google_storage_bucket_object" "zip_file_stop_flex" {
  name   = "CF/stop-flex-slots-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  bucket = google_storage_bucket.cf_code.name
  source = data.archive_file.function_stop_flex_slots.output_path
  lifecycle {
    ignore_changes = [name]
  }
}

// Deploy the stop bq flex slots Cloud Function
resource "google_cloudfunctions_function" "stop_flex_slots" {
  name                  = "stop_bq_flex"
  description           = "[Managed by Terraform] This function gets triggered by a http GET call and will stop BigQuery flex slots."
  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket_object.zip_file_stop_flex.bucket
  source_archive_object = google_storage_bucket_object.zip_file_stop_flex.name
  entry_point           = "main"
  region                = var.region_gcp
  runtime               = "python37"
  service_account_email = google_service_account.bq-flex-slots.email
  trigger_http          = true

  environment_variables = {
    LOCATION     = var.location_flex_slots
  }

  depends_on = [google_project_service.cf-service]
}