import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import networkx as nx
import pandas as pd
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from networkx.readwrite import json_graph

import data
import graph
import plot

df_full = data.get_transaction_data()
START_DATE = pd.to_datetime("2019-08-05")
END_DATE = pd.to_datetime("2020-11-25")

LEVEL = 1
DEFAULT_TIN = "100001766"

DEFAULT_FIG = {
    "layout": {
        "xaxis": {"visible": False},
        "yaxis": {"visible": False},
        "annotations": [
            {
                "text": "Pick a date range and TIN number and click on CREATE GRAPH",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 28},
            }
        ],
    }
}

suppliers_clients_options = {
    1: "Both",
    2: "Suppliers",
    3: "Clients",
}


def get_taxpayer_summary(TIN, start_date, end_date):

    trans_data_period = data.filter_transaction_dates(df_full, start_date, end_date)
    summary = data.summarize_transactions(trans_data_period)
    summary.set_index("TIN", inplace=True)
    summary = f"""Taxpayer: {summary.loc[TIN, "TaxpayerName"]}

Sales: {summary.loc[TIN, "Total_sales"]:,.2f}
Rec.Offered: {summary.loc[TIN, "Receipts_offered"]:,.2f}
Tax output: {summary.loc[TIN, "Total_VAT_output"]:,.2f}

Purchases:{summary.loc[TIN, "Total_purchase"]:,.2f}
Rec.Received: {summary.loc[TIN, "Receipts_received"]:,.2f}
Tax input: {summary.loc[TIN, "Total_VAT_input"]:,.2f}
"""
    return summary


app = dash.Dash(
    __name__,
    show_undo_redo=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
app.title = "Network Analysis"


SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "20rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.P("Please input date range and TIN number", className="lead"),
        dcc.DatePickerRange(
            id="my-date-picker-range",
            min_date_allowed=data.MIN_DATE.date(),
            max_date_allowed=data.MAX_DATE.date(),
            start_date=START_DATE.date(),
            end_date=END_DATE.date(),
        ),
        html.Hr(),
        dbc.Input(
            id="tin_number",
            placeholder="Enter TIN number...",
            value=DEFAULT_TIN,
            type="text",
        ),
        html.Br(),
        dbc.FormGroup(
            [
                dbc.Label("Suppliers and/or clients?"),
                dbc.RadioItems(
                    options=[
                        {"label": label, "value": value}
                        for value, label in suppliers_clients_options.items()
                    ],
                    value=1,
                    id="suppliers_clients_check",
                    inline=True,
                ),
            ]
        ),
        html.Br(),
        dbc.Button(
            "Create graph",
            id="create_button",
            color="primary",
            className="mr-1",
        ),
        html.Hr(),
        dcc.Textarea(
            id="textarea_summary",
            value=get_taxpayer_summary(DEFAULT_TIN, START_DATE, END_DATE),
            style={"width": "100%", "height": "300px"},
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(
    children=[
        dcc.Store(id="graph-memory"),
        dcc.Store(id="tins-memory"),
        dcc.Graph(
            id="my-graph",
            figure=DEFAULT_FIG,
        ),
    ],
    style=CONTENT_STYLE,
)


app.layout = html.Div([dcc.Location(id="url"), sidebar, content])


@app.callback(
    Output("my-graph", "figure"),
    Output("textarea_summary", "value"),
    Output("graph-memory", "data"),
    Output("tins-memory", "data"),
    [
        Input("my-graph", "clickData"),
        Input("create_button", "n_clicks"),
    ],
    [
        State("suppliers_clients_check", "value"),
        State("tin_number", "value"),
        State("my-date-picker-range", "start_date"),
        State("my-date-picker-range", "end_date"),
        State("graph-memory", "data"),
        State("tins-memory", "data"),
    ],
)
def update_graph_output(
    figure,
    create,
    suppliers_clients_check,
    tin_number,
    start_date,
    end_date,
    graph_memory,
    tins_memory,
):
    changed_id = [p["prop_id"] for p in dash.callback_context.triggered][0]

    if "create_button" in changed_id:
        tins_memory = [tin_number]
        graph_memory = None
    elif "my-graph" in changed_id:
        tin_number = figure.get("points")[0].get("text")
        tins_memory = tins_memory or [tin_number]
        tins_memory.append(tin_number)
    else:
        raise PreventUpdate

    df_filtered = data.filter_transaction_dates(
        df_full,
        start_date,
        end_date,
    )

    G_new = graph.get_network_graph(
        df_filtered,
        tin_number,
        LEVEL,
        direction=suppliers_clients_options[suppliers_clients_check],
    )

    if graph_memory is not None:
        G_previous = json_graph.node_link_graph(graph_memory)
        G = nx.compose(G_previous, G_new)
    else:
        G = G_new

    network_fig = plot.plot_circular_graph(
        G,
        df_filtered,
        tin_highlight=tins_memory,
    )
    taxpayer_summary = get_taxpayer_summary(
        tin_number,
        start_date,
        end_date,
    )

    return network_fig, taxpayer_summary, json_graph.node_link_data(G), tins_memory


@app.callback(
    Output("tin_number", "value"),
    [
        Input("my-graph", "clickData"),
    ],
)
def display_click_data(clickData):

    if clickData is None:
        raise PreventUpdate
    TIN = clickData.get("points")[0].get("text")
    return TIN


if __name__ == "__main__":
    app.run_server(debug=True, port=8040)
