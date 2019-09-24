import dash
import dash_table
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import pandas as pd
from dash_table.Format import Format, Scheme
from sqlalchemy import create_engine
import plotly.express as px
from plotly.subplots import make_subplots

# TODO
# Unify the languages
# Clean up the code

##############
# Model Code #
##############

conn = create_engine("sqlite:///./train_items.db")


def fetch_data(q: str, conn) -> pd.DataFrame:
    '''
    parm: q - the SQL query
    parm: conn - the create engine variable
    '''
    return pd.read_sql(sql=q, con=conn)


def query_date(conn,clickData):
    q = ''
    if clickData:
        sport = clickData['points'][0]['x']
        q = f'''SELECT "Date",
                    AVG("Reps")AS "Avg Reps",AVG(Weight) AS "Avg Weight"
                FROM train_record
                WHERE "Exercise Name" = "{sport}"
                GROUP BY "Date"
                ORDER BY "Date" '''
    else:
        q =  '''SELECT "Date",AVG(Weight) AS 'Avg Weight',
                    AVG("Reps")AS "Avg Reps"
                FROM train_record
                GROUP BY "Date"
                ORDER BY "Date" '''
    return fetch_data(q, conn)


def query_sport_name(conn,clickData):
    q=''
    if clickData:
        sport_name = clickData['points'][0]['x']
        q = f'''SELECT "Exercise Name",
                            sum("Reps")AS "Avg Reps", AVG(Weight) AS "Avg Weight"
                            FROM train_record
                            WHERE "Reps" > 0 AND "Date" = "{sport_name}"
                            GROUP BY "Exercise Name"
                            ORDER BY sum("Reps")DESC '''
    else:
        q = '''SELECT "Exercise Name",
                            sum("Reps") AS "Avg Reps", AVG(Weight) AS 'Avg Weight'
                            FROM train_record
                            WHERE "Reps" > 0
                            GROUP BY "Exercise Name"
                            ORDER BY sum("Reps") DESC '''
    return fetch_data(q, conn)



##########
#  View  #
##########

