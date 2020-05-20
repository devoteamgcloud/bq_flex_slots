"""This module contains the Cloud Function that creates a reservation in BigQuery for a certain amount of slots."""
from apiclient.discovery import build
import time
import os


project_id = os.environ.get("GCP_PROJECT")
region = "EU"

reservation_name = 'daily-reservation'

parent_arg = "projects/{}/locations/{}".format(project_id, "EU")


def get_ids(res_api):
    parent_assign = "projects/{}/locations/{}/reservations/{}".format(project_id, region, reservation_name)
    parent_res = "projects/{}/locations/{}".format(project_id, region)
    parent_commit = "projects/{}/locations/{}".format(project_id, region)

    assignment_id = res_api.reservations() \
                           .assignments().list(parent=parent_assign) \
                           .execute()['assignments'][0]['name']

    reservation_id = res_api.reservations()\
                            .list(parent=parent_res)\
                            .execute()['reservations'][0]['name']

    commit_id = res_api.capacityCommitments() \
                       .list(parent=parent_commit) \
                       .execute()['capacityCommitments'][0]['name']

    return assignment_id, reservation_id, commit_id


def cleanup(res_api, assignment_id, reservation_id, commit_id):
    res_api.reservations() \
        .assignments().delete(name=assignment_id) \
        .execute()
    res_api.reservations() \
        .delete(name=reservation_id) \
        .execute()

    retry = 0
    while retry < 20:
        try:
            res_api.capacityCommitments() \
                .delete(name=commit_id) \
                .execute()
            break
        except:
            retry += 1
            time.sleep(5)


def main(context):

    print(context)

    try:
        start = time.time()

        res_api = build(serviceName='bigqueryreservation',
                        version="v1beta1", cache_discovery=False) \
            .projects() \
            .locations()

        assign_id, res_id, commit_id = get_ids(res_api)

        cleanup(res_api, assign_id, res_id, commit_id)

        end = time.time()
        print("Deleting ran for ~{} seconds".format((end - start)))

    except Exception as e:
        print(e)
        return
