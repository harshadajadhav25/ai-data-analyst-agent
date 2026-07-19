import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from src.data_cleaning import clean_dataset
from src.ai_agent import (
    validate_question,
    generate_pandas_code,
    generate_explanation
)
from src.visualization import (
    generate_visualization_plan,
    create_dynamic_chart
)
from src.utils import (
    get_file_identifier,
    is_safe_code,
    convert_result_to_dataframe
)


# ==================================================
# ENVIRONMENT SETUP
# ==================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

client = (
    Groq(api_key=api_key)
    if api_key
    else None
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="InsightAI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================================
# LOAD CUSTOM CSS
# ==================================================

def load_css():
    try:
        with open(
            "styles/style.css",
            "r",
            encoding="utf-8"
        ) as css_file:

            st.markdown(
                f"<style>{css_file.read()}</style>",
                unsafe_allow_html=True
            )

    except FileNotFoundError:
        st.warning(
            "Custom style file was not found."
        )


load_css()


# ==================================================
# SESSION STATE
# ==================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_file_id" not in st.session_state:
    st.session_state.current_file_id = None

if "last_generated_code" not in st.session_state:
    st.session_state.last_generated_code = None

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


# ==================================================
# HELPERS
# ==================================================

def get_conversation_context():
    """
    Return recent conversation history.
    """

    if not st.session_state.messages:
        return "No previous conversation."

    recent_messages = (
        st.session_state.messages[-6:]
    )

    context = []

    for message in recent_messages:

        role = message.get(
            "role",
            ""
        )

        content = message.get(
            "content",
            ""
        )

        context.append(
            f"{role}: {content}"
        )

    return "\n".join(
        context
    )


def render_result(
    result,
    user_question,
    generated_code
):
    """
    Render a compact analysis result.
    """

    result_df = (
        convert_result_to_dataframe(
            result
        )
    )

    # ----------------------------------------------
    # Visualization
    # ----------------------------------------------

    if (
        result_df is not None
        and not result_df.empty
    ):

        try:

            chart_plan = (
                generate_visualization_plan(
                    client,
                    user_question,
                    result_df
                )
            )

            if chart_plan.get(
                "create_chart",
                False
            ):

                chart = (
                    create_dynamic_chart(
                        result_df,
                        chart_plan
                    )
                )

                st.plotly_chart(
                    chart,
                    use_container_width=True
                )

        except Exception:
            pass


    # ----------------------------------------------
    # Result Data
    # ----------------------------------------------

    if isinstance(
        result,
        pd.DataFrame
    ):

        with st.expander(
            "View Analysis Data"
        ):

            st.dataframe(
                result,
                use_container_width=True
            )

    elif isinstance(
        result,
        pd.Series
    ):

        with st.expander(
            "View Analysis Data"
        ):

            st.dataframe(
                result.to_frame(),
                use_container_width=True
            )

    else:

        st.metric(
            "Result",
            result
        )


    # ----------------------------------------------
    # Technical Details
    # ----------------------------------------------

    with st.expander(
        "Analysis Details"
    ):

        st.code(
            generated_code,
            language="python"
        )


# ==================================================
# HEADER
# ==================================================

st.markdown(
    """
<div class="insight-header">
    <div class="insight-title">📊 InsightAI</div>
    <div class="insight-subtitle">
        Your AI-powered data analyst for instant insights,
        trends, comparisons, and visualizations.
    </div>
</div>
    """,
    unsafe_allow_html=True
)


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-title">'
        '📁 Dataset'
        '</div>',
        unsafe_allow_html=True
    )

    uploaded_file = (
        st.file_uploader(
            "Upload CSV",
            type=["csv"]
        )
    )


# ==================================================
# EMPTY STATE
# ==================================================

