
import plotly.graph_objects as go
import pandas as pd

# Load data
df=pd.read_csv("./marketdata/tradedata/binance/future/SNXUSDT/binance-SNXUSDT.csv")

# Create figure
fig = go.Figure()

SMA_LINE_NAME = "SMA40"

fig.add_trace(
    go.Scattergl(
        name='Buy',
        x=list(df["Datetime"][df["Side"] == 'buy']),
        y=list(df["Price"][df["Side"] == 'buy']),
        mode='markers',
        marker=dict(
            color='forestgreen',
            size=10,
            line=dict(
                width=1,
                color='forestgreen')
        )
    )
)

fig.add_trace(
    go.Scattergl(
        name='Sell',
        x=list(df["Datetime"][df["Side"] == 'sell']),
        y=list(df["Price"][df["Side"] == 'sell']),
        mode='markers',
        marker=dict(
            color='orangered',
            size=10,
            line=dict(
                width=1,
                color='orangered')
        )
    )
)

fig.add_trace(
    go.Scattergl(
        name='Buy/Sell Line',
        x=list(df["Datetime"]),
        y=list(df["Price"]),
        mode='lines',
        line=dict(
                width=4,
                color='blue'),
        marker=dict(
            color='blue',
            size=10,
            line=dict(
                width=1,
                color='blue')
        )
    )
)

fig.add_trace(
    go.Scattergl(
        name=SMA_LINE_NAME,
        x=list(df["Datetime"][df[SMA_LINE_NAME] != 0]),
        y=list(df[SMA_LINE_NAME][df[SMA_LINE_NAME] != 0]),
        mode='lines+markers',
        marker=dict(
            size=1,
            color='orange',
            line=dict(
                width=2,
                color='green')
        )
    )
)

'''fig.add_trace(
    go.Scattergl(
        name='SMA5',
        x=list(df["Datetime"][df["SMA5"] != 0]),
        y=list(df["SMA5"][df["SMA5"] != 0]),
        mode='lines+markers',
        marker=dict(
            size=1,
            color='orange',
            line=dict(
                width=2,
                color='green')
        )
    )
)

fig.add_trace(
    go.Scattergl(
        name='SMA7',
        x=list(df["Datetime"][df["SMA7"] != 0]),
        y=list(df["SMA7"][df["SMA7"] != 0]),
        mode='lines+markers',
        marker=dict(
            size=1,
            color='orange',
            line=dict(
                width=2,
                color='green')
        )
    )
)'''

fig.update_xaxes(
           tickformat="%Y-%m-%d %H:%M:%S.%L"
        )
fig.show()