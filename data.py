from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "data"

MIN_DATE = pd.to_datetime("2016-01-01")
MAX_DATE = pd.to_datetime("2021-01-01")


def get_risk_rules():
    df = pd.read_parquet(DATA / "df_taxpayers_risk_rules.parquet")
    df.loc[:, "Risk rule"] = df[["nil_filer", "non_payer", "non_filer"]].apply(
        convert_boolean_flags_to_risk_rule, axis=1
    )

    df = df.drop(
        [
            "nil_filer",
            "non_filer",
            "non_payer",
            "buyer_from_suspicious",
            "seller_to_suspicious",
            "Identified_suspicious",
        ],
        axis=1,
    )

    return df


def convert_boolean_flags_to_risk_rule(boolean_risk_flags):
    flags = boolean_risk_flags.index[
        boolean_risk_flags
    ]  # This selects the flags that are True
    risk_rule = (
        " & ".join(flags) if flags.any() else ""
    )  # This joins flags into a string as you wanted
    return risk_rule


def get_transaction_data():
    df = pd.read_parquet(DATA / "df_sales.parquet")
    df = add_dates_transaction_data(df, MIN_DATE, MAX_DATE)
    return df


def get_taxpayer_identification():
    return pd.read_parquet(DATA / "df_taxpayers_identifications.parquet").fillna("")


def summarize_transactions(df_transactions):

    df_suppliers = (
        df_transactions.groupby(["TIN"])
        .agg(
            Receipts_offered=("Nreceipts", "sum"),
            Total_sales=("Total_sales", "sum"),
            Total_VAT_output=("Total_VAT_output", "sum"),
        )
        .reset_index()
    )

    df_clients = (
        df_transactions.groupby(["ClientsTIN"])
        .agg(
            Receipts_received=("Nreceipts", "sum"),
            Total_purchase=("Total_sales", "sum"),
            Total_VAT_input=("Total_VAT_output", "sum"),
        )
        .reset_index()
    )

    tins = np.unique(list(df_clients.ClientsTIN) + list(df_suppliers.TIN))
    tins = pd.DataFrame({"TIN": tins})

    taxpayer_summary = pd.merge(
        df_suppliers,
        tins,
        how="outer",
        left_on="TIN",
        right_on="TIN",
    )
    taxpayer_summary = pd.merge(
        taxpayer_summary,
        df_clients,
        how="outer",
        left_on="TIN",
        right_on="ClientsTIN",
    )

    taxpayer_summary = taxpayer_summary[
        [
            "TIN",
            "Receipts_offered",
            "Total_sales",
            "Receipts_received",
            "Total_purchase",
            "Total_VAT_input",
            "Total_VAT_output",
        ]
    ]
    taxpayer_summary = taxpayer_summary.fillna(0)

    # convert strint to int64
    taxpayer_summary.Receipts_offered = taxpayer_summary.Receipts_offered.astype(
        np.int64
    )
    taxpayer_summary.Receipts_received = taxpayer_summary.Receipts_received.astype(
        np.int64
    )
    taxpayer_summary.Total_sales = taxpayer_summary.Total_sales.astype(np.int64)
    taxpayer_summary.Total_purchase = taxpayer_summary.Total_purchase.astype(np.int64)
    taxpayer_summary.Total_VAT_input = taxpayer_summary.Total_VAT_input.astype(np.int64)
    taxpayer_summary.Total_VAT_output = taxpayer_summary.Total_VAT_output.astype(
        np.int64
    )

    # Add risk rule
    taxpayer_summary = pd.merge(
        taxpayer_summary,
        get_risk_rules(),
        how="outer",
        on="TIN",
    )
    taxpayer_summary.loc[:, "Risk rule"] = taxpayer_summary.loc[:, "Risk rule"].fillna(
        ""
    )

    # Add taxpayer identification
    taxpayer_summary = pd.merge(
        taxpayer_summary,
        get_taxpayer_identification(),
        how="outer",
        on="TIN",
    )
    return taxpayer_summary


### Additional helper functions
def filter_transaction_dates(data, start_date, end_date):
    transaction_data = data.loc[
        (data["Dates"] > start_date) & (data["Dates"] < end_date)
    ]
    return transaction_data


def random_dates(start, end, n=312458):
    start_u = start.value // 10 ** 9
    end_u = end.value // 10 ** 9
    np.random.seed(42)
    return pd.to_datetime(np.random.randint(start_u, end_u, n), unit="s")


def add_dates_transaction_data(trans_data, start_date, end_date):
    dates = random_dates(start_date, end_date)
    trans_data = pd.concat([pd.Series(dates), trans_data], axis=1)
    trans_data = trans_data.rename(columns={0: "Dates"})

    return trans_data