if uploaded_file is None:

    st.markdown(
        "## Turn your data into answers"
    )

    st.write(
        "Upload a CSV file and start asking questions "
        "in plain English. InsightAI will analyze your "
        "data, calculate results, generate visualizations, "
        "and explain what the numbers mean."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(
            "📈 **Discover Trends**\n\n"
            "Find patterns and changes over time."
        )

    with col2:
        st.info(
            "🔎 **Explore Insights**\n\n"
            "Ask questions about any metric or category."
        )

    with col3:
        st.info(
            "📊 **Visualize Results**\n\n"
            "Generate charts automatically."
        )

    st.stop()


# ==================================================
# DATASET PROCESSING
# ==================================================

try:

    file_id = (
        get_file_identifier(
            uploaded_file
        )
    )

    if (
        st.session_state.current_file_id
        != file_id
    ):

        st.session_state.messages = []

        st.session_state.last_generated_code = None

        st.session_state.pending_prompt = None

        st.session_state.current_file_id = (
            file_id
        )


    original_df = pd.read_csv(
        uploaded_file
    )


    # ==================================================
    # SIDEBAR DATASET INFO
    # ==================================================

    with st.sidebar:

        st.success(
            "Dataset ready"
        )


        # ----------------------------------------------
        # Dataset Health
        # ----------------------------------------------

        st.markdown(
            '<div class="sidebar-title">'
            'Dataset Health'
            '</div>',
            unsafe_allow_html=True
        )


        total_missing = (
            original_df
            .isnull()
            .sum()
            .sum()
        )


        duplicate_rows = (
            original_df
            .duplicated()
            .sum()
        )


        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Rows",
                original_df.shape[0]
            )

            st.metric(
                "Missing",
                total_missing
            )


        with col2:

            st.metric(
                "Columns",
                original_df.shape[1]
            )

            st.metric(
                "Duplicates",
                duplicate_rows
            )


        # ----------------------------------------------
        # Cleaning
        # ----------------------------------------------

        st.markdown(
            '<div class="sidebar-title">'
            'Data Cleaning'
            '</div>',
            unsafe_allow_html=True
        )


        use_clean_data = (
            st.checkbox(
                "Use cleaned dataset",
                value=True
            )
        )


        if use_clean_data:

            df = clean_dataset(
                original_df
            )

        else:

            df = (
                original_df.copy()
            )


        duplicates_removed = (
            original_df.shape[0]
            - df.shape[0]
        )


        if use_clean_data:

            st.caption(
                f"{duplicates_removed} exact duplicate "
                f"rows removed."
            )


        # ----------------------------------------------
        # Dataset Details
        # ----------------------------------------------

        with st.expander(
            "Dataset Details"
        ):

            st.write(
                "**Columns**"
            )

            st.write(
                list(
                    original_df.columns
                )
            )


            data_types = pd.DataFrame(
                {
                    "Column":
                    original_df.columns,

                    "Data Type":
                    original_df
                    .dtypes
                    .astype(str)
                    .values
                }
            )


            st.write(
                "**Data Types**"
            )

            st.dataframe(
                data_types,
                use_container_width=True
            )


            missing_values = (
                original_df
                .isnull()
                .sum()
            )


            missing_table = pd.DataFrame(
                {
                    "Column":
                    missing_values.index,

                    "Missing Values":
                    missing_values.values
                }
            )


            missing_table = (
                missing_table[
                    missing_table[
                        "Missing Values"
                    ] > 0
                ]
            )


            st.write(
                "**Missing Values**"
            )


            if missing_table.empty:

                st.caption(
                    "No missing values."
                )

            else:

                st.dataframe(
                    missing_table,
                    use_container_width=True
                )


            st.write(
                "**Preview**"
            )

            st.dataframe(
                original_df.head(8),
                use_container_width=True
            )


        # ----------------------------------------------
        # Conversation Controls
        # ----------------------------------------------

        st.markdown(
            '<div class="sidebar-title">'
            'Conversation'
            '</div>',
            unsafe_allow_html=True
        )


        if st.button(
            "Clear Conversation"
        ):

            st.session_state.messages = []

            st.session_state.last_generated_code = None

            st.session_state.pending_prompt = None

            st.rerun()


    # ==================================================
    # MAIN CHAT AREA
    # ==================================================

    st.markdown(
        "### 💬 Chat with your data"
    )

    st.caption(
        "Ask a question or start with one of the suggestions below."
    )


    # ==================================================
    # SUGGESTED PROMPTS
    # ==================================================

    if not st.session_state.messages:

        col1, col2, col3, col4 = (
            st.columns(4)
        )


        with col1:

            if st.button(
                "✨ Summarize dataset"
            ):

                st.session_state.pending_prompt = (
                    "Summarize this dataset and highlight "
                    "the most important insights."
                )


        with col2:

            if st.button(
                "📈 Find key trends"
            ):

                st.session_state.pending_prompt = (
                    "Find the most important trends "
                    "in this dataset."
                )


        with col3:

            if st.button(
                "🏆 Show top results"
            ):

                st.session_state.pending_prompt = (
                    "Show the most important top-performing "
                    "records or categories in this dataset."
                )


        with col4:

            if st.button(
                "🔎 Find patterns"
            ):

                st.session_state.pending_prompt = (
                    "Identify interesting patterns "
                    "or relationships in this dataset."
                )


    # ==================================================
    # DISPLAY CHAT HISTORY
    # ==================================================

    for message in (
        st.session_state.messages
    ):

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )


    # ==================================================
    # INPUT
    # ==================================================

    user_question = (
        st.chat_input(
            "Ask anything about your data..."
        )
    )


    if (
        st.session_state.pending_prompt
        and not user_question
    ):

        user_question = (
            st.session_state.pending_prompt
        )

        st.session_state.pending_prompt = None


    # ==================================================
    # PROCESS QUESTION
    # ==================================================

    if user_question:


        # ----------------------------------------------
        # User Message
        # ----------------------------------------------

        with st.chat_message(
            "user"
        ):

            st.markdown(
                user_question
            )


        conversation_context = (
            get_conversation_context()
        )


        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_question
            }
        )


        # ----------------------------------------------
        # API Check
        # ----------------------------------------------

        if client is None:

            assistant_message = (
                "Groq API key not found. "
                "Please add GROQ_API_KEY "
                "to your .env file."
            )


            with st.chat_message(
                "assistant"
            ):

                st.error(
                    assistant_message
                )


        else:

            try:

                # ==========================================
                # VALIDATE QUESTION
                # ==========================================

                with st.status(
                    "InsightAI is thinking...",
                    expanded=False
                ):

                    validation = (
                        validate_question(
                            client,
                            user_question,
                            df,
                            conversation_context
                        )
                    )


                if not validation.get(
                    "can_answer",
                    True
                ):

                    assistant_message = (
                        validation.get(
                            "message",
                            (
                                "The requested information "
                                "is not available "
                                "in this dataset."
                            )
                        )
                    )


                    with st.chat_message(
                        "assistant"
                    ):

                        st.warning(
                            assistant_message
                        )


                    st.session_state.messages.append(
                        {
                            "role":
                            "assistant",

                            "content":
                            assistant_message
                        }
                    )


                # ==========================================
                # ANALYZE
                # ==========================================

                else:

                    with st.status(
                        "Analyzing your data...",
                        expanded=False
                    ):

                        generated_code = (
                            generate_pandas_code(
                                client,
                                user_question,
                                df,
                                conversation_context
                            )
                        )


                    st.session_state.last_generated_code = (
                        generated_code
                    )


                    if not is_safe_code(
                        generated_code
                    ):

                        raise ValueError(
                            "Generated analysis was "
                            "blocked for safety."
                        )


                    # ======================================
                    # SAFE EVAL ENVIRONMENT
                    # ======================================

                    safe_builtins = {
                        "len": len,
                        "min": min,
                        "max": max,
                        "sum": sum,
                        "round": round,
                        "abs": abs,
                        "sorted": sorted
                    }


                    result = eval(
                        generated_code,
                        {
                            "__builtins__":
                            safe_builtins,

                            "df":
                            df,

                            "pd":
                            pd
                        }
                    )


                    ai_answer = (
                        generate_explanation(
                            client,
                            user_question,
                            result,
                            conversation_context
                        )
                    )


                    # ======================================
                    # DISPLAY RESPONSE
                    # ======================================

                    with st.chat_message(
                        "assistant"
                    ):

                        st.markdown(
                            "#### Insight"
                        )

                        st.markdown(
                            ai_answer
                        )


                        render_result(
                            result,
                            user_question,
                            generated_code
                        )


                    st.session_state.messages.append(
                        {
                            "role":
                            "assistant",

                            "content":
                            ai_answer
                        }
                    )


            except Exception as e:

                with st.chat_message(
                    "assistant"
                ):

                    st.error(
                        "InsightAI could not complete "
                        "the analysis."
                    )

                    st.caption(
                        str(e)
                    )


                    if (
                        st.session_state
                        .last_generated_code
                    ):

                        with st.expander(
                            "Debug Information"
                        ):

                            st.code(
                                st.session_state
                                .last_generated_code,

                                language="python"
                            )


except Exception as e:

    st.error(
        f"Could not load the dataset: {e}"
    )