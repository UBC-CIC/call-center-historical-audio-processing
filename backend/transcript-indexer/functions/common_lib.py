import logging
import random
import string

logging.basicConfig()
logger = logging.getLogger()

"""
Contains helper functions only, not a lambda function file
"""


def find_duplicate_person(people):
    """
    Obtains duplicate list of people in the given Amazon Comprehend entities list
    :param people: List of entities as returned by Amazon Comprehend
    :return: duplicate people entities in the input people list

    TODO: try to improve the performance for this
    """
    duplicates = []
    for i, person in enumerate(people):
        for j in range(i + 1, len(people)):
            if person in people[j]:
                if person not in duplicates:
                    duplicates.append(person)
                logger.info("found " + person + " in " + people[j])
            if people[j] in person:
                logger.info("found " + people[j] + " in " + person)
                if people[j] not in duplicates:
                    duplicates.append(people[j])
    return duplicates


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """
    Random string generator using uppercase letters and digits

    """
    return ''.join(random.choice(chars) for _ in range(size))
