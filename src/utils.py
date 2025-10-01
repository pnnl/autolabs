import pickle
# from .create_lslibrary import get_exp_steps
# from .lslayers import extract_vial_dict_from_step, convert_string_to_dict
import errno
import os
from datetime import datetime
import re
import logging
from bs4 import BeautifulSoup



def get_exp_steps(steps_text):
    """
    Get the steps from the text of the steps
    Uses BeautifulSoup to parse the XML based on the tags that were used in the GPT-4O prompt/response. 
    """
    soup = BeautifulSoup(steps_text, features="lxml")
    steps_ = soup.find_all('final-steps')
    steps = steps_[-1]
    

    try:
        children = steps.findChildren("step" , recursive=False)
    except:
        return None
    
    steps = [child for child in children]
    logging.info(f"Got the experiment steps.")
    return steps

def save_steps(chat_history):
    if 'final-steps' in chat_history[-1]["content"]:
        with open('current_steps.pkl', 'wb') as f:
            pickle.dump( {'steps': chat_history[-1],
                          }, f)
        
def save_tags_txt():
    data = [{'Add naphthalene to vials in Plate1. {A1: 5, A2: 10, A3: 15, A4: 20, B1: 25, B2: 30, B3: 40, B4: 50}': ['Powder']}, {'Set Cap vials in Plate1. {A1: 1, A2: 1, A3: 1, A4: 1, B1: 1, B2: 1, B3: 1, B4: 1}': ['Processing', 'ScrewCap']}, {'Set VortexRate in vials in Plate1. {A1: 1, A2: 1, A3: 1, A4: 1, B1: 1, B2: 1, B3: 1, B4: 1}': ['Processing']}, {'Set Delay to 10 min in vials in Plate1. {A1: 10, A2: 10, A3: 10, A4: 10, B1: 10, B2: 10, B3: 10, B4: 10}': ['Processing']}, {'Add 5 ul from Plate1 to Plate2. {A1:a2, A2:b3, A3:a3}' : ['ExtSingleTip', 'SyringePump']}]

    with open('multiplate-tags.pkl', 'wb') as f:
        pickle.dump(data, f)
def save_steps_txt():
    with open('multiplate-steps.pkl', 'wb') as f:
        pickle.dump({  "steps": {"content": "<final-steps>\n<step>Add naphthalene to vials in Plate1. {A1: 5, A2: 10, A3: 15, A4: 20, B1: 25, B2: 30, B3: 40, B4: 50}</step>\n<step>Set Cap vials in Plate1. {A1: 1, A2: 1, A3: 1, A4: 1, B1: 1, B2: 1, B3: 1, B4: 1}</step>\n<step>Set VortexRate in vials in Plate1. {A1: 1, A2: 1, A3: 1, A4: 1, B1: 1, B2: 1, B3: 1, B4: 1}</step>\n<step>Set Delay to 10 min in vials in Plate1. {A1: 10, A2: 10, A3: 10, A4: 10, B1: 10, B2: 10, B3: 10, B4: 10}</step>\n<step>Add 5 ul from Plate1 to Plate2. {A1:a2, A2:b3, A3:a3}</step>\n</final-steps>"}}, f)

def df2dict(df):
    d = {}
    for CH in df.index:
        for i in df.columns:
            d.update({f'{CH}{i}': df.loc[CH, i] })
    return d

def convert_string_to_dict(s):
    # Remove the outer curly braces
    s = s.strip('{}')
    
    # Split the string into key-value pairs
    items = s.split(',')
    
    # Initialize an empty dictionary
    dictionary = {}
    
    for item in items:
        if ':' in item:
            key, value = item.split(':')
            key = key.replace(' ', '')
        
            # Keep the entire value as a string
            dictionary[key.strip()] = value
    
    return dictionary

def extract_vial_dict_from_step(step_text):
        
    # s = step.get_text()
    pattern = r'\{([^}]+)\}'
    
    # Find all matches in the text
    matches = re.findall(pattern, step_text)

    if len(matches) > 0:
        return matches[0]
    else:
        return ""
    
