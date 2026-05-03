import pandas as pd

DATA_PATH = "data/cultures_agricoles.csv"

def load_cultures():
    return pd.read_csv(DATA_PATH)


def get_fao_code(culture_name: str):
    df = load_cultures()

    row = df[df["Culture"] == culture_name]

    if row.empty:
        raise ValueError(f"Culture non trouvée : {culture_name}")

    return int(row["Code_FAO_Exemple"].values[0])