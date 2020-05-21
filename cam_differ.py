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
            "This script will apply IBNS dot1x configurations to Cisco Catalyst switches"
        )
        c_print(f"Inventory includes the following devices {site}:")
        for host in nr.inventory.hosts.keys():
            c_print(f"*** {host} ***")

    c_print("Checking inventory for credentials")
    # check for existing credentials in inventory

    if nr.inventory.defaults.username == None or nr.inventory.defaults.password == None:
        c_print("Please enter device credentials:")

        if nr.inventory.defaults.username == None:
            nr.inventory.defaults.username = input("Username: ")

        if nr.inventory.defaults.password == None:
            nr.inventory.defaults.password = getpass()
            print()

    print("~" * 80)
    return nr


def get_cam(task):
    cmd = "show mac address | exclude criterion"
    cam = task.run(
        task=netmiko_send_command, 
        command_string=cmd,
        use_textfsm=True
    )


def diff_cam(task):

#    with open("output/{task.host}_pre_cam.txt", "w+") as file:        
#        pre_cam = file.readlines()
#
#    with open("output/{task.host}_post_cam.txt", "w+") as file:        
#        post_cam = file.readlines()
#
#    for line in difflib.unified_diff(pre_cam, post_cam):
#        print(line)

#    with open('output/data.txt', 'w') as outfile:
#        json.dump(cam.result, outfile)

    with open('output/pre_data.txt', 'r') as infile:
        pre_data = json.load(infile)

    with open('output/post_data.txt', 'r') as infile:
        post_data = json.load(infile)

    pprint(pre_data)

    c_print("~" * 80)
    pprint(post_data)


#    print(next((item for item in data if item["destination_address"] == "0100.0ccc.cccc"), None))



# main function
def main():
    """
    Main function and script logic
    """
    # kickoff The Norn
    nr = kickoff()

    # diff CAM table
    c_print(f"Compare pre and post CAM tables for each device")
    # run The Norn to diff CAM table
    nr.run(task=diff_cam)
    c_print(f"Failed hosts: {nr.data.failed_hosts}")
    print("~" * 80)


if __name__ == "__main__":
    main()
