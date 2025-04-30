from sys import argv
import requests
import argparse
from string import hexdigits


def get_mac_address_vendor(mac_address) -> str | None:
    """Get the vendor of the MAC address by using the macvendors.com API.
    It takes a MAC address as a string input and a boolean to determine, if debug is enabled.
    It returns a tuple containing the vendor name (of type str) and the status code (of type int) of the API call."""
    mac_address_vendor_api_url = "https://api.macvendors.com/" + mac_address
    mac_address_vendor_api_call = requests.get(mac_address_vendor_api_url)
    mac_address_vendor_api_call_text = mac_address_vendor_api_call.text
    if mac_address_vendor_api_call_text == '{"errors":{"detail":"Not Found"}}' or mac_address_vendor_api_call.status_code != 200:
        return None
    return mac_address_vendor_api_call.text


def is_valid_mac_address(mac_address: str) -> bool:
    """It checks if the given MAC Address is valid by checking if the raw length is 12.
    It also prints a message if the MAC Address is invalid including supported mac address formats. It returns True if the MAC Address is valid, otherwise False."""
    count: int = 0
    for character in mac_address:
        if character in hexdigits:
            count += 1

    if count != 12:
        raise Exception("Invalid MAC Address submitted.\nPlease enter a valid Mac Address with a length of 12 or more characters\nSupported formats are like the following:\nD83ADDEE5522\nd83addee5522\nD8-3A-DD-EE-55-22\nD8:3A:DD:EE:55:22\nd8$3A$DD$eE$55!22")
    return True


def get_raw_mac_address(mac_address: str) -> str:
    raw_mac_address: str = ""
    for index, letter in enumerate(mac_address):
        if letter in hexdigits:
            raw_mac_address += mac_address[index]

    return raw_mac_address


def convert_mac_address(raw_mac_address: str, separation_character: str) -> str | None:
    count: int = 0
    amount_of_times_true: int = 0
    mac_address = raw_mac_address
    for i in range(len(raw_mac_address)):
        if count == 2:
            mac_address = mac_address[:i + (amount_of_times_true * len(separation_character))] + separation_character + mac_address[i + (amount_of_times_true * len(separation_character)):]
            count = 0
            amount_of_times_true += 1

        count += 1

    return mac_address.upper()

def get_args() -> argparse.PARSER:
    parser = argparse.ArgumentParser("This is a Converter which converts MAC Address Notation to a other one [e.g. 'E8-9C-25-DC-A5-EA' -> 'E8:9C:25:DC:A5:EA']\nIt will lookup the vendor of the MAC Address by default.\n\n\t©timmatheis-de")
    parser.add_argument("-m", "--mac-address", required=False, action="store", dest="mac_address", help="Provide MAC Address in supported format.", type=str)
    parser.add_argument("-s", "--separator", required=False, default="-", action="store", dest="separation_character", help="Enter symbol used for separation. [Default: '-']", type=str)
    parser.add_argument("-l", "--lower", required=False, default=False, action="store_true", dest="lower_boolean", help="Specify to change the MAC Address to only lowercase. [Default: False]")
    parser.add_argument("-a", "--api", required=False, default=False, action="store_true", dest="api_boolean", help="Specify to enable the API lookup of your MAC Address. [Default: False]")
    return parser.parse_args()


def main() -> None:
    lower = False
    cli_args_given = False
    api = False

    # Check if any arguments were passed, excluding the program name
    if len(argv) > 1:
        try:
            args = get_args()
            cli_args_given = True
        except SystemExit:  # This exception is raised when -h or --help is called and help is printed
            quit("Exiting. User entered '-h/--help'")
        except Exception as e:
            print(f"Error parsing arguments: {e}\nUsing interactive mode instead")
    else:
        print("No arguments provided. Using interactive mode.")

    if cli_args_given:
        mac_address: str = args.mac_address
        separation_character: str = args.separation_character
        if args.lower_boolean:
            lower = True
        if args.api_boolean:
            api = True
    else:
        mac_address = input("Enter a MAC-Address: ")
        separation_character = input("Enter the separation character: ")

    raw_mac_address = get_raw_mac_address(mac_address)
    if is_valid_mac_address(raw_mac_address):
        mac_address = convert_mac_address(raw_mac_address, separation_character)
        if api:
            vendor = get_mac_address_vendor(raw_mac_address)
            print(f"MAC Address: {mac_address.lower() if lower is True else mac_address}\nVendor: {vendor}")
        else:
            print(f"MAC Address: {mac_address.lower() if lower is True else mac_address}")

if __name__ == "__main__":
    main()