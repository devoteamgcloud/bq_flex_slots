"""This module contains the Cloud Function that stops a commitment, reservation and assignments in BigQuery."""
from google.cloud.bigquery.reservation_v1 import *
from google.api_core import retry
from flask import jsonify
import time
import os

project_id = os.environ.get("GCP_PROJECT")
location = os.environ.get("LOCATION")
parent_arg = "projects/{}/locations/{}".format(project_id, "EU")

res_api = ReservationServiceClient()


def get_list_ids():

    list_commitments = [i.name for i in res_api.list_capacity_commitments(parent=parent_arg)]
    list_reservations = [i.name for i in res_api.list_reservations(parent=parent_arg)]

    list_assignments = []
    for i in list(map(lambda x: x.split("/")[-1], list_reservations)):
        list_assignments.extend([i.name for i in res_api.list_assignments(parent=parent_arg + "/reservations/" + i)])

    return list_commitments, list_reservations, list_assignments


def cleanup(list_commitments, list_reservations, list_assignments):
    for i in list_assignments:
        res_api.delete_assignment(name=i)
    for i in list_reservations:
        res_api.delete_reservation(name=i)
    for i in list_commitments:
        res_api.delete_capacity_commitment(name=i,
                                           retry=retry.Retry(deadline=90,
                                                             predicate=Exception,
                                                             maximum=2))


def main(context):
    try:
        start = time.time()
        # Get a list list id for the commitments, reservations and assignments
        list_commitments, list_reservations, list_assignments = get_list_ids()
        # Delete all the assignments, reservations and commitments
        cleanup(list_commitments, list_reservations, list_assignments)
        end = time.time()
        print("Deleting ran for ~{} seconds".format((end - start)))

        return jsonify(success=True)

    except Exception as e:
        print(e)
        return
