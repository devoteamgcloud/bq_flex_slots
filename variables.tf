variable "credentials_file_name" {
  type    = "string"
  default = "terraform.json"
}

variable project_id {
  type = string
}

variable region_gcp {
  type = string
}

variable zone_gcp {
  type = string
}

variable location_flex_slots {
  type = string
}