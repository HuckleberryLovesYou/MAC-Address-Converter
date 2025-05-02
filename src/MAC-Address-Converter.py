import argparse
import csv
from string import hexdigits
from sys import argv
from time import sleep
from tkinter import filedialog
import requests
import progressbar
from progressbar import FormatLabel


def get_mac_address_vendor(mac_address: str, api_token: str | None) -> str:
    """
    Gets the vendor of the interface with the provided MAC address by using https://api.macvendors.com.
    It will call the API only with the vendor specific part of the MAC Address so it's not device specific.
    It returns the vendor name.
    """
    if api_token is None:
        mac_address_vendor_api_call = requests.get("https://api.macvendors.com/" + mac_address[:6])
    else:
        mac_address_vendor_api_call = requests.get("https://api.macvendors.com/" + mac_address[:6], headers={"Authorization": f"Bearer {api_token}"})
    if mac_address_vendor_api_call.text == '{"errors":{"detail":"Not Found"}}':
        if mac_address_vendor_api_call.status_code == 404:
            return f"API Call failed with status code 404"
        elif mac_address_vendor_api_call.status_code == 429:
            return f"You are being rate-limited by the API."
        return "Vendor not found"
    return mac_address_vendor_api_call.text


def get_raw_mac_address(mac_address: str) -> str:
    raw_mac_address: str = ""
    for letter in mac_address:
        if letter in hexdigits:
            raw_mac_address += letter

    if len(raw_mac_address) != 12:
        raise Exception("Invalid MAC Address submitted.\nPlease enter a valid Mac Address with a length of 12 or more characters\nSupported formats are like the following:\nD83ADDEE5522\nd83addee5522\nD8-3A-DD-EE-55-22\nD8:3A:DD:EE:55:22\nd8$3A$DD$eE$55!22")

    return raw_mac_address


def convert_mac_address(raw_mac_address: str, separation_character: str) -> str | None:
    converted_mac_address = ""
    counter: int = 0
    for letter in raw_mac_address:
        if counter == 2:
            counter = 0
            converted_mac_address += separation_character
        counter += 1
        converted_mac_address += letter
    return converted_mac_address.upper()


def get_args() -> argparse.PARSER:
    parser = argparse.ArgumentParser("This is a Converter which converts MAC Address Notation to a other one [e.g. 'E8-9C-25-DC-A5-EA' -> 'E8:9C:25:DC:A5:EA']\nIt will lookup the vendor of the MAC Address if specified.\n\n\t©timmatheis-de")
    parser.add_argument("-m", "--mac-address", required=False, action="store", dest="mac_address", help="Provide MAC Address in supported format.", type=str)
    parser.add_argument("-s", "--separator", required=False, default="-", action="store", dest="separation_character", help="Enter symbol used for separation. [Default: '-']", type=str)
    parser.add_argument("-l", "--lower", required=False, default=False, action="store_true", dest="lower_boolean", help="Specify to change the MAC Address to only lowercase. [Default: False]")
    parser.add_argument("-a", "--api", required=False, default=False, action="store_true", dest="api_boolean", help="Specify to enable the API lookup of your MAC Address. [Default: False]")
    parser.add_argument("-f", "--file", required=False, default=False, action="store_true", dest="file", help="Specify weather you want to import a CSV file created by the latest version of advanced ip scanner.")
    parser.add_argument("-t", "--api-token", required=False, default=False, action="store", dest="api_token", help="Specify the API Token from the MACVendors API. [e.g.: eyJ0eXAiOiJKV1QiLCJhbG...JJnwt1TqcsvtiqA]")
    parser.add_argument("-o", "--output", required=False, default=False, action="store_true", dest="output_boolean", help="Specify weather to output to a .csv file.")
    return parser.parse_args()

def write_file(output: str) -> None:
    filepath = filedialog.asksaveasfilename(title="Select file to store output", filetypes=(("CSV Files", "*.csv"),)) + ".csv"
    with open(filepath, "w") as csv_file:
        csv_file.write(output)
    print(f"Wrote file to {filepath}")

def get_filepath():
    return filedialog.askopenfilename(title="Select csv-file to iterate through:", filetypes=(("CSV Files", "*.csv"),))

def handle_file(separation_character: str, api: bool, lower: bool, api_token, output: bool):
    filepath = get_filepath()
    with open(filepath, newline='', encoding='utf-16') as csvfile:
        output_list: list[str] = []
        reader = csv.reader(csvfile, delimiter='\t')
        rows = list(reader)
        total_rows = (len(rows) - 1)
        widgets = [progressbar.PercentageLabelBar(), " ", FormatLabel('[%(value)d/%(max_value)d]'), " ", progressbar.ETA()]
        bar = progressbar.ProgressBar(widgets=widgets, max_value=total_rows, redirect_stdout=True).start()
        for i, row in enumerate(rows[1:]):
            columns = str(row).split(",")

            name = columns[1][:-1]
            ip = columns[2][:-1]
            mac_address = columns[12]
            raw_mac_address = get_raw_mac_address(mac_address)
            mac_address = convert_mac_address(raw_mac_address, separation_character)
            if api:
                if output:
                    output_list += f"'Name: {name}', 'IP-Address: {ip}', 'MAC-Address: {mac_address.lower() if lower is True else mac_address}', 'Vendor: {get_mac_address_vendor(raw_mac_address, api_token)}'\n"
                else:
                    print(f"'Name: {name}', 'IP-Address: {ip}', 'MAC-Address: {mac_address.lower() if lower is True else mac_address}', Vendor: {get_mac_address_vendor(raw_mac_address, api_token)}")
                    if not api_token:
                        sleep(0.9)
                    else:
                        sleep(0.15)
            else:
                if output:
                    output_list += f"'Name: {name}', 'IP-Address: {ip}', 'MAC-Address: {mac_address.lower() if lower is True else mac_address}'\n"
                else:
                    print(f"'Name: {name}', 'IP-Address: {ip}', 'MAC-Address: {mac_address.lower() if lower is True else mac_address}'")
            bar.update(i + 1)
        bar.finish()
        if output:
            write_file(''.join(str(line) for line in output_list))
    exit()


def main() -> None:
    lower = False
    cli_args_given = False
    api = False
    output = False
    file = False

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
        separation_character: str = args.separation_character
        if args.lower_boolean:
            lower = True
        if args.api_boolean:
            api = True
        if args.output_boolean:
            output = True
        if args.file:
            file = True
            handle_file(separation_character, api, lower, None, output)
        else:
            mac_address: str = args.mac_address

        if args.api_token is not None and file:
            handle_file(separation_character, api, lower, args.api_token, output)

    else:
        mac_address = input("Enter a MAC-Address: ")
        separation_character = input("Enter the separation character: ")
        if input("Get Vendor of MAC-Address by API [Y/n]:") == "Y":
            api = True

    raw_mac_address = get_raw_mac_address(mac_address)
    mac_address = convert_mac_address(raw_mac_address, separation_character)
    if api:
        vendor = get_mac_address_vendor(raw_mac_address, None)
        print(f"MAC Address: {mac_address.lower() if lower is True else mac_address}\nVendor: {vendor}")
    else:
        print(f"MAC Address: {mac_address.lower() if lower is True else mac_address}")

if __name__ == "__main__":
    main()