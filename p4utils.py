import os
import subprocess

from P4 import P4, P4Exception

p4 = P4()


def submit(change_num, change_desc=None):
    if change_desc:
        update_change_desc(change_num, change_desc)
    try:
        p4.connect()

        p4.run_submit("-c", change_num)

        p4.disconnect()
    except P4Exception as e:
        print(e)
        p4.disconnect()


def revert_unchanged(files=None, changelist=None):
    if files:
        if isinstance(files, list):
            pass
        elif isinstance(files, str):
            files = [files]
        else:
            raise Exception("files must be string or list of strings")

    print("reverting unchaned files", files)
    try:
        p4.connect()

        if files:
            p4.run("revert", "-a", *files)
        elif changelist:
            p4.run("revert", "-a", "-c", changelist)

    except P4Exception as e:
        p4.disconnect()
        print("P4Exception")
        print(e)


def get_file_info(files):
    print("\ngetting file status for:", files)
    if isinstance(files, list):
        pass
    elif isinstance(files, str):
        files = [files]
    else:
        raise Exception("files must be string or list of strings")

    file_info_list = []
    changelists = []
    try:
        p4.connect()

        for file in files:
            try:
                # stat file each file individually
                cmd_return_vals = p4.run_fstat(file)[0]

                # depending on if the file has been submitted or not it will have different keys
                if "change" in cmd_return_vals:
                    changelist = cmd_return_vals["change"]
                    action = cmd_return_vals["action"]
                else:
                    changelist = cmd_return_vals["headChange"]
                    action = cmd_return_vals["headAction"]
                depot_file = cmd_return_vals["depotFile"]

                # add changelist to list if not a duplicate
                if changelist not in changelists:
                    changelists.append(changelist)

                # collect information about file and add it to list
                file_info = {
                    "action": action,
                    "change": changelist,
                    "depotFile": depot_file,
                    "client_file": cmd_return_vals["clientFile"],
                }
                if "haveRev" in cmd_return_vals:
                    file_info["have_rev"] = cmd_return_vals["haveRev"]
                if "headRev" in cmd_return_vals:
                    file_info["head_rev"] = cmd_return_vals["headRev"]

                file_info_list.append(file_info)
            except P4Exception:
                # files that trigger this exception are either nonexistent or not in a changelist/depot
                # for now I'm just assuming the file is existent
                # collect information about file and add it to list
                file_info = {
                    "action": None,
                    "change": None,
                    "depotFile": None,
                    "status": "unopened",
                    "client_file": os.path.abspath(file),
                }
                file_info_list.append(file_info)

        # unopened files don't have changelist, make sure there are changelists before continuing
        if len(changelists) > 0:
            # fetch description of all unique changelists to get the status
            changelist_descriptions = p4.run_describe("-s", changelists)
            # container for the status of each changelist with the key being the changelist number
            changelist_status_dict = {}
            # get status of each changelist and populate dict
            for i, changelist in enumerate(changelist_descriptions):
                changelist_num = changelists[i]
                changelist_status_dict.update({changelist_num: changelist["status"]})

            for file_info in file_info_list:
                changelist_num = file_info["change"]
                if not changelist_num:
                    continue
                file_info["status"] = changelist_status_dict[changelist_num]

        # disconnect at end of session
        p4.disconnect()
    except P4Exception as e:
        print("P4Exception")
        print(e)
        print("changelists", changelists)
        p4.disconnect()

    # return information about file(s) argument
    return file_info_list


def get_user_from_workspace():
    client = p4.client
    client_split = client.split("-")

    user = "Unknown user"

    if len(client_split) > 1:
        user = client_split[1]

    return user


def format_change_desc(
    unformatted_change_desc, subject_type="Asset", subject_type_desc=None
):
    if unformatted_change_desc == "" or unformatted_change_desc is None:
        unformatted_change_desc = "automatic changelist"
    print("UNFORMATED CHANGE TYPE", type(unformatted_change_desc))

    # fetch user
    user = get_user_from_workspace()

    # format description
    change_desc = f"User: {user}"
    if subject_type and subject_type_desc:
        change_desc += f"\n{subject_type}: {subject_type_desc}"
    change_desc += "\n\ndesc:\n" + unformatted_change_desc

    return change_desc


def validate_changelist(
    change_num, change_description, subject_type="Asset", subject_type_desc=None
):
    change_info = get_change_info(change_num)
    print("change info:", change_info)
    is_valid_changelist = change_info and change_info[0]["status"] == "pending"
    print(f"changelist number: {change_num}, valid: {is_valid_changelist}")

    if not is_valid_changelist:
        change_description = format_change_desc(
            change_description, subject_type, subject_type_desc
        )
        change_num = make_change(change_description)

    return change_num


def add(
    files,
    change_num=None,
    change_description=None,
    subject_type=None,
    subject_type_desc=None,
):
    change_num = validate_changelist(
        change_num, change_description, subject_type, subject_type_desc
    )

    if isinstance(files, list):
        pass
    elif isinstance(files, str):
        files = [files]
    else:
        raise Exception("files must be string or list of strings")

    print(f"Adding: {files}, to changelist: {change_num}")

    # Connect to perforce server
    try:
        p4.connect()

        # add file to changelist
        cmd_return = p4.run("add", "-c", change_num, files)
        print(cmd_return)

        p4.disconnect()
    except P4Exception:
        for e in p4.errors:
            print(e)
    return change_num


def edit(
    files, change_num=None, change_desc=None, subject_type=None, subject_type_desc=None
):
    change_num = validate_changelist(
        change_num, change_desc, subject_type, subject_type_desc
    )

    if isinstance(files, list):
        pass
    elif isinstance(files, str):
        files = [files]
    else:
        raise Exception("files must be string or list of strings")

    print(f"Adding: {files}, to changelist: {change_num}")

    # Connect to perforce server
    try:
        p4.connect()

        # add edit action to changelist
        cmd_return = p4.run_edit("-c", change_num, files)
        print(cmd_return)

        p4.disconnect()
    except P4Exception:
        print(P4Exception)
        p4.disconnect()

    return change_num


def get_change_info(change_num):
    try:
        p4.connect()
        status = p4.run_describe(change_num)
        p4.disconnect()
        return status
    except P4Exception:
        print("P4Exception")
        for e in p4.errors:
            print(e)
        return


def update_change_desc(
    change_num, change_desc, subject_type="Asset", subject_type_desc=None
):
    change_desc = format_change_desc(
        change_desc, subject_type=subject_type, subject_type_desc=subject_type_desc
    )
    try:
        p4.connect()

        change = p4.fetch_change(change_num)
        change._description = change_desc
        cmd_return = p4.save_change(change)

        p4.disconnect()
    except P4Exception:
        print(P4Exception)
        p4.disconnect()


# creates changelist
def make_change(description):
    try:
        p4.connect()

        change = p4.fetch_change()
        change._description = description
        cmd_return = p4.save_change(change)
        change_num = cmd_return[0].split(" ")[1].strip()
        print(f"New changelist created with id: {change_num}, desc: {description}")
        p4.disconnect()

        return change_num
    except P4Exception:
        for e in p4.errors:
            print(e)


def get_latest(file_path):
    try:
        p4.connect()
        p4.run("sync", file_path + "#head")
        p4.disconnect()
    except P4Exception:
        print(P4Exception)
        p4.disconnect()
