import pandas as pd


def export_to_excel(
    data,
    columns,
    filename
):

    df = pd.DataFrame(
        data,
        columns=columns
    )

    df.to_excel(
        filename,
        index=False
    )

    return filename