def check_dict_value_correctness(final_resp):
        
    correct_dict = True
    steps = get_exp_steps(final_resp)

    if not steps or steps == None:
        return False

    for s in steps:
        text = s.get_text()
        d = convert_string_to_dict(extract_vial_dict_from_step(text))
        v = list(d.values())

        for i in v:
            try:
                float(i)
            except:
                correct_dict=False

    return correct_dict





# utils for displaying the final steps

def get_step_text(step):
    loc = step.find('{')
    step_text = step[:loc]
    return step_text


def get_step2loc(all_steps):
    steps = [get_step_text(i) for i in all_steps]
    # adding the step index to create unique steps
    steps = [str(i+1) + '.  ' + s for i, s in enumerate(steps)]
    loc2step = dict(enumerate(steps))
    step2loc = {v:k for k,v in loc2step.items()}
    return steps, step2loc

def create_df_steps(session_state_current_steps):
    # df_steps = st.session_state.current_steps.copy()
    df_steps = session_state_current_steps.copy()
    # df_steps.index = df_steps.index+1
    df_steps.columns = ['description']
    df_steps['step'] = range(1, len(df_steps)+1)
    df_steps = df_steps[['step', 'description']]
    return df_steps


def get_exp_dir():
    mydir = os.path.join(
        os.getcwd(), 
        'experiments',
        datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    try:
        os.makedirs(mydir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise  # This was not a "directory exist" error..
    return mydir

tags_values = [
'ZSample',
 'MoveVial',
 '250uLTip',
 'BalancePictureOnly',
 'SourceTracking',
 'Backsolvent',
 'Manual',
 'LookAhead',
 'Chaser',
 'Powder',
 'Uncap',
 'SyringePump',
 'Filter StepCap',
 'Plate',
 'NewTip',
 'Filter',
 'SkipMap',
 'Filter CompletePress',
 'ScrewCap',
 'ExtSingleTip',
 'Image',
 'PDT',
 '1000uLTip',
 '4Tip',
 '50uLTip',
 '100uLTip',
 '10mLTip',
 'StartReactionTimer',
 'Hover',
 'Analysis',
 'Wait',
 'CapAfterDispense',
 'Processing',
 'HPTare',
 'DestinationTracking',
 'Filter StepPartialPress',
 'HighResPictureOnly',
 'StartVialTimer',
 'WaitVialTimer',
 'Notify' 
 '',
 ]

def print_pkl(filename):
    if "tag" in filename:
        
        with open(filename, 'rb') as f:
            data = pickle.load(f)
            data = data[0]
    else:
        with open(filename, 'rb') as f:
            data = pickle.load(f)
            data = data["steps"]["content"]
    return data
def clean_tag(tag):

    tag = tag.replace(' ','')
    tag = re.sub(r'\W+', '', tag)
    
    return(tag)

from collections import defaultdict
def get_row_col_dict():
        
    CH_key_to_rowcol = defaultdict()
    row_count=1
    for CH in ["A", "B", "C", "D", "E", "F", "G", "H"]:
        for col in range(1, 13):
            key = f'{CH}{col}'
            row = row_count
            col = col
    
            val = {'Row': row, 'Column': col}
            # print(key, val)
            CH_key_to_rowcol[key] = val
        row_count+=1
    return CH_key_to_rowcol


tags_values = ['ZSample',
 'MoveVial',
 '250uLTip',
 'BalancePictureOnly',
 'SourceTracking',
 'Backsolvent',
 'Manual',
 'LookAhead',
 'Chaser',
 'Powder',
 'Uncap',
 'SyringePump',
 'Filter StepCap',
 'Plate',
 'NewTip',
 'Filter',
 'SkipMap',
 'Filter CompletePress',
 'ScrewCap',
 'ExtSingleTip',
 'Image',
 'PDT',
 '1000uLTip',
 '4Tip',
 '50uLTip',
 '100uLTip',
 '10mLTip',
 'StartReactionTimer',
 'Hover',
 'Analysis',
 'Wait',
 'CapAfterDispense',
 'Processing',
 'HPTare',
 'DestinationTracking',
 'Filter StepPartialPress',
 'HighResPictureOnly']


if __name__ == '__main__':
    # print(print_pkl('tag_options.pkl'))
    # print(print_pkl('multiarraytest-tags.pkl'))
    save_tags_txt()
    save_steps_txt()

