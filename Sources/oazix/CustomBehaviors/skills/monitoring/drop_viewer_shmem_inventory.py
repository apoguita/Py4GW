from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import (
    handle_inventory_action_branch,
    handle_inventory_stats_request_branch,
    handle_inventory_stats_response_branch,
)


def process_inventory_message(
    viewer,
    *,
    extra_0,
    extra_data_list,
    shared_msg,
    my_email,
    msg_idx,
    shmem,
    to_text_fn,
    normalize_text_fn,
):
    inventory_action_result = {"value": None}

    def _run_inventory_action_capture(action_code_arg, action_payload_arg, action_meta_arg, sender_email_arg):
        result = viewer._run_inventory_action(
            action_code_arg,
            action_payload_arg,
            action_meta_arg,
            sender_email_arg,
        )
        inventory_action_result["value"] = result
        return True

    if handle_inventory_action_branch(
        extra_0=extra_0,
        expected_tag=viewer.inventory_action_tag,
        extra_data_list=extra_data_list,
        shared_msg=shared_msg,
        to_text_fn=to_text_fn,
        normalize_text_fn=normalize_text_fn,
        run_inventory_action_fn=_run_inventory_action_capture,
    ):
        action_result = inventory_action_result.get("value")
        should_finish = not bool(action_result.is_deferred) if action_result is not None else True
        if should_finish:
            shmem.MarkMessageAsFinished(my_email, msg_idx)
            return {"handled": 1, "processed": 1, "inventory_action": 1}
        return {"handled": 1, "processed": 0, "inventory_action": 1}

    if handle_inventory_stats_request_branch(
        extra_0=extra_0,
        expected_tag=viewer.inventory_stats_request_tag,
        shared_msg=shared_msg,
        my_email=my_email,
        normalize_text_fn=normalize_text_fn,
        send_inventory_kit_stats_response_fn=viewer._send_inventory_kit_stats_response,
    ):
        shmem.MarkMessageAsFinished(my_email, msg_idx)
        return {"handled": 1, "processed": 1, "inventory_action": 0}

    if handle_inventory_stats_response_branch(
        extra_0=extra_0,
        expected_tag=viewer.inventory_stats_response_tag,
        extra_data_list=extra_data_list,
        shared_msg=shared_msg,
        to_text_fn=to_text_fn,
        normalize_text_fn=normalize_text_fn,
        safe_int_fn=viewer._safe_int,
        get_account_data_fn=shmem.GetAccountDataFromEmail,
        upsert_inventory_kit_stats_fn=viewer._upsert_inventory_kit_stats,
    ):
        shmem.MarkMessageAsFinished(my_email, msg_idx)
        return {"handled": 1, "processed": 1, "inventory_action": 0}

    return {"handled": 0, "processed": 0, "inventory_action": 0}
