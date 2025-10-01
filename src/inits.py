import streamlit as st
from .utils import get_exp_dir
from langgraph.checkpoint.memory import InMemorySaver, MemorySaver


def init():

    # initialize chat session in streamlit if not already present
    if "chemicals" not in st.session_state:
        st.session_state.chemicals = ""
    if "parameters" not in st.session_state:
        st.session_state.parameters = ""

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "query_experiment" not in st.session_state:
        st.session_state["query_experiment"] = False

    if "iteration_count" not in st.session_state:
        st.session_state.iteration_count = 0

    if "use_current_steps" not in st.session_state:
        st.session_state.use_current_steps = False

    if "user_input_counter" not in st.session_state:
        st.session_state.user_input_counter = 0

    if "array_dim" not in st.session_state:
        st.session_state.array_dim = None
    # print('1')

    # if 'vials_df' not in st.session_state:
    #     # print('here!')
    #     st.session_state.vials_df = pd.DataFrame(np.zeros((6,8)),
    #                                     index=['A', 'B', 'C', 'D', 'E', 'F'],
    #                                     columns=['1', '2', '3', '4', '5', '6', '7', '8'])

    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if "user_prompt" not in st.session_state:
        st.session_state.user_prompt = ""

    if "tag_counter" not in st.session_state:
        st.session_state.tag_counter = 0

    # if 'audio_model' not in st.session_state:
    #     st.session_state["audio_model"] =  whisper.load_model("whisper/base.pt")

    if "tag_options" not in st.session_state:
        st.session_state.tag_options = []

    if "speech_on" not in st.session_state:
        st.session_state.speech_on = False

    if "checks_off" not in st.session_state:
        st.session_state.checks_off = False

    if "unfiltered_on" not in st.session_state:
        st.session_state.unfiltered_on = False

    if "refine_button_clicked" not in st.session_state:
        st.session_state.refine_button_clicked = False

    if "VIALS_REFINED" not in st.session_state:
        st.session_state.VIALS_REFINED = 0

    if "step_text" not in st.session_state:
        st.session_state.step_text = None

    if "current_steps" not in st.session_state:
        st.session_state.current_steps = None

    if "exp_dir" not in st.session_state:
        st.session_state.exp_dir = get_exp_dir()

    if "work_on_optional_tags" not in st.session_state:
        st.session_state.work_on_optional_tags = False

    if "tags_finalized" not in st.session_state:
        st.session_state.tags_finalized = False

    if "memory" not in st.session_state:
        st.session_state["memory"] = InMemorySaver()

    if "use_reflection" not in st.session_state:
        st.session_state.use_reflection = False

    if "rewrite_user_query" not in st.session_state:
        st.session_state.rewrite_user_query = False

    if "redo_calculations" not in st.session_state:
        st.session_state.redo_calculations = False

    # if 'use_tools' not in st.session_state:
    #     st.session_state.use_tools = True

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = 0

    if "self_checks_done" not in st.session_state:
        st.session_state.self_checks_done = False

    if "use_processing_steps_rag" not in st.session_state:
        st.session_state.use_processing_steps_rag = False


def init_graph_variables(
    use_self_checks,
    use_self_checks_reasoning,
    use_tools,
    use_reflection=False,
    redo_calculations=False,
):

    st.session_state.use_self_checks = use_self_checks
    st.session_state.use_self_checks_reasoning = use_self_checks_reasoning
    st.session_state.use_tools = use_tools
    st.session_state.use_reflection = use_reflection
    st.session_state.redo_calculations = redo_calculations

    if use_reflection:
        st.session_state.reflection_count = 0

    if redo_calculations:
        st.session_state.n_redone = 0

    # st.session_state.current_steps_text

    # if 'level1_option' not in st.session_state:
    #     st.session_state.level1_option = None

    # for op in range(1,9):
    #     if not f'op{op}' in st.session_state:
    #         st.session_state[f'op{op}'] = False
