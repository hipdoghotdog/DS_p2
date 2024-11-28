import random

# List of fortunes
FORTUNES = [
    "You will have a great day!",
    "A new opportunity is on the horizon.",
    "Good fortune is coming your way.",
    "An unexpected event will bring joy.",
    "You will achieve your goals soon.",
]

def get_random_fortune():
    """Returns a random fortune from the list."""
    return random.choice(FORTUNES)