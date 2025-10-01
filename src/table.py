import streamlit as st
from src.utils import get_step2loc, create_df_steps
import pandas as pd
# from src.lslayers import extract_vial_dict_from_step, convert_string_to_dict
from src.utils import extract_vial_dict_from_step, convert_string_to_dict
# from src.lslayers import get_row_col_dict
from src.utils import get_row_col_dict
import numpy as np
import re

def display_table():
        
    if type(st.session_state.current_steps) == pd.core.frame.DataFrame:
        with st.sidebar:
            st.markdown("current final steps")
            df_steps = create_df_steps(st.session_state.current_steps)
            steps, step2loc = get_step2loc(df_steps.description.values)

            edited_df = st.data_editor(
                    df_steps,
                    hide_index=True,
                )

            with st.form(key='final_steps'):

                # response = AgGrid(
                # df_steps,
                # height=200,
                # gridOptions=gridoptions,
                # enable_enterprise_modules=True,
                # update_mode=GridUpdateMode.MODEL_CHANGED,
                # data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                # fit_columns_on_grid_load=False,
                # header_checkbox_selection_filtered_only=True,
                # use_checkbox=True)

                # v = response['selected_rows']

                vials_df = pd.DataFrame(np.full((8, 12), np.nan), 
                            index=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'],
                            columns=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'])
                
                # first_level_choice =  st.selectbox('', (range(1, len(df_steps)+1)))
                first_level_choice =  st.selectbox('', steps )
                # if v is not None:
                #     # print("v index:", int(v.index.item()) )
                #     first_level_choice =  int(v.index.item())
                # else: 
                #     first_level_choice=0

                # print("keys:", first_level_choice)

                submit_button = st.form_submit_button(label='Update Table')
                def color_survived(val):
                    if np.isnan(val):
                        color = '#787779'  # Default color for NaN
                    elif val < 0:
                        color = '#ff3131'  # Red color for negative values
                    else:
                        color = '#2a895c'  # Green color for non-NaN values
                    return f'background-color: {color}'
                    
                # need to modify function so that it will parse the transfer dict correctly - get_step2loc and second dataframe visual
                # need to keep track of which plate things are happening in
                # show 1 at a time unless it is a transfer step, if transfer step show 2
                step = df_steps.loc[step2loc[first_level_choice], 'description']
                # step = df_steps.iloc[first_level_choice, 'description']
                if 'transfer' in step:
                    vials_df2 = pd.DataFrame(np.full((8, 12), np.nan), 
                            index=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'],
                            columns=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'])
                    # get the dictionary from the tranfser step
                    result_dict = extract_vial_dict_from_step(step)
                    # since this is a string but contains a list, we cannot parse it the same. The code below properly extracts the list from the string
                    pattern = r'(\w+):\[\s*(\w+)\s*,\s*([^]]+)\s*\]'
                    matches = re.findall(pattern, result_dict)
                    d = {}
                    # Iterate over the matches and populate the dictionary
                    for match in matches:
                        key = match[0]
                        # only get the number from the string
                        match2 = re.search(r"[\d.]+", match[2])
                        value = [match[1], match2[0]]
                        if key in d:
                            d[key].append(value)
                        else:
                            d[key] = [value]
                    CH2rowcol = get_row_col_dict()
                    d2 = {k:CH2rowcol[k] for k,v in d.items()}
                    for k, v in d2.items():
                        for value in d[k]:
                            row = d2[k]['Row'] - 1
                            col = d2[k]['Column'] - 1
                            vials_df.iloc[row, col] = "-" + value[1]
                            # need to get the second plate wells out of the value dict
                            position = value[0]
                            row2 = CH2rowcol[position]['Row'] - 1
                            col2 = CH2rowcol[position]['Column'] - 1
                            vials_df2.iloc[row2, col2] = value[1]
                    vials_df = vials_df.fillna(-1)
                    # Replace the placeholder value back to NaN
                    vials_df = vials_df.replace(-1, np.nan)
                    # Cast filled DataFrame to float
                    vials_df = vials_df.astype(float)


                    vials_df2 = vials_df2.fillna(-1)
                    # Replace the placeholder value back to NaN
                    vials_df2 = vials_df2.replace(-1, np.nan)
                    # Cast filled DataFrame to float
                    vials_df2 = vials_df2.astype(float)
                    st.dataframe(vials_df.style.applymap(color_survived).format("{:.2f}"))
                    st.dataframe(vials_df2.style.applymap(color_survived).format("{:.2f}"))
                else:
                    d = convert_string_to_dict(extract_vial_dict_from_step(step))
                    d = {k:float(v) for k,v in d.items()}
                    CH2rowcol = get_row_col_dict()
                    d2 = {k:CH2rowcol[k] for k,v in d.items()}
                    for k,v in d2.items():
                        value = d[k]
                        row = d2[k]['Row']-1
                        col = d2[k]['Column']-1
                        vials_df.iloc[row, col] = value

                    vials_df = vials_df.fillna(-1)
                    # Replace the placeholder value back to NaN
                    vials_df = vials_df.replace(-1, np.nan)
                    st.dataframe(vials_df.style.applymap(color_survived).format("{:.2f}"))

