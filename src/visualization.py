import json

import plotly.express as px

from src.utils import clean_json_response


MODEL_NAME = "openai/gpt-oss-20b"


def generate_visualization_plan(
    client,
    question,
    result_df
):
    """
    Ask the AI whether a visualization is useful
    and select the appropriate chart type and columns.
    """

    columns = list(result_df.columns)

    data_types = (
        result_df
        .dtypes
        .astype(str)
        .to_dict()
    )

    sample_data = (
        result_df
        .head(10)
        .to_dict(orient="records")
    )

    prompt = f"""
You are an expert data visualization analyst.

User question:

{question}

Result columns:

{columns}

Result data types:

{data_types}

Sample result:

{sample_data}

Determine whether a chart would help answer
the user's question.

Return ONLY valid JSON:

{{
    "create_chart": true,
    "chart_type": "bar",
    "x": "column_name",
    "y": "column_name",
    "title": "Chart title"
}}

Allowed chart types:

bar
line
scatter
histogram
pie

Rules:

1. Use bar charts for:
   - category comparisons
   - rankings
   - top-N results

2. Use line charts for:
   - time-series data
   - trends
   - chronological progression

3. Use scatter plots for:
   - relationships between two numeric variables
   - correlation exploration

4. Use histograms for:
   - distribution of one numeric variable

5. Use pie charts only for:
   - meaningful part-to-whole relationships
   - relatively few categories

6. x and y must exactly match
   the available result columns.

7. For a histogram:
   - x = numeric column
   - y = null

8. If a visualization is not useful, return:

{{
    "create_chart": false,
    "chart_type": null,
    "x": null,
    "y": null,
    "title": null
}}

9. Do not invent columns.

10. Return JSON only.
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
                        "You create structured "
                        "data visualization plans."
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


def create_dynamic_chart(
    result_df,
    chart_plan
):
    """
    Generate a Plotly chart based on
    the AI visualization plan.
    """

    chart_type = chart_plan.get("chart_type")
    x_column = chart_plan.get("x")
    y_column = chart_plan.get("y")

    title = chart_plan.get(
        "title",
        "Data Visualization"
    )

    available_columns = list(
        result_df.columns
    )

    # Validate selected columns
    if (
        x_column is not None
        and x_column not in available_columns
    ):
        raise ValueError(
            f"Column '{x_column}' does not exist."
        )

    if (
        y_column is not None
        and y_column not in available_columns
    ):
        raise ValueError(
            f"Column '{y_column}' does not exist."
        )

    chart_df = result_df.copy()

    # Prevent extremely large visualizations
    if len(chart_df) > 1000:
        chart_df = chart_df.head(1000)

    # ----------------------------------------------
    # Bar Chart
    # ----------------------------------------------

    if chart_type == "bar":

        if x_column is None or y_column is None:
            raise ValueError(
                "Bar chart requires X and Y columns."
            )

        return px.bar(
            chart_df,
            x=x_column,
            y=y_column,
            title=title
        )

    # ----------------------------------------------
    # Line Chart
    # ----------------------------------------------

    if chart_type == "line":

        if x_column is None or y_column is None:
            raise ValueError(
                "Line chart requires X and Y columns."
            )

        return px.line(
            chart_df,
            x=x_column,
            y=y_column,
            title=title,
            markers=True
        )

    # ----------------------------------------------
    # Scatter Plot
    # ----------------------------------------------

    if chart_type == "scatter":

        if x_column is None or y_column is None:
            raise ValueError(
                "Scatter plot requires X and Y columns."
            )

        return px.scatter(
            chart_df,
            x=x_column,
            y=y_column,
            title=title
        )

    # ----------------------------------------------
    # Histogram
    # ----------------------------------------------

    if chart_type == "histogram":

        if x_column is None:
            raise ValueError(
                "Histogram requires an X column."
            )

        return px.histogram(
            chart_df,
            x=x_column,
            title=title
        )

    # ----------------------------------------------
    # Pie Chart
    # ----------------------------------------------

    if chart_type == "pie":

        if x_column is None or y_column is None:
            raise ValueError(
                "Pie chart requires category "
                "and value columns."
            )

        return px.pie(
            chart_df,
            names=x_column,
            values=y_column,
            title=title
        )

    raise ValueError(
        f"Unsupported chart type: {chart_type}"
    )