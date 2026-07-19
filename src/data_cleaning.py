import pandas as pd


def clean_dataset(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the uploaded dataset.

    Cleaning steps:
    1. Remove exact duplicate rows.
    2. Fill missing text values with 'Unknown'.
    3. Keep missing numeric values unchanged.
    4. Reset the index.
    """

    cleaned_df = dataframe.copy()

    # Remove exact duplicate rows
    cleaned_df = cleaned_df.drop_duplicates()

    # Detect text columns
    text_columns = cleaned_df.select_dtypes(
        include=["object", "string"]
    ).columns

    # Fill missing text values
    cleaned_df[text_columns] = (
        cleaned_df[text_columns]
        .fillna("Unknown")
    )

    # Reset index after removing duplicates
    cleaned_df = cleaned_df.reset_index(
        drop=True
    )

    return cleaned_df