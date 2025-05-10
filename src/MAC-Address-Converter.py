import argparse
import csv
from string import hexdigits
from sys import argv, stdout
from time import sleep
from tkinter import filedialog
import requests
import progressbar
import logging
import colorlog


def get_logger(verbose=False, quiet=False):
    """Multilevel colored log using colorlog"""
    # Define conditional color formatter
    formatter = colorlog.LevelFormatter(
        fmt={
            'DEBUG': '%(log_color)s[%(levelname)s] %(msg)s',
            'INFO': '%(log_color)s[%(levelname)s] %(msg)s',
            'WARNING': '%(log_color)s[%(levelname)s] %(msg)s',
            'ERROR': '%(log_color)s[%(levelname)s] %(msg)s',
            'CRITICAL': '%(log_color)s[%(levelname)s] %(msg)s', },
        reset=True)

    # Define logger with custom color formatter
    logging.basicConfig(format='%(message)s')
    handler = colorlog.StreamHandler(stdout)
    handler.setFormatter(formatter)
    logging.getLogger().handlers[0] = handler
    logger = logging.getLogger(__name__)

    return logger


def get_mac_address_vendor(mac_address: str, api_token: str | None) -> str:
    """
    Gets the vendor of the interface with the provided MAC address by using https://api.macvendors.com.
    It will call the API only with the vendor specific part of the MAC Address so it's not device specific.
    It returns the vendor name.
    """
    counter = 1
    while True:
        if api_token is None:
            mac_address_vendor_api_call = requests.get("https://api.macvendors.com/" + mac_address[:6])
        else:
            mac_address_vendor_api_call = requests.get("https://api.macvendors.com/" + mac_address[:6], headers={"Authorization": f"Bearer {api_token}"})

        if mac_address_vendor_api_call.status_code == 404:
            if mac_address_vendor_api_call.text == '{"errors":{"detail":"Not Found"}}':
                logger.warning(f"Vendor not found for the passed MAC-Address.")
                return "Vendor not found"
            else:
                logger.warning("Contacting the API failed. Check your Internet Connection")
                if counter == 3:
                    logger.warning(f"Vendor Lookup by API failed {counter} times. Skipping MAC-Address '{mac_address}'.")
                    return "Vendor not found"
                else:
                    logger.warning(f"[{counter}/3]Vendor Lookup failed. Retrying.")
                    counter += 1
        elif mac_address_vendor_api_call.status_code == 429:
            logger.warning("You are being rate-limited by the API. If you want to send more requests per second enter your API Token with the --api_token argument")
            if counter == 3:
                logger.warning(f"Vendor Lookup by API failed {counter} times. Skipping MAC-Address '{mac_address}'.")
                return "Vendor not found"
            else:
                logger.warning(f"[{counter}/3]Vendor Lookup failed. Retrying.")
                counter += 1
        return mac_address_vendor_api_call.text


def get_raw_mac_address(mac_address: str) -> str | None:
    raw_mac_address: str = ""
    for letter in mac_address:
        if letter in hexdigits:
            raw_mac_address += letter

    logger.debug(f"Length of the raw MAC-Address is {len(raw_mac_address)}.")
    if len(raw_mac_address) == 12:
        return raw_mac_address
    else:
        logger.error(f"MAC-Address '{raw_mac_address}' is invalid.")
        return None


def convert_mac_address(raw_mac_address: str | None, separation_character: str) -> str | None:
    if raw_mac_address is None:
        return None

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
    parser.add_argument("-s", "--separator", required=True, default="-", action="store", dest="separation_character", help="Enter symbol used for separation. [Default: '-']", type=str)
    parser.add_argument("-l", "--lower", required=False, default=False, action="store_true", dest="lower_boolean", help="Specify to change the MAC Address to only lowercase. [Default: False]")
    parser.add_argument("-a", "--api", required=False, default=False, action="store_true", dest="api_boolean", help="Specify to enable the API lookup of your MAC Address. [Default: False]")
    parser.add_argument("-f", "--file", required=False, default=False, action="store_true", dest="file", help="Specify weather you want to import a CSV file created by the latest version of advanced ip scanner.")
    parser.add_argument("-t", "--api-token", required=False, default=False, action="store", dest="api_token", help="Specify the API Token from the MACVendors API. [e.g.: eyJ0eXAiOiJKV1QiLCJhbG...JJnwt1TqcsvtiqA]")
    parser.add_argument("-o", "--output", required=False, default=False, action="store_true", dest="output_boolean", help="Specify weather to output to a .csv file.")
    parser.add_argument("-v", "--verbose", required=False, default=False, action="store_true", dest="verbose_boolean", help="Specify weather to print all debug logs to the terminal.")
    parser.add_argument("-q", "--quiet", required=False, default=False, action="store_true", dest="quiet_boolean", help="Specify weather to print only warning, error and critical logs to the terminal.")
    return parser.parse_args()


