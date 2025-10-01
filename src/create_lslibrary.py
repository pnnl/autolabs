import pandas as pd
from bs4 import BeautifulSoup
import sys
from .lschemicals import create_LSChemicals
from .lsparams import create_LSParameters

# from lslayers import create_LSlayers
from .lslayers2 import create_LSlayers

# from .correct_steps import get_new_steps
import pickle
from .chem_utils import get_chem_name

# from .config import get_client
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from .config import Client

_client = Client("unfiltered")


def str2dict(input_str):

    pairs = input_str.split(",")

    # Initialize an empty dictionary
    output_dict = {}

    # Iterate over the pairs and split by ': ' to separate keys and values
    for pair in pairs:
        key, value = pair.split(":")
        output_dict[key] = float(value)

    return output_dict


def get_exp_steps(steps_text):
    """
    Get the steps from the text of the steps
    Uses BeautifulSoup to parse the XML based on the tags that were used in the GPT-4O prompt/response.
    """
    soup = BeautifulSoup(steps_text, features="lxml")
    steps_ = soup.find_all("final-steps")
    steps = steps_[-1]

    try:
        children = steps.findChildren("step", recursive=False)
    except:
        return None

    steps = [child for child in children]
    logging.info(f"Got the experiment steps.")
    return steps


def get_used_vials(vial_dicts):

    used_vials = []
    for v in vial_dicts:
        used_vials += list(v.keys())

    return used_vials


def create_tmp_tag_file(steps):
    tmp_tags = []
    for i in steps:
        t = i.get_text()
        tmp_tags.append({t: ["Processing"]})
    with open("tmp/tag_options.pkl", "wb") as f:
        pickle.dump(tmp_tags, f)

    # return tmp_tags
