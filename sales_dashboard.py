import dash 
from dash.dependencies import Input, Output
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
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
    df.set_index('Record ID', inplace=True, drop = False)
    df['Create Date'] = pd.to_datetime(df['Create Date']) 
    df['Year'] = df['Create Date'].dt.year
    # print(df['Year'])
    # print(df.columns)

    return df
# data = [["react", "React"], ["ng", "Angular"], ["svelte", "Svelte"], ["vue", "Vue"]]
# ------------------------------------------------------------------------------------------------------------------------------

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
                                                            'margin': '10px auto',  
                                                        },
                                                        multiple=False,
                                                    ),
                                                ]),                                                               
    
    html.Div(id = 'data-table-component'),
    # html.Div(id = 'year-silder'),
    html.Div([
    dcc.Input(
        id='year-input',
        type='number',
        placeholder='Enter year',
        value=2023,  
    ),
]),
    
    html.Br(),
    html.Br(),
    html.Div(id='bar-container'),
    dcc.Graph(id='country-map'),
    html.Div([
        dcc.Slider(id='year-slider', value=0, min=0, max=100),
        ]),
    
    html.Div([
            #   html.Div([dcc.Graph(id = 'country-bar-chart'),
            #             html.Div(id='missing-country-count2')]),

              html.Div([dcc.Graph(id = 'country-pie-chart'),
                        html.Div(id='missing-country-count')]),

              html.Div([dcc.Graph(id = 'lead-source-pie-chart'),
                        html.Div(id='missing-leadsource-count')]),

              html.Div([dcc.Graph(id = 'contact-owner-pie-chart'),
                        html.Div(id='missing-contactowner-count')]),

              html.Div([dcc.Graph(id = 'lead-status-pie-chart'),
                        html.Div(id='missing-leadstatus-count')]),

              dcc.Graph(id = 'month-pie-chart'),

              html.Div([dcc.Graph(id = 'age-pie-chart'),
                        html.Div(id='inconsistent-values')]),
            ]),
])

# ------------------------------------------------------------------------------------------------------------------------------

