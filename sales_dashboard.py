import dash 
from dash.dependencies import Input, Output
from dash import html, dcc, dash_table
import plotly.express as px
import pandas as pd
import io
import base64

# ------------------------------------------------------------------------------------------------------------------------------

#Function to read excel file, decode and convert to dataframe
def read_file(contents):
    if contents is None:
        return ''
    content_type, content_string = contents.split(',')
    
    decoded = io.BytesIO(base64.b64decode(content_string))
    df = pd.read_excel(decoded, engine='openpyxl')
    # Creating an ID column 
    df['id'] = df['Record ID']
    df.set_index('id', inplace=True, drop=False)
    print(df.columns)

    return df

# ------------------------------------------------------------------------------------------------------------------------------

# App initialisation
app = dash.Dash(__name__, prevent_initial_callbacks=True)

# ------------------------------------------------------------------------------------------------------------------------------

app.layout = html.Div([
    html.Div(id='upload-container', className='centered-container', 
                                 children=[
                                            dcc.Upload(
                                                        id='upload-data',
                                                        children=html.Div([html.A('Select Data File')], style={'color': 'black'}),
                                                        style={
                                                            'width': '50%',
                                                            'height': '60px',
                                                            'lineHeight': '60px',
                                                            'borderWidth': '1px',
                                                            'borderStyle': 'dashed',
                                                            'borderRadius': '5px',
                                                            'textAlign': 'center',
                                                            'margin': '10px auto',  # Center horizontally
                                                        },
                                                        multiple=False,
                                                    ),
                                                ]),                   
    
    html.Div(id = 'data-table-component'),

    html.Br(),
    html.Br(),
    html.Div(id='bar-container'),
    html.Div(id='choromap-container')

])

# ------------------------------------------------------------------------------------------------------------------------------

@app.callback(
        Output('data-table-component', 'children'),
        Input('upload-data', 'contents'),      
)
def make_table(contents):
    if contents is None:
        return ''
    df = read_file(contents)
    table = dash_table.DataTable(
                id='datatable-interactivity',
                columns=[
                    {"name": i, "id": i, "deletable": True, "selectable": True, "hideable": True}
                    if i == "iso_alpha3" or i == "year" or i == "id"
                    else {"name": i, "id": i, "deletable": True, "selectable": True}
                    for i in df.columns
                ],
                data=df.to_dict('records'),  
                editable=False,              # editting inside cell - no
                filter_action="native",     
                sort_action="native",       
                sort_mode="single",         
                column_selectable="multi",  
                row_selectable="multi",     
                row_deletable=False,         
                selected_columns=[],        # indices of user selected columns
                selected_rows=[],           # rows
                page_action="native",       # all data is passed to the table up-front
                page_current=0,             # current pg no.
                page_size=6,                # rows per page
                style_cell={                # ensure adequate header width when text is shorter than cell's text
                    'minWidth': 95, 'maxWidth': 95, 'width': 95
                },
                style_cell_conditional=[    # align text columns to left. default - right
                    {
                        'if': {'column_id': c},
                        'textAlign': 'left'
                    } for c in ['country', 'iso_alpha3']
                ],
                style_data={                # overflow cell contents into multiple lines
                    'whiteSpace': 'normal',
                    'height': 'auto'
                }
            )
    return table

# ------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)
