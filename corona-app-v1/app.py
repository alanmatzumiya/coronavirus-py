import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import pandas as pd

baseURL = (
    "https://raw.githubusercontent.com/" +
    "CSSEGISandData/COVID-19/master/" +
    "csse_covid_19_data/csse_covid_19_time_series/"
)


tickFont = {
    'size':12,
    'color':"rgb(30,30,30)",
    'family':"Courier New, monospace"
}

def loadData(fileName, columnName):

    data = pd.read_csv(baseURL + fileName) \
             .drop(['Lat', 'Long'], axis=1) \
             .melt(id_vars=['Province/State', 'Country/Region'],
                   var_name='date', value_name=columnName) \
             .fillna('<all>')
    data['date'] = data['date'].astype('datetime64[ns]')
    return data

allData = loadData("time_series_19-covid-Confirmed.csv", "CumConfirmed") \
    .merge(loadData("time_series_19-covid-Deaths.csv", "CumDeaths")) \
    .merge(loadData("time_series_19-covid-Recovered.csv", "CumRecovered")) \
    .merge(loadData("time_series_19-covid-Confirmed.csv", "NewConfirmed")) \
    .merge(loadData("time_series_19-covid-Deaths.csv", "NewDeaths")) \
    .merge(loadData("time_series_19-covid-Recovered.csv", "CumRecovered"))


countries = allData['Country/Region'].unique()
countries.sort()

app = dash.Dash(
    __name__
)

app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

app.layout = html.Div(
    style={ 'font-family':"Roboto" },
    children=[
        html.H1('Evolución histórica de COVID-19'),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="four columns",
                    children=[
                        html.H5('País'),
                        dcc.Dropdown(
                            id='country',
                            options=[{'label':c, 'value':c} for c in countries],
                            value='Mexico'
                        )
                    ]
                ),
                html.Div(
                    className="four columns",
                    children=[
                        html.H5('Estado / Provincia'),
                        dcc.Dropdown(
                            id='state'
                        )
                    ]
                ),
                html.Div(
                    className="four columns",
                    children=[
                        html.H5('Metricas'),
                        dcc.Checklist(
                            id='metrics',
                            options=[{'label':m, 'value':m}
                                     for m in ['Confirmed', 'Deaths', 'Recovered']],
                            value=['Confirmed', 'Deaths']
                        )
                    ]
                )
            ]
        ),
        dcc.Graph(
            id="plot_new_metrics",
            config={ 'displayModeBar': False }
        ),
        dcc.Graph(
            id="plot_cum_metrics",
            config={ 'displayModeBar': False }
        )
    ]
)

@app.callback(
    [Output('state', 'options'), Output('state', 'value')],
    [Input('country', 'value')]
)
def update_states(country):
    states = list(allData.loc[allData['Country/Region'] == country]['Province/State'].unique())
    states.insert(0, '<all>')
    states.sort()
    state_options = [{'label':s, 'value':s} for s in states]
    state_value = state_options[0]['value']
    return state_options, state_value

def nonreactive_data(country, state):
    data = allData.loc[allData['Country/Region'] == country]
    if state == '<all>':
        data = data.drop('Province/State', axis=1).groupby("date").sum().reset_index()
    else:
        data = data.loc[data['Province/State'] == state]
    newCases = data.select_dtypes(include='int64').diff().fillna(0)
    newCases.columns = [column.replace('Cum', 'New') for column in newCases.columns]
    data = data.join(newCases)
    data['dateStr'] = data['date'].dt.strftime('%b %d, %Y')
    return data

def barchart(data, metrics, prefix="", yaxisTitle=""):
    figure = go.Figure(
        data=[
            go.Bar( 
                name=metric, x=data.date, y=data[prefix + metric],
                marker_line_color='rgb(0,0,0)', marker_line_width=1,
                marker_color={
                    'Deaths':'rgb(200,30,30)',
                    'Recovered':'rgb(30,200,30)',
                    'Confirmed':'rgb(100,140,240)'
                }[metric]
            ) for metric in metrics
        ]
    )
    figure.update_layout(
        barmode='group',
        legend=dict(
            x=.05,
            y=0.95,
            font={'size':15},
            bgcolor='rgba(240,240,240,0.5)'),
        plot_bgcolor='#FFFFFF', font=tickFont
    ).update_xaxes(
        title="",
        tickangle=-90,
        type='category',
        showgrid=True,
        gridcolor='#DDDDDD',
        tickfont=tickFont,
        ticktext=data.dateStr,
        tickvals=data.date
    ).update_yaxes(
        title=yaxisTitle,
        showgrid=True,
        gridcolor='#DDDDDD'
    )
    return figure

@app.callback(
    Output('plot_new_metrics', 'figure'), 
    [Input('country', 'value'), Input('state', 'value'), Input('metrics', 'value')]
)
def update_plot_new_metrics(country, state, metrics):
    data = nonreactive_data(country, state)
    return barchart(data, metrics, prefix="New", yaxisTitle="Nuevos casos por día")

@app.callback(
    Output('plot_cum_metrics', 'figure'), 
    [Input('country', 'value'), Input('state', 'value'), Input('metrics', 'value')]
)
def update_plot_cum_metrics(country, state, metrics):
    data = nonreactive_data(country, state)
    return barchart(data, metrics, prefix="Cum", yaxisTitle="Casos acumulados")

if __name__ == '__main__':
    app.run_server(debug=True)
