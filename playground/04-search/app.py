"""A tiny application used by the search exercise."""

from helpers import format_name


def main():
    # TODO: load the user list from users.json
    name = format_name("ada", "lovelace")
    print(f"{name} checked in")


if __name__ == "__main__":
    main()
