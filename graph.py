import networkx as nx

import data

COLOR_MAP = {
    "non_filer": "#ef1f1f",
    "non_payer": "#ef1fdf",
    "nil_filer": "#1fef9a",
    "Compliant": "#33acff",
    "nil_filer & non_payer": "#16e1d4",
    "non_payer & non_filer": "#582a2a",
    "nil_filer & non_filer": "#2e582a",
    "nil_filer, non_filer & non_payer": "#9c1313",
    "": "#1135a8",
}


def build_graph(trans_data, create_using=nx.MultiDiGraph()):

    Graph_transaction = nx.from_pandas_edgelist(
        trans_data,
        "TIN",
        "ClientsTIN",
        ["Nreceipts", "Total_sales", "Total_VAT_output"],
        create_using=create_using,
    )

    summary = data.summarize_transactions(trans_data)

    summary.loc[:, "color"] = summary["Risk rule"].map(COLOR_MAP)

    summary.set_index("TIN", inplace=True)

    for node in Graph_transaction:
        Graph_transaction.add_node(
            node,
            group=summary.loc[node, "Risk rule"],
            total_sales=summary.loc[node, "Total_sales"],
            total_purchases=summary.loc[node, "Total_purchase"],
            TaxpayerName=summary.loc[node, "TaxpayerName"],
            TaxCentre=summary.loc[node, "TaxCentre"],
            color=summary.loc[node, "color"],
        )
    return Graph_transaction


def network_graph_payers(trans_data, tin_number, level):
    Graph_transaction = build_graph(trans_data)
    G = nx.ego_graph(Graph_transaction, tin_number, level, undirected=True)
    return G


def clients_network(trans_data, tin_number, level):
    Graph_transaction = build_graph(trans_data)
    successors = nx.dfs_successors(
        Graph_transaction, source=tin_number, depth_limit=level
    )

    node_list = [tin_number]
    for i in successors.values():
        for s in i:
            node_list.append(s)
    G = Graph_transaction.subgraph(node_list)

    return G


def supplier_network(trans_data, tin_number, level):

    Graph_transaction = build_graph(trans_data)

    whole_graph = nx.ego_graph(Graph_transaction, tin_number, level, undirected=True)

    K = list(nx.edge_dfs(whole_graph, tin_number, orientation="reverse"))
    upstream_nodes = []
    for edge in K:
        if edge[0] not in upstream_nodes:
            upstream_nodes.append(edge[0])
        if edge[1] not in upstream_nodes:
            upstream_nodes.append(edge[1])
    G = Graph_transaction.subgraph(upstream_nodes)
    return G


def get_network_graph(df, tin_number, level, direction=None):
    if (direction.lower() == "both") or (direction is None):
        func = network_graph_payers
    elif direction.lower() == "suppliers":
        func = supplier_network
    elif direction.lower() == "clients":
        func = clients_network

    G = func(df, tin_number, level)

    return G
