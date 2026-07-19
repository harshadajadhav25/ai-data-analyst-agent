import json

from src.utils import (
    clean_generated_code,
    clean_json_response,
    normalize_pandas_frequency_aliases
)


MODEL_NAME = "openai/gpt-oss-20b"


def validate_question(
    client,
    question,
    dataframe,
    conversation_context
):
    """
    Validate whether the user's question can be answered
    using the uploaded dataset and conversation context.
    """

    columns = list(
        dataframe.columns
    )

    data_types = (
        dataframe
        .dtypes
        .astype(str)
        .to_dict()
    )

    prompt = f"""
You are validating a data analysis question.

Dataset columns:

{columns}

Column data types:

{data_types}

Previous conversation:

{conversation_context}

Current question:

{question}

Determine whether the question can reasonably
be answered from this dataset.

Consider that the current question may be
a follow-up to the previous conversation.

Return ONLY valid JSON:

{{
    "can_answer": true,
    "message": ""
}}

If the requested information is clearly
not available:

{{
    "can_answer": false,
    "message": "Brief explanation of what information is missing."
}}

Rules:

1. Consider semantic matches between the user's
   wording and dataset column names.

2. Do not invent columns.

3. General questions such as
   "summarize the dataset" are valid.

4. Follow-up questions are valid when the
   previous conversation provides context.

5. Return JSON only.
"""

    response = (
        client
        .chat
        .completions
        .create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You validate whether questions "
                        "can be answered from dataset schemas."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model=MODEL_NAME
        )
    )

    response_text = (
        response
        .choices[0]
        .message
        .content
    )

    response_text = clean_json_response(
        response_text
    )

    return json.loads(
        response_text
    )


def generate_pandas_code(
    client,
    question,
    dataframe,
    conversation_context
):
    """
    Generate a single Pandas expression
    that answers the user's question.
    """

    dataset_info = f"""
Columns:

{list(dataframe.columns)}

Data types:

{dataframe.dtypes.astype(str).to_dict()}

Dataset size:

{dataframe.shape[0]} rows
{dataframe.shape[1]} columns

Sample data:

{dataframe.head(5).to_string()}
"""

    prompt = f"""
You are InsightAI,
an expert Python Pandas data analyst.

A Pandas DataFrame named df already exists.

Pandas is available using the name pd.

Dataset:

{dataset_info}

Previous conversation:

{conversation_context}

Current question:

{question}

Generate ONE Python Pandas expression
that answers the CURRENT question.

Rules:

1. Use only the DataFrame df.

2. Pandas is available as pd.

3. Do not import anything.

4. Do not read or write files.

5. Do not use print().

6. Do not access the operating system.

7. Return only ONE Python expression.

8. Do not include Markdown.

9. Only use columns that exist.

10. Handle missing values appropriately.

11. Do not invent values.

12. For rankings and averages,
    exclude missing values when appropriate.

13. For a distribution request,
    return the relevant numeric Series
    or DataFrame.

14. For comparisons and trends,
    return a Series or DataFrame containing
    the relevant results.

15. For dates use:

pd.to_datetime(
    df["column_name"],
    errors="coerce"
)

16. Pandas date frequency rules:

For resample() or pd.Grouper():

Monthly = ME
Quarterly = QE
Yearly = YE

Examples:

df.resample("ME")
pd.Grouper(freq="ME")

For Period operations using to_period():

Monthly = M
Quarterly = Q
Yearly = Y

Examples:

.dt.to_period("M")
.dt.to_period("Q")
.dt.to_period("Y")

Never use ME, QE, or YE inside to_period().

17. Resolve follow-up questions using
    previous conversation context.

18. The final result must be returned
    by the expression.
"""

    response = (
        client
        .chat
        .completions
        .create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate safe modern Pandas "
                        "expressions for data analysis."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model=MODEL_NAME
        )
    )

    generated_code = (
        response
        .choices[0]
        .message
        .content
    )

    generated_code = clean_generated_code(
        generated_code
    )

    generated_code = (
        normalize_pandas_frequency_aliases(
            generated_code
        )
    )

    return generated_code


def generate_explanation(
    client,
    question,
    result,
    conversation_context
):
    """
    Generate a concise natural-language explanation
    for the Pandas analysis result.
    """

    result_text = str(
        result
    )[:5000]

    prompt = f"""
You are InsightAI,
an expert data analyst.

Previous conversation:

{conversation_context}

Current question:

{question}

Analysis result:

{result_text}

Explain the result.

Rules:

1. Answer the current question directly.

2. Use simple language.

3. Mention important patterns.

4. Do not invent information.

5. Keep the response concise.
"""

    response = (
        client
        .chat
        .completions
        .create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You explain data analysis "
                        "results clearly."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model=MODEL_NAME
        )
    )

    return (
        response
        .choices[0]
        .message
        .content
    )