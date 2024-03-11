import importlib
import os
import subprocess

import hou

import p4utils

importlib.reload(p4utils)
import P4


def hip_update_status(kwargs, check_file):
    NODE_PENDING_COLOR = hou.Color(0.98, 0.275, 0.275)
    NODE_DEFAULT_COLOR = hou.Color(0.58, 0.77, 1.0)

    node = kwargs["node"]
    status = p4utils.get_file_info(check_file)[0]["status"]
    print(f"file: {check_file}, status: {status}")
    node.parm("p4_hip_status").set(status)

    # color node
    if status != "pending":
        node.setColor(NODE_PENDING_COLOR)
    else:
        node.setColor(NODE_DEFAULT_COLOR)


def hip_add(kwargs):
    node = kwargs["node"]
    change_parm = kwargs["node"].parm("p4_hip_num")
    change_num = change_parm.eval()

    hip_file = hou.getenv("HIPFILE")

    change_desc = node.evalParm("hip_change_desc")
    subject_type, subject_type_desc = get_subject(kwargs)
    change_num = p4utils.add(
        hip_file, change_num, change_desc, subject_type, subject_type_desc
    )

    if change_parm.eval() != change_num:
        change_parm.set(change_num)

    hip_update_status(kwargs, hip_file)


def hip_edit(kwargs):
    node = kwargs["node"]

    change_parm = node.parm("p4_hip_num")
    change_num = change_parm.eval()

    change_desc = node.evalParm("hip_change_desc")

    hip_file = hou.getenv("HIPFILE")

    change_desc = node.evalParm("hip_change_desc")
    subject_type, subject_type_desc = get_subject(kwargs)
    change_num = p4utils.edit(
        hip_file, change_num, change_desc, subject_type, subject_type_desc
    )

    if change_parm.eval() != change_num:
        change_parm.set(change_num)

    hip_update_status(kwargs, hip_file)


def get_subject(kwargs):
    node = kwargs["node"]
    subject_type_parm = node.parm("subject_type")
    subject_type = subject_type_parm.menuLabels()[subject_type_parm.eval()]
    subject_type = subject_type if subject_type != "None" else None
    subject_type_desc = node.evalParm("subject_type_desc")
    subject_type_desc = subject_type_desc if subject_type_desc != "" else None

    # subject_info = {"subject_type":subject_type, "subject_type_desc"}
    return subject_type, subject_type_desc


def hip_update_desc(kwargs):
    node = kwargs["node"]

    change_parm = node.parm("p4_hip_num")
    change_num = change_parm.eval()

    change_desc = node.evalParm("hip_change_desc")

    hip_file = hou.getenv("HIPFILE")

    subject_type, subject_type_desc = get_subject(kwargs)
    p4utils.update_change_desc(change_num, change_desc, subject_type, subject_type_desc)


def hip_update_change_num(kwargs):
    node = kwargs["node"]
    hip_file = hou.getenv("HIPFILE")
    file_info = p4utils.get_file_info(hip_file)

    change_parm = node.parm("p4_hip_num")
    change_num = change_parm.eval()

    change_num = file_info[0]["change"]

    if change_num and change_parm.eval() != change_num:
        change_parm.set(change_num)


def p4_change(description):
    change_num = p4utils.p4_change(description)
    print(change_num)


def hip_submit(kwargs):
    hip_update_desc(kwargs)
    node = kwargs["node"]
    hip_file = hou.getenv("HIPFILE")
    change_parm = node.parm("p4_hip_num")
    change_num = change_parm.eval()

    if node.evalParm("save_on_submit") == 1:
        hou.hipFile.saveAndBackup()

    p4utils.submit(change_num)

    hip_update_status(kwargs, hip_file)


def hip_notify_checkout(kwargs):
    node = kwargs["node"]
    hip_status = node.evalParm("p4_hip_status")
    if hip_status == "pending":
        return

    hip_file = hou.getenv("HIPFILE")
    if hip_status == "" or hip_status == "unopened":
        message_text = f"""File is not in depot, others will not be able to access this file.
Would you like to add the file now?
\nFile:
{hip_file}"""
        option = "add"
    elif hip_status == "submitted":
        message_text = f"""File is not checked out, you will not be able to save this file.
Would you like to check out the file now?
\nFile:
{hip_file}"""
        option = "checkout"

    message_choice = hou.ui.displayMessage(
        message_text,
        buttons=(option, "not now"),
        default_choice=1,
        close_choice=1,
        title=option.title() + " File",
    )

    if message_choice == 0:
        if option == "checkout":
            hip_edit(kwargs)
        elif option == "add":
            hip_add(kwargs)