def write_file(output: str) -> None:
    while True:
        filepath = filedialog.asksaveasfilename(title="Select file to store output", filetypes=(("CSV Files", "*.csv"),)) + ".csv"
        if len(filepath) > 0:
            break
        else:
            logger.error("File specified does not exist.")

    with open(filepath, "w") as csv_file:
        csv_file.write(output)
    print(f"Wrote file to {filepath}")


def get_filepath():
    while True:
        filepath = filedialog.askopenfilename(title="Select csv-file to iterate through:", filetypes=(("CSV Files", "*.csv"),))
        if len(filepath) > 0:
            break
        else:
            logger.error("File specified does not exist.")
    return filepath


def handle_file(separation_character: str, api: bool, lower: bool, api_token, output_to_file: bool):
    filepath = get_filepath()
    with open(filepath, newline='', encoding='utf-16') as csvfile:
        output: list[str] = []
        reader = csv.reader(csvfile, delimiter='\t')
        rows = list(reader)
        total_rows = (len(rows) - 1)

        # Define progressbar
        widgets = [progressbar.PercentageLabelBar(), " ", progressbar.FormatLabel('[%(value)d/%(max_value)d]'), " ", progressbar.ETA()]
        bar = progressbar.ProgressBar(widgets=widgets, max_value=total_rows, redirect_stdout=True).start()

        for i, row in enumerate(rows[1:]):
            columns = str(row).split(",")

            name = columns[1][:-1]
            ip = columns[2][:-1]
            mac_address = columns[12]
            raw_mac_address = get_raw_mac_address(mac_address)
            mac_address = convert_mac_address(raw_mac_address, separation_character)
            if api:
                output += f"'Name: {name}', 'IP-Address: {ip}', 'MAC-Address: {mac_address.lower() if lower is True else mac_address}', 'Vendor: {get_mac_address_vendor(raw_mac_address, api_token)}'\n"
                if not api_token:
                    sleep(0.9)
                else:
                    sleep(0.15)
            else:
                output += f"'Name: {name}', 'IP-Address: {ip}', 'MAC-Address: {mac_address.lower() if lower is True else mac_address}'\n"
            bar.update(i + 1)
        bar.finish()
        output_str = ''.join(str(line) for line in output)
        if output_to_file:
            write_file(output_str)
        else:
            print("\nOutput:\n" + output_str, sep=",\n")
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
            logger.debug("Fetched commandline arguments.")
        except SystemExit:  # This exception is raised when -h or --help is called and help is printed
            logger.debug("Exiting. User entered '-h/--help'")
            exit()
        except Exception as e:
            logger.error(f"Error parsing arguments: {e}\nUsing interactive mode instead")
    else:
        logger.info("No arguments provided. Using interactive mode.")

    # Define logging level depending on verbosity
    if args.verbose_boolean:
        logger.setLevel(logging.DEBUG)
    elif args.quiet_boolean:
        logger.setLevel(logging.WARNING)
    else:
        logger.setLevel(logging.INFO)

    if cli_args_given:
        separation_character: str = args.separation_character
        if args.lower_boolean:
            logger.debug("Output MAC-Address will be lower-cased.")
            lower = True
        if args.api_boolean:
            logger.debug("Every Vendor of all MAC-Addresses will be fetched.")
            api = True
        if args.output_boolean:
            logger.debug("The output will be written to a file instead of stdout.")
            output = True
        if args.file:
            logger.debug("The input of MAC-Addresses will be a file.")
            print("The supported file format is only csv files exported from the 'Advanced IP Scanner' (https://www.advanced-ip-scanner.com/de/). It's language independent.")
            file = True
            handle_file(separation_character, api, lower, None, output)
        else:
            mac_address: str = args.mac_address

        if args.api_token is not None and file:
            logger.debug("The passed API Token will be used.")
            handle_file(separation_character, api, lower, args.api_token, output)

    else:
        mac_address = input("Enter a MAC-Address: ")
        separation_character = input("Enter the separation character: ")
        if input("Get Vendor of MAC-Address by API? [Y/n]:").lower() == "y":
            api = True
            logger.debug("MAC-Address API Lookup activated.")

    raw_mac_address = get_raw_mac_address(mac_address)
    mac_address = convert_mac_address(raw_mac_address, separation_character)
    if api:
        vendor = get_mac_address_vendor(raw_mac_address, None)
        print(f"MAC Address: {mac_address.lower() if lower is True else mac_address}\nVendor: {vendor}")
    else:
        print(f"MAC Address: {mac_address.lower() if lower is True else mac_address}")


if __name__ == "__main__":
    logger = get_logger()
    main()