color_scheme = {
    'white': "#FFF",
    "black": '#011627',
    'black pearl':'#011627',
    'snappire': '#293F99',
    'cerulean':'#19ACE3',
    'dark cerulearn':'#004777',
    'dark_grey': '#373E49',
    'grey': '#9099AB',
    'red': '#FF5A33'
}
external_stylesheets = ['https://unpkg.com/purecss@1.0.0/build/pure-min.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server



def generate_fact():
    days_query = 'SELECT COUNT(DISTINCT "Date") AS days FROM train_record'
    days = fetch_data(days_query,conn).at[0,"days"]
    return days

def get_favorite_excercise():
  query = 'SELECT "Exercise Name",COUNT("Exercise Name")\
                FROM (SELECT date(Date), "Exercise Name"\
            FROM train_record GROUP BY date(Date), "Exercise Name") \
            GROUP BY  "Exercise Name" \
            ORDER BY  COUNT("Exercise Name") DESC'
  excercise = fetch_data(query,conn).at[0,'Exercise Name']
  return excercise

def get_favorite_workout_plan():
  query = 'SELECT "Workout Name",COUNT("Workout Name")\
                FROM (SELECT date(Date), "Workout Name"\
            FROM train_record GROUP BY date(Date), "Workout Name") \
            GROUP BY  "Workout Name" \
            ORDER BY  COUNT("Workout Name") DESC'
  workout = fetch_data(query,conn).at[0,'Workout Name']
  return workout

def get_max_weight():
  query = 'SELECT Weight\
            FROM train_record ORDER BY Weight DESC'
  weight = fetch_data(query,conn).at[1,'Weight']
  return weight

# def get_
  
def gen_radar():
  df = pd.DataFrame(dict(
    r=[1, 5, 2, 2, 3],
    theta=['processing cost','mechanical properties','chemical stability', 
           'thermal stability', 'device integration']))
  radar = px.line_polar(df, r='r', theta='theta', line_close=True,width=400,height=300)
  radar.update_traces(fill='toself')
  return radar

def get_heatmap_data():

  query='SELECT date(Date) AS Date,strftime("%H",Date) AS Hour, strftime("%w",Date) AS daysofweek, sum("Reps") AS "Avg Reps" \
              FROM train_record GROUP BY date(Date),Hour,daysofweek ORDER BY date(Date)'
  heatmap_data = fetch_data(query,conn)
  return heatmap_data

def gen_heatmap():
  heatmap_source = get_heatmap_data()
  heatmap_source['Date'] = pd.to_datetime(heatmap_source['Date'])
  heatmap_pivot = pd.pivot_table(heatmap_source,index=['Hour'],columns=['daysofweek'],values=['Avg Reps'],aggfunc='count').fillna(0)
  heatmap_pivot = heatmap_pivot.reset_index()
  fig = go.Figure(data=go.Heatmap(
                   z=[list(heatmap_pivot.loc[:,('Avg Reps','0')].values),\
                   list(heatmap_pivot.loc[:,('Avg Reps','1')].values),\
                   list(heatmap_pivot.loc[:,('Avg Reps','2')].values), \
                   list(heatmap_pivot.loc[:,('Avg Reps','3')].values),\
                   list(heatmap_pivot.loc[:,('Avg Reps','4')].values),\
                   list(heatmap_pivot.loc[:,('Avg Reps','5')].values), \
                   list(heatmap_pivot.loc[:,('Avg Reps','6')].values)],
                   x= [str(i) + ':00' for i in heatmap_pivot['Hour'].tolist()], 
                   # x = [str(i) for i in heatmap_pivot.index.get_level_values('weekofmonth').tolist()],
                   y=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday','Saturday','Sunday'],
                   colorscale=['#D0DCED',color_scheme['cerulean'],color_scheme['black pearl']]),\
                   layout=go.Layout(title='Workout at which time in a day',width=600,height=320))
  return fig

app.layout = html.Div(children=[
  html.Div([
    html.H2(children='Weight Training Analysis'),
    html.H2(children='Workout Dashboard',className='subtitle'),
    ],className='banner'),
    html.Div([
      html.Div([
        html.Div(children=[html.Div(children="This dashboard based data of traing records \
                                              of a Strong App user, showing instense, frequence, \
                                              and preference of taining in a 3 years time interval. "),
                          html.Div([
                                 html.Div(f"The favorite exercise: {get_favorite_excercise()}", className='statstext'),
                                 html.Div(f"The favorite Workout Plan: {get_favorite_workout_plan()}", className='statstext'),
                                 html.Div(f"The max lift weight: {get_max_weight():.0f} lb", className='statstext')
                            ],className='stats')
                           
                           ], className='pure-u-1-5 summary'),
        html.Div(children=[dcc.Graph(id='heatmap',figure=gen_heatmap())], className='pure-u-3-5 first_chart')
    ],
             className='pure-g'),
    html.Div(children=[
        html.Div(dcc.Graph(id='time_trend',figure={'layout':{'plot_bgcolor':color_scheme['white'],
                                      'paper_bgcolor':color_scheme['white']}}), className='pure-u-1 second_chart'),
        html.Div(dcc.Graph(id='sports_potion_barplot',figure={'layout':{'plot_bgcolor':color_scheme['black'],
                                      'paper_bgcolor':color_scheme['white']}}), className='pure-u-1 third_chart')
    ],
             className='pure-g'),
    
],className='container')

      ])
    

# CallBacks

# Customerize the bar plot interaction
@app.callback(
    Output(component_id='sports_potion_barplot', component_property='figure'),
    [Input('time_trend', 'clickData')
    ])
def generate_bar_graph(clickData):
    dataframe = query_sport_name(conn, clickData)
    bar = make_subplots(specs=[[{"secondary_y": True}]])
    fig = go.Figure(
              data=[

              ]
      )
    bar.add_trace(
        go.Bar(x=dataframe['Exercise Name'].tolist(),
               y=dataframe['Avg Reps'].tolist(),
               width=0.55,
               marker={'color': color_scheme['cerulean']}),
        secondary_y=False
      ) 

    bar.update_layout(
      barmode='group',
      legend_orientation="h",
      title=f"Total Repeats of Each Exercises",
      width=900,
                                      font={'color': color_scheme['black']},
                                      plot_bgcolor=color_scheme['white'],
                                      paper_bgcolor=color_scheme['white'],
                                      xaxis={
                                          'title': 'Exercise Name',
                                          'tickfont': {
                                              'size': 8
                                          },
                                          'showgrid': False,
                                          'linewidth': 1,
                                          'linecolor': color_scheme['black']
                                      },
                                      yaxis={
                                          'title': 'Avg Reps',
                                          'linewidth': 1,
                                          'linecolor': color_scheme['black'],
                                          'tickfont': {
                                              'size': 10
                                          },
                                          'showgrid': False,
                                          'showline': True
                                      },
                                      height=400,
                                      autosize=True,
                                      bargap=0.1,
                                      hovermode='closest'

      )     
    if clickData:
      bar.update_layout(title=f"Exercises of {clickData['points'][0]['x']}")

    return bar




@app.callback(Output(component_id='time_trend', component_property='figure'), 
        [Input(component_id='sports_potion_barplot', component_property='clickData')
])
def update_time_trend(clickData):
    dataframe = query_date(conn,clickData)
    time_fig = make_subplots(specs=[[{"secondary_y": True}]])
    time_fig.add_trace(
        go.Scatter({
            'x': dataframe["Date"].tolist(),
            'y': dataframe["Avg Reps"].tolist(),
            'type': 'line',
             'mode':"lines",
            'name': 'Avg Reps',
            'line':{'width':1,'color':color_scheme['cerulean']},
            'marker': {
                'color': color_scheme['snappire']
            }
        }),
        secondary_y=False
      )
    
    time_fig.add_trace(go.Scatter(x=dataframe["Date"].tolist(), 
                                  y=dataframe["Avg Weight"].tolist(),
                                  line={'width':1,'color':color_scheme['dark cerulearn']}, 
                                    name="Avg Weight"),
                      secondary_y=True)
    time_fig.update_layout(
                         legend_orientation="h",
                         plot_bgcolor= color_scheme['white'],
                         paper_bgcolor= color_scheme['white'],
                         autosize= False,
                         title= "Total Repeats Trending",
                         font= {
                             'color': color_scheme['black']
                         },
                         width=900,
                         height= 400,
                         xaxis= {
                             'title': 'Date',
                             'showgrid': False,
                             'showline': True,
                             'linewidth': 1,
                             'linecolor': color_scheme['black'],
                             'tickformat': '%d %b %Y'
                         },
                         yaxis={
                         'title': 'Avg Reps',
                             'showline': True,
                             'linecolor': color_scheme['black'],
                         'linewidth': 1,
                         },
                         yaxis2={
                             'showline': True,
                         'title': 'Avg Weight',
                         'linecolor': color_scheme['black'],
                         'linewidth': 1,
                         },
                         hovermode='closest')
    if clickData:
      time_fig.update_layout(title= f"Repeats Trending of {clickData['points'][0]['x']}  ")
    return time_fig


if __name__ == '__main__':
    app.run_server(debug=True)

