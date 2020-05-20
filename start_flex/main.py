"""This module contains the Cloud Function that creates a reservation in BigQuery for a certain amount of slots."""
from apiclient.discovery import build
import time
import os


project_id = os.environ.get("GCP_PROJECT")

reservation_name = 'daily-reservation'

parent_arg = "projects/{}/locations/{}".format(project_id, "EU")


def purchase_commitment(res_api, slots=500):
    commitment_req = {
        'plan':'FLEX',
        'slotCount': slots
      }

    commit = res_api.capacityCommitments()\
                    .create(parent=parent_arg, body=commitment_req)\
                    .execute()
    print(commit)
    return commit['name']


def create_reservation(res_api, reservation, slots=500):
    reservation_req = {
        'slotCapacity':slots,
        'ignoreIdleSlots': False
      }
    res = res_api.reservations()\
                 .create(parent=parent_arg,
                         reservationId=reservation,
                         body=reservation_req)\
                 .execute()
    print(res)
    return res['name']


def create_assignment(res_api, reservation_id, user_project):
    assignment_req = {
        'assignee':"projects/{}".format(user_project),
        'jobType':"QUERY"
      }
    assignment = res_api.reservations()\
                        .assignments()\
                        .create(parent=reservation_id, body=assignment_req)\
                        .execute()
    print(assignment)
    return assignment['name']


def main(context):

    print(context)

    slots_required = context.args.get('slots')

    print(slots_required)

    try:
        start = time.time()

        res_api = build(serviceName='bigqueryreservation',
                        version="v1beta1", cache_discovery=False) \
            .projects() \
            .locations()

        commit_id = purchase_commitment(res_api, int(slots_required))
        res_id = create_reservation(res_api, reservation_name, int(slots_required))
        assign_id = create_assignment(res_api, res_id, project_id)

        end = time.time()
        print("Function ran for ~{} seconds".format((end - start)))
        print("commit id: ", commit_id)
        print("res id: ", res_id)
        print("assign id: ", assign_id)

        return "ok"

    except Exception as e:
        print(e)
        return
