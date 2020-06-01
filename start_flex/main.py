"""This module contains the Cloud Function that creates a reservation in BigQuery for a certain amount of slots."""
from google.cloud.bigquery.reservation_v1 import *
from flask import jsonify
import time
import os

project_id = os.environ.get("GCP_PROJECT")
location = os.environ.get("LOCATION")
parent_arg = "projects/{}/locations/{}".format(project_id, "EU")

res_api = ReservationServiceClient()


def purchase_commitment(slots):
    """
    Create a commitment for a specific amount of slots (in increments of 500).
    :param slots: Number of slots to purchase
    :return: the commit name
    """

    commit_config = CapacityCommitment(plan='FLEX', slot_count=slots)

    commit = res_api.create_capacity_commitment(parent=parent_arg,
                                                capacity_commitment=commit_config)

    print(commit)
    return commit.name


def create_reservation(reservation_name, reservation_slots=500):
    """
    Create a reservation with a specific amount of slots (reservation_slots must be lower than remaining slots available).
    :param reservation_name: Name of the reservation.
    :param reservation_slots: Number of slots for this reservation
    :return: the reservation name
    """

    res_config = Reservation(slot_capacity=reservation_slots, ignore_idle_slots=False)
    res = res_api.create_reservation(parent=parent_arg,
                                     reservation_id=reservation_name,
                                     reservation=res_config)
    print(res)
    return res.name


def create_assignment(reservation_id, user_project):
    """
    Create an assignment of either an organization, folders or projects to a specific reservation.
    :param reservation_id: The reservation id from which the project id will be assigned
    :param user_project: The project id that will use be assigned to this reservation
    :return: the assignment name
    """
    assign_config = Assignment(job_type='QUERY',
                               assignee='projects/{}'.format(user_project))

    assign = res_api.create_assignment(parent=reservation_id,
                                       assignment=assign_config)
    print(assign)
    return assign.name


def main(context):
    """
    Entrypoint of the Cloud Function. Will create the commitment, reservation and assignments.
    :param context:
    :return:
    """

    # Get the various arguments from the function call
    commitment_slots = context.args.get('slots')
    reservation_name = context.args.get('reservation_name')
    reservation_slots = context.args.get('reservation_slots')
    assignment_project = context.args.get('project_id')

    try:
        start = time.time()

        if commitment_slots:
            commit = purchase_commitment(int(commitment_slots))
        reservation = create_reservation(reservation_name, int(reservation_slots))
        assignment = create_assignment(reservation.name, assignment_project)

        # Once assigned, flex slots require some time before being active for a project.
        time.sleep(60)

        end = time.time()

        print("Function ran for ~{} seconds".format((end - start)))
        print("--------------------------------")
        if commitment_slots:
            print("commit id: ", commit.name)
        print("res id: ", reservation.name)
        print("assign id: ", assignment.name)
        print("--------------------------------")

        return jsonify(success=True)

    except Exception as e:
        print(e)
        return
