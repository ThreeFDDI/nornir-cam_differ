import sys
import json
import difflib
from getpass import getpass
from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from pprint import pprint

# print formatting function
def c_print(printme):
    """
    Function to print centered text with newline before and after
    """
    print(f"\n" + printme.center(80, " ") + "\n")


# continue banner
def proceed():
    """
    Function to prompt to proceed or exit script
    """
    c_print("********** PROCEED? **********")
    # capture user input
    confirm = input(" " * 36 + "(y/n) ")
    # quit script if not confirmed
    if confirm.lower() != "y":
        c_print("******* EXITING SCRIPT *******")
        print("~" * 80)
        exit()
    else:
        c_print("********* PROCEEDING *********")


# set device credentials
def kickoff():
    """
    Nornir kickoff function to initialize inventory and set or confirm credentials
    """
    # check arguments for site code
    if len(sys.argv) < 2:
        # set no site code
        site = ""
        site_ = ""

    else:
        # set site code
        site = sys.argv[1]
        site_ = sys.argv[1] + "_"

    # print banner
    print()
    print("~" * 80)

    # initialize The Norn
    nr = InitNornir(
        logging={"file": f"logs/{site_}nornir_log.txt", "level": "debug"},
        inventory={
            "plugin": "nornir.plugins.inventory.simple.SimpleInventory",
            "options": {
                "host_file": f"inventory/{site_}hosts.yaml",
                "group_file": f"inventory/{site_}groups.yaml",
                "defaults_file": "inventory/defaults.yaml",
            },
        },
    )

    # filter The Norn
    nr = nr.filter(platform="ios")

    if len(nr.inventory.hosts) == 0:
        c_print("*** No matching hosts found in inventory ***")
        print("~" * 80)
        exit()

    else:
        c_print(
            "This script will collect and compare CAM tables on Cisco Catalyst switches"
        )
        c_print(f"Inventory includes the following devices {site}:")
        for host in nr.inventory.hosts.keys():
            c_print(f"*** {host} ***")

    c_print("Checking inventory for credentials")
    # check for shared credentials in inventory

    if nr.inventory.defaults.username == None or nr.inventory.defaults.password == None:
        c_print("Please enter device credentials:")

        if nr.inventory.defaults.username == None:
            nr.inventory.defaults.username = input("Username: ")

        if nr.inventory.defaults.password == None:
            nr.inventory.defaults.password = getpass()
            print()

    print("~" * 80)
    return nr


def set_mode():
    c_print("Please select script mode of operation:")
    print(" " * 20 + "1. Pre migration CAM table collection")
    print(" " * 20 + "2. Post migration CAM table collection\n")
    mode = input(" " * 20 + "Mode: ")

    if str(mode) == "2":
        mode = "post"
    else:
        mode = "pre"

    return mode


def get_cam(task):
    cmd = "show mac address | exclude criterion"
    cam = task.run(task=netmiko_send_command, command_string=cmd, use_textfsm=True)


def unique_entries(mode):
    if mode == "pre":
        alt_mode = "post"
    else:
        alt_mode = "pre"

    with open(f"test_data/{mode}_data.txt", "r") as infile:
        entries = json.load(infile)

    with open(f"test_data/{alt_mode}_data.txt", "r") as infile:
        compare = json.load(infile)

    unique = []
    shared = []

    for entry in entries:
        if (
            next(
                (
                    None
                    for alt in compare
                    if alt["destination_address"] == entry["destination_address"]
                ),
                entry,
            )
            != None
        ):
            unique.append(entry)
        else:
            shared.append(entry)

    return unique, shared


def diff_cam(task):

    c_print("Unique entries seen before migration")

    pre_unique, pre_shared = unique_entries("pre")
    pprint(pre_unique)

    c_print("Unique entries seen after migration")

    post_unique, post_shared = unique_entries("post")
    pprint(post_unique)

    if pre_shared == post_shared:
        c_print("MATCH")

    c_print("Shared entries seen before migration")

    pprint(pre_shared)

    c_print("Shared entries seen after migration")

    pprint(post_shared)

    """

    diff logic:

    find all MACs in pre list but not in post list

    find all MACs in post list but not in pre list

    compare all MACs in both lists and check interface

    """


# main function
def main():
    """
    Main function and script logic
    """
    # kickoff The Norn
    nr = kickoff()

    # set script mode to pre or post
    # mode = set_mode()
    # print(mode)
    # diff CAM table
    c_print(f"Compare pre and post CAM tables for each device")
    # run The Norn to diff CAM table
    nr.run(task=diff_cam)
    c_print(f"Failed hosts: {nr.data.failed_hosts}")
    print("~" * 80)


if __name__ == "__main__":
    main()
