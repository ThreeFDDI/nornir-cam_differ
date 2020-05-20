import sys
from getpass import getpass
from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command


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


# test Nornir textfsm result
def test_norn_textfsm(task, result, cmd):
    """
    Test Nornir result expected to be a dict within a list
    """
    if type(result) != list or type(result[0]) != dict:
        c_print(f'*** {task.host}: ERROR running "{cmd}" ***')


# test Nornir result
def test_norn(task, result):
    """
    Test Nornir result expected to be a string
    """
    if type(result) != str:
        c_print(f"*** {task.host}: ERROR running Nornir task ***")


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
    cmd = "authentication display new-style"
    cam = task.run(
        task=netmiko_send_command, 
        command_string=cmd,
        use_textfsm=True
    )

    print(cam.result)

# main function
def main():
    """
    Main function and script logic
    """
    # kickoff The Norn
    nr = kickoff()

    # enable SCP
    c_print(f"Enabling SCP for NAPALM on all devices")
    # run The Norn to enable SCP
    nr.run(task=get_cam)
    c_print(f"Failed hosts: {nr.data.failed_hosts}")
    print("~" * 80)

