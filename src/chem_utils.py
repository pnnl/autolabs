def get_chem_name(client_completer, s):
    messages=[
        {"role":"system", "content": f'Return only the chemical name in this if there is a chemical name. Water is also a chemical for this purpose. Do not change it. If there is no chemical name return None.\n {s} '
        }]
    response = client_completer.get_chat_completions(messages) 
    response = response.choices[0].message.content

    chem_name = response

    return chem_name