provider google {
  credentials  = file(var.credentials_file_name)
  project      = var.project_id
  region       = var.region_gcp
  zone         = var.zone_gcp
}


terraform {
  backend "gcs" {
    bucket      = "charles-sandbox-274617-terraform"
    prefix      = "state"
    credentials = "./terraform.json"
  }
}


provider "archive" {
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
  name                  = "new_opco_generator"
  description           = "[Managed by Terraform] This function gets triggered by an http GET call and will start BigQuery flex slots."
  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket_object.zip_file_start_flex.bucket
  source_archive_object = google_storage_bucket_object.zip_file_start_flex.name
  entry_point           = "main"
  region                = var.region_gcp
  runtime               = "python37"
  trigger_http          = true

  environment_variables = {
    LOCATION     = var.location_flex_slots
  }
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
  name                  = "new_opco_generator"
  description           = "[Managed by Terraform] This function gets triggered by an http GET call and will stop BigQuery flex slots."
  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket_object.zip_file_stop_flex.bucket
  source_archive_object = google_storage_bucket_object.zip_file_stop_flex.name
  entry_point           = "main"
  region                = var.region_gcp
  runtime               = "python37"
  trigger_http          = true

  environment_variables = {
    LOCATION     = var.location_flex_slots
  }
}