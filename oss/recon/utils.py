from colorama import Fore, Style, init

init(autoreset=True)

def print_info(msg):
    print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} {msg}")

def print_success(msg):
    print(f"{Fore.GREEN}[+]{Style.RESET_ALL} {msg}")

def print_error(msg):
    print(f"{Fore.RED}[-]{Style.RESET_ALL} {msg}")

def print_warning(msg):
    print(f"{Fore.YELLOW}[WARN]{Style.RESET_ALL} {msg}")

def print_result(header, result):
    print(f"{Fore.MAGENTA}[RESULT]{Style.RESET_ALL} {header}:\n{result}")
