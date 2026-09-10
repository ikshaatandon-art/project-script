"""
Simple Python script that generates and prints numbers from 1 to 1000.
Can be executed directly via command line or imported into a web application.
"""

def print_numbers(start=1, end=1000):
    """Prints numbers from start to end in the console."""
    print(f"--- Starting sequence from {start} to {end} ---")
    for i in range(start, end + 1):
        print(f"Number: {i}")
    print("--- Sequence Completed Successfully ---")

def get_numbers_list(start=1, end=1000):
    """Returns numbers from start to end as a list of strings."""
    return [f"Number {i}" for i in range(start, end + 1)]

if __name__ == "__main__":
    print_numbers(1, 1000)