@app.callback(
        Output('data-table-component', 'children'),
        # Output('year-slider', 'children'),
        Input('upload-data', 'contents'),      
        
)
def make_table(contents):
    if contents is None:
        return dash.no_update#, dash.no_update
    
    df = read_file(contents)
    table = dash_table.DataTable(
                id='datatable-interactivity',
                columns=[{  "name": i, "id": i, "deletable": True, "selectable": True, "hideable": True}
                            if i == "iso_alpha3" or i == "year" or i == "id"
                            else {"name": i, "id": i, "deletable": True, "selectable": True}
                            for i in df.columns],
                data=df.to_dict('records'),  
                editable=False,              # editting inside cell - no
                filter_action="native",     
                sort_action="native",       
                sort_mode="single",           
                row_deletable=False,         
                page_action="native",       # all data is passed to the table up-front
                page_current=0,             # current pg no.
                page_size=10,                # rows per page
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
    
    # slider = dcc.Slider(min=min(df['Year']),
    #                     max=max(df['Year']),
    #                     step=1,
    #                     value=2023,
    #                     marks={str(year): str(year) for year in df['Year'].unique()},
    #                     id='slider')
    
    return table#, slider 

# ------------------------------------------------------------------------------------------------------------------------------

@app.callback(
        Output('country-map', 'figure'),
        Input('upload-data', 'contents'),
        Input('year-input', 'value'),
        Prevent_initial_call = True,      
)
def make_pie_chart(contents, selected_year):
    if contents is None:
        return dash.no_update
    df = read_file(contents)

    filtered_df = df[df['Year'] == selected_year]
    
    country_counts = filtered_df['Country/Region'].value_counts().reset_index()
    country_counts.columns = ['Country/Region', 'Lead Count']

    fig = px.choropleth(country_counts, 
                    locations='Country/Region',  
                    locationmode='country names', 
                    color='Lead Count',  
                    hover_name='Country/Region',  
                    color_continuous_scale=px.colors.sequential.Plasma,
                    title='Country-wise Lead Distribution Map')
    
    return fig

# ------------------------------------------------------------------------------------------------------------------------------

@app.callback(
        Output('country-pie-chart', 'figure'),
        Output('missing-country-count', 'children'),
        Input('upload-data', 'contents'),
        Input('year-input', 'value'),
        Prevent_initial_call = True,      
)
def make_pie_chart(contents, selected_year):
    if contents is None:
        return dash.no_update, dash.no_update
    df = read_file(contents)

    filtered_df = df[df['Year'] == selected_year]
    country_counts = filtered_df['Country/Region'].value_counts().reset_index() #new dataframe country_counts
    country_counts.columns = ['Country/Region', 'Lead Count'] #cols in country_counts = country/reg and lead count 

    missing_data_count = len(filtered_df[filtered_df['Country/Region'].isna()]) 
    fig = px.pie(country_counts, names='Country/Region', values='Lead Count', title='Country-wise Lead Distribution')

    return fig, f"Missing Country Data Count: {missing_data_count}"

# ------------------------------------------------------------------------------------------------------------------------------

@app.callback(
        Output('lead-source-pie-chart', 'figure'),
        Output('missing-leadsource-count', 'children'),
        Input('upload-data', 'contents'),
        Input('year-input', 'value'),
        Prevent_initial_call = True,      
)
def make_pie_chart(contents, selected_year):
    if contents is None:
        return dash.no_update, dash.no_update
    df = read_file(contents)
    filtered_df = df[df['Year'] == selected_year]
    country_counts = filtered_df['Lead Source'].value_counts().reset_index()
    country_counts.columns = ['Lead Source', 'Lead Count']

    missing_data_count = len(filtered_df[filtered_df['Lead Source'].isna()]) 
    fig = px.pie(country_counts, names='Lead Source', values='Lead Count', title='Lead Source-wise Lead Distribution')
    return fig, f"Missing Lead Source Data Count: {missing_data_count}"

# ------------------------------------------------------------------------------------------------------------------------------

@app.callback(
        Output('contact-owner-pie-chart', 'figure'),
        Output('missing-contactowner-count', 'children'),
        Input('upload-data', 'contents'),
        Input('year-input', 'value'),
        Prevent_initial_call = True,      
)
def make_pie_chart(contents, selected_year):
    if contents is None:
        return dash.no_update, dash.no_update
    df = read_file(contents)
    filtered_df = df[df['Year'] == selected_year]
    country_counts = filtered_df['Contact owner'].value_counts().reset_index()
    country_counts.columns = ['Contact owner', 'Lead Count']

    missing_data_count = len(filtered_df[filtered_df['Contact owner'].isna()]) 
    fig = px.pie(country_counts, names='Contact owner', values='Lead Count', title='Contact Owner-wise Lead Distribution')
    return fig, f"Missing Contact Owner Data Count: {missing_data_count}"
# ------------------------------------------------------------------------------------------------------------------------------

@app.callback(
        Output('lead-status-pie-chart', 'figure'),
        Output('missing-leadstatus-count', 'children'),
        Input('upload-data', 'contents'),
        Input('year-input', 'value'),
        Prevent_initial_call = True,      
)
def make_pie_chart(contents, selected_year):
    if contents is None:
        return dash.no_update, dash.no_update
    df = read_file(contents)
    filtered_df = df[df['Year'] == selected_year]
    country_counts = filtered_df['Lead Status'].value_counts().reset_index()
    country_counts.columns = ['Lead Status', 'Lead Count']

    missing_data_count = len(filtered_df[filtered_df['Lead Status'].isna()]) 
    fig = px.pie(country_counts, names='Lead Status', values='Lead Count', title='Lead Status-wise Lead Distribution')
    return fig, f"Missing Lead Status Data Count: {missing_data_count}"
# ------------------------------------------------------------------------------------------------------------------------------

@app.callback(
        Output('month-pie-chart', 'figure'),
        Input('upload-data', 'contents'),
        Input('year-input', 'value'),
        Prevent_initial_call = True,      
)
def make_pie_chart(contents, selected_year):
    if contents is None:
        return dash.no_update
    df = read_file(contents)
    filtered_df = df[df['Year'] == selected_year].copy()
    filtered_df['Create Date'] = pd.to_datetime(filtered_df['Create Date'])
    filtered_df['Month'] = filtered_df['Create Date'].dt.strftime('%B')
    month_counts = filtered_df['Month'].value_counts().reset_index()
    month_counts.columns = ['Month', 'Lead Count']
    fig = px.pie(month_counts, names='Month', values='Lead Count', title='Create Date-wise Lead Distribution')
    return fig
# ------------------------------------------------------------------------------------------------------------------------------

@app.callback(
        Output('age-pie-chart', 'figure'),
        # Output('inconsistent-values', 'children'),
        Input('upload-data', 'contents'),
        Input('year-input', 'value'),
        Prevent_initial_call = True,      
)
def make_pie_chart(contents, selected_year):
    if contents is None:
        return dash.no_update#, dash.no_update
    
    df = read_file(contents)
    filtered_df = df[df['Year'] == selected_year].copy()
    filtered_df['Age of your Child'] = pd.to_numeric(filtered_df['Age of your Child'], errors='coerce') #convert inconsistent values to NaN
    # inconsistent_values = filtered_df.loc[filtered_df['Age of your Child'].isna(), 'Age of your Child'] #track inconsistent values 
    def categorize_age(age):
        if age <= 10:
            return "Ages <= 10"
        elif 11 <= age <= 19:
            return "11 <= Ages <= 19"
        elif 20 <= age <= 22:
            return "20 <= Ages <= 22"
        else:
            return "Age > 22"

    filtered_df['Age Group'] = filtered_df['Age of your Child'].apply(categorize_age)
    age_group_counts = filtered_df['Age Group'].value_counts().reset_index()
    age_group_counts.columns = ['Age Group', 'Lead Count']

    fig = px.pie(age_group_counts, names='Age Group', values='Lead Count', title='Age-wise Lead Distribution')
    return fig#, inconsistent_values.to_string(index=False)
    # inconsistent_values_str = '\n'.join(inconsistent_values.dropna().astype(str))
    # if inconsistent_values_str:
    #     inconsistent_values_output = f"Inconsistent values: \n{inconsistent_values_str}"
    # else:
    #     inconsistent_values_output = "No inconsistent values found."

    # return fig, inconsistent_values_output
    
# ------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)
