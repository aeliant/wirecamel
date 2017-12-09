# coding=utf-8

# HEADER = '\033[95m'
# OKBLUE = '\033[94m'


def checked(text):
    print("[\033[94m+\033[0m] {}".format(text))


def not_checked(text):
    print("[\033[91m×\033[0m] {}".format(text))


def loading(text):
    print("[\033[93m*\033[0m] {}".format(text))


def underline(text):
    print("\033[4m{}\033[0m".format(text))


def bold(text):
    print("\033[1m{}\033[0m".format(text))


def fail(text):
    print("\033[91m{}\033[0m\n".format(text))


def success(text):
    print("\033[92m{}\033[0m".format(text))


def warning(text):
    print("\033[93m{}\033[0m".format(text))


# Printing function
def print_call_info(return_code, process_name, text):
    if return_code != 0:
        not_checked("A problem occured with {}. Aborting".format(process_name))
        exit(1)
    else:
        checked(text)
