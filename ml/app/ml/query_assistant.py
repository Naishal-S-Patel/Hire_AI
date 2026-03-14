import re


def parse_query(query):

    numbers = re.findall(r"\d+", query)

    experience = int(numbers[0]) if numbers else None

    return {
        "experience_min": experience
    }