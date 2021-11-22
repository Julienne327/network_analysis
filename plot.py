import networkx as nx
import numpy as np
import plotly.graph_objs as go


def plot_circular_graph(G, trans_data, tin_highlight=None):
    tin_highlight = tin_highlight or []
    # creating nodes positions in the graph
    pos = nx.nx_agraph.graphviz_layout(G, prog="circo")
    if tin_highlight:
        pos[tin_highlight[0]] = np.array([0, 0])
    for node in G.nodes:
        G.nodes[node]["pos"] = list(pos[node])

    traceRecode = []  # contains edge_trace, node_trace, middle_node_trace

    # Adding edges as disconnected lines

    for edge in G.edges():
        x0, y0 = G.nodes[edge[0]]["pos"]
        x1, y1 = G.nodes[edge[1]]["pos"]
        weight = (
            float(G[edge[0]][edge[1]][0]["Nreceipts"])
            / max(trans_data["Nreceipts"])
            * 200
        )

        edge_trace = go.Scatter(
            x=tuple([x0, x1, None]),
            y=tuple([y0, y1, None]),
            mode="lines",
            line={"width": weight},
            marker=dict(color="LightSkyBlue"),
            line_shape="spline",
            opacity=1,
        )

        traceRecode.append(edge_trace)

    ########################################## Nodes as a scatter trace ####################################

    node_trace = go.Scatter(
        x=[],
        y=[],
        hovertext=[],
        text=[],
        mode="markers+text",
        textposition="bottom center",
        hoverinfo="text",
        marker={
            "size": [],
            "color": [],
            "symbol": [],
            "line": {"width": [], "color": "white"},
        },
    )

    for node in G.nodes():

        x, y = G.nodes[node]["pos"]
        hovertext = (
            "Taxpayer Name: "
            + str(G.nodes[node]["TaxpayerName"])
            + "<br>"
            + "Total Sales: "
            + str(G.nodes[node]["total_sales"])
            + "<br>"
            + "Total Purchase: "
            + str(G.nodes[node]["total_purchases"])
            + "<br>"
            + "Tax Center: "
            + str(G.nodes[node]["TaxCentre"])
        )
        text = node
        color = G.nodes[node]["color"]
        node_trace["x"] += tuple([x])
        node_trace["y"] += tuple([y])
        node_trace["hovertext"] += tuple([hovertext])
        node_trace["text"] += tuple([text])
        node_trace["marker"]["color"] += tuple([color])
        if node in tin_highlight:
            node_trace["marker"]["size"] += tuple([35])
            node_trace["marker"]["symbol"] += tuple(["circle-cross"])
            node_trace["marker"]["line"]["width"] += tuple([3])
        else:
            node_trace["marker"]["size"] += tuple([20])
            node_trace["marker"]["symbol"] += tuple(["circle"])
            node_trace["marker"]["line"]["width"] += tuple([0.5])

        traceRecode.append(node_trace)

    ##################### Hover text #############################################################3

    middle_hover_trace = go.Scatter(
        x=[],
        y=[],
        hovertext=[],
        mode="markers",
        hoverinfo="text",
        marker={"size": 10, "color": "LightSkyBlue"},
        opacity=0,
    )

    for edge in G.edges:
        x0, y0 = G.nodes[edge[0]]["pos"]
        x1, y1 = G.nodes[edge[1]]["pos"]
        hovertext = (
            "Supplier: "
            + str(edge[0])
            + "<br>"
            + "Client: "
            + str(edge[1])
            + "<br>"
            + "N Receipts: "
            + str(G[edge[0]][edge[1]][0]["Nreceipts"])
            + "<br>"
            + "Transaction Amount: "
            + str(G[edge[0]][edge[1]][0]["Total_VAT_output"])
        )
        middle_hover_trace["x"] += tuple([(x0 + x1) / 2])
        middle_hover_trace["y"] += tuple([(y0 + y1) / 2])
        middle_hover_trace["hovertext"] += tuple([hovertext])
        traceRecode.append(middle_hover_trace)

    #################################################################################################################################################################

    figure = {
        "data": traceRecode,
        "layout": go.Layout(
            title="Interactive Transaction Visualization",
            showlegend=False,
            hovermode="closest",
            margin={"b": 40, "l": 40, "r": 40, "t": 40},
            xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
            yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
            height=600,
            clickmode="event+select",
            annotations=[
                dict(
                    ax=(G.nodes[edge[0]]["pos"][0]),
                    ay=(G.nodes[edge[0]]["pos"][1]),
                    axref="x",
                    ayref="y",
                    x=(G.nodes[edge[1]]["pos"][0]),
                    y=(G.nodes[edge[1]]["pos"][1]),
                    xref="x",
                    yref="y",
                    showarrow=True,
                    startstandoff=10,
                    arrowcolor="LightGray",
                    arrowhead=5,
                    arrowsize=1,
                    arrowwidth=1,
                    opacity=1,
                )
                for edge in G.edges
            ],
        ),
    }
    return figure
