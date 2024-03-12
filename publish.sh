#!/bin/bash

# set user var
user="parker"
do_p4=0

# checkout file on perforce then copy updated version
function edit_and_copy {
    local source_file=$1
    local destination=$2
    local change_list=$3

    if [[ $do_p4 -eq 1 ]]; then
        p4 edit -c "$change_list" "$destination"
        cp "$source_file" "$destination"
    fi
}

if [[ $do_p4 -eq 1 ]]; then
    # create a new changelist and get its number
    change_list=$(p4 change -o | 
        sed "s/<enter description here>/user:${user} asset:p4 utils desc: update p4 utils/g" | 
        p4 change -i | awk '{print $2}')
fi

# publish files
edit_and_copy "./helpers/" "~/Perforce/y3-film/pipeline/packages/2AM/python_utils/p4utils.py" $change_list
edit_and_copy "./houdini_controller" "~/Perforce/y3-film/pipeline/packages/2AM/houdini/python3.9libs/" $change_list

# submit the changelist
if [[ $do_p4 -eq 1 ]]; then
    p4 submit -c $change_list
fi
