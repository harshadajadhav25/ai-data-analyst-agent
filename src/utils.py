import re
import hashlib

import pandas as pd


def clean_generated_code(code):
    """
    Remove Markdown formatting from AI-generated Python code.
    """

    code = code.strip()

    code = re.sub(
        r"```python",
        "",
        code,
        flags=re.IGNORECASE
    )

    code = code.replace("```", "")

    return code.strip()


def clean_json_response(response_text):
    """
    Remove Markdown formatting from AI-generated JSON.
    """

    response_text = response_text.strip()

    response_text = re.sub(
        r"```json",
        "",
        response_text,
        flags=re.IGNORECASE
    )

    response_text = response_text.replace("```", "")

    return response_text.strip()


def normalize_pandas_frequency_aliases(code):
    """
    Normalize Pandas frequency aliases based on context.

    Pandas uses different aliases for resampling
    and Period operations.

    Examples:
    - resample("ME")       -> Month-end resampling
    - to_period("M")       -> Monthly Period
    - resample("QE")       -> Quarter-end resampling
    - to_period("Q")       -> Quarterly Period
    - resample("YE")       -> Year-end resampling
    - to_period("Y")       -> Yearly Period
    """

    # --------------------------------------------------
    # Fix resample frequency aliases
    # --------------------------------------------------

    code = re.sub(
        r'\.resample\(\s*["\']M["\']\s*\)',
        '.resample("ME")',
        code
    )

    code = re.sub(
        r'\.resample\(\s*["\']Q["\']\s*\)',
        '.resample("QE")',
        code
    )

    code = re.sub(
        r'\.resample\(\s*["\']Y["\']\s*\)',
        '.resample("YE")',
        code
    )


    # --------------------------------------------------
    # Fix pd.Grouper frequency aliases
    # --------------------------------------------------

    code = re.sub(
        r'freq\s*=\s*["\']M["\']',
        'freq="ME"',
        code
    )

    code = re.sub(
        r'freq\s*=\s*["\']Q["\']',
        'freq="QE"',
        code
    )

    code = re.sub(
        r'freq\s*=\s*["\']Y["\']',
        'freq="YE"',
        code
    )


    # --------------------------------------------------
    # Fix Period aliases
    # Period requires M/Q/Y rather than ME/QE/YE
    # --------------------------------------------------

    code = re.sub(
        r'\.to_period\(\s*["\']ME["\']\s*\)',
        '.to_period("M")',
        code
    )

    code = re.sub(
        r'\.to_period\(\s*["\']QE["\']\s*\)',
        '.to_period("Q")',
        code
    )

    code = re.sub(
        r'\.to_period\(\s*["\']YE["\']\s*\)',
        '.to_period("Y")',
        code
    )

    return code


def is_safe_code(code):
    """
    Perform a basic safety check on
    AI-generated Pandas code.
    """

    blocked_terms = [
        "import ",
        "__",
        "open(",
        "exec(",
        "eval(",
        "compile(",
        "os.",
        "sys.",
        "subprocess",
        "socket",
        "requests",
        "pathlib",
        "shutil"
    ]

    code_lower = code.lower()

    for term in blocked_terms:
        if term.lower() in code_lower:
            return False

    return True


def get_file_identifier(uploaded_file):
    """
    Generate a unique identifier for an uploaded file.
    """

    file_bytes = uploaded_file.getvalue()

    return hashlib.md5(
        file_bytes
    ).hexdigest()


def convert_result_to_dataframe(result):
    """
    Convert a Pandas analysis result into
    a DataFrame for visualization.
    """

    if isinstance(result, pd.DataFrame):
        return result.reset_index()

    if isinstance(result, pd.Series):
        return result.reset_index()

    return None