"""
skills.py

This module defines additional skills for the AI agent, such as plotting parameters from the data.
"""

try:
    from pandasai.skills import skill as _skill
except ImportError:  # pandasai is not a declared dependency; install manually on Python 3.11
    def _skill(fn):  # no-op decorator so the module loads without pandasai
        return fn


@_skill
def plot_parameter(parameter1, parameter2, df):
    """
    Displays a bar chart comparing two parameters from the dataframe.

    Args:
        parameter1 (str): The first parameter to plot.
        parameter2 (str): The second parameter to plot.
        df (pd.DataFrame): The dataframe containing the data.
    """
    import matplotlib.pyplot as plt

    plt.bar(df[parameter1], df[parameter2])
    plt.xlabel(parameter1)
    plt.ylabel(parameter2)
    plt.title(f"{parameter1} vs {parameter2}")
    plt.xticks(rotation=45)
    plt.show()
