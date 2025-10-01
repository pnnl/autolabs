from dotenv import load_dotenv
import os
import openai
import ast
import re

# from lslayers import extract_vial_dict_from_step
# from create_lslibrary import get_exp_steps

load_dotenv()
API_KEY = os.environ.get("CLOUD_LLM_API_KEY")
client = openai.OpenAI(api_key=API_KEY, base_url="https://ai-incubator-api.pnnl.gov")


def extract_vial_dict_from_step(step_text):

    # s = step.get_text()
    pattern = r"\{([^}]+)\}"

    # Find all matches in the text
    matches = re.findall(pattern, step_text)

    if len(matches) > 0:
        return matches[0]
    else:
        return ""


def find_the_used_vials(steps):
    items = []
    for s in steps:
        a = extract_vial_dict_from_step(s.get_text())
        a = a.split(",")
        items.extend(a)

    keys = [i.split(":")[0].strip() for i in items]
    keys = list(set(keys))
    if "" in keys:
        keys.remove("")

    return keys


def find_value_unit_in_step(step_text):

    if "cap" in step_text.lower():
        v, u = 1, "BINARY"
        return v, u

    else:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"return only the value and the unit in the text as a comma seperated list. text: {step_text} ",
                }
            ],
        )

        rsp = response.choices[0].message.content
        print(rsp)
        rsp = rsp.strip("[]")
        print(rsp)
        # if 'stir' not in step_text.lower():

        if "stir" in step_text.lower() or "delay" in step_text.lower():
            try:
                v, u = rsp.split(",")
                return v, u
            except:
                v, u = rsp.split(" ")
                return v, u
        else:
            v, u = rsp.split(",")
            return v, u


def get_new_value_dict(keys, value):
    d_new = {}
    for k in keys:
        d_new.update({k: value})
    return d_new


def remove_slash_n(text):
    if "\n" in text:
        return text.replace("\n", "")
    else:
        return text


def get_new_step(step, steps):
    keys = find_the_used_vials(steps)

    step_text = step.get_text()
    a = extract_vial_dict_from_step(step_text)

    if a == "":
        value, unit = find_value_unit_in_step(step_text)
        d_new = get_new_value_dict(keys, value)
        new_text = step_text + f" in vials {d_new}"
        new_text = remove_slash_n(new_text)
    else:
        step_text = remove_slash_n(step_text)

    return step_text


def get_new_steps(steps):
    keys = find_the_used_vials(steps)

    new_steps = []
    for s in steps:
        step_text = s.get_text()
        a = extract_vial_dict_from_step(step_text)

        if a == "":
            value, unit = find_value_unit_in_step(step_text)
            d_new = get_new_value_dict(keys, value)
            new_text = step_text + f" in vials {d_new}"
            new_text = remove_slash_n(new_text)
            new_steps.append(new_text)
        else:
            step_text = remove_slash_n(step_text)
            new_steps.append(step_text)

    return new_steps
