
# install XlsxWriter

# ------------------------------------------------------------------------------------------------------------------------------

import dash 
from dash.dependencies import Input, Output
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
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
    df.insert(0, 'SNo', range(1, len(df) + 1))
    df.set_index('Record ID', inplace=True, drop = False)
    df['Create Date'] = pd.to_datetime(df['Create Date']) 
    df['Year'] = df['Create Date'].dt.year
    df['Phone Number'] = df['Phone Number'].str.replace(' ', '').str[-10:] #extract last 10 digits after removing extra spaces, to remove any country codes
    df['Lead Source'].fillna("Facebook", inplace = True)

    # print(df['Year'])
    # print(df.columns)

    return df
# ------------------------------------------------------------------------------------------------------------------------------

app = dash.Dash(__name__, prevent_initial_callbacks=True)

# ------------------------------------------------------------------------------------------------------------------------------

app.layout = html.Div([
    html.Div(id='upload-container', 
             className='centered-container', 
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
    html.Br(),
    html.Br(),
    html.Div([
        dcc.Input(id='year-input',
                  type='number',
                  placeholder='Enter year',
                  value=2023,  
                ),
            ]),
    html.Br(),
    html.Br(),
    html.Div([  
        dbc.Select( 
            id='month-dropdown',
            options=[{'label': 'January', 'value': '01'},
                     {'label': 'February', 'value': '02'},
                     {'label': 'March', 'value': '03'},
                     {'label': 'April', 'value': '04'},
                     {'label': 'May', 'value': '05'},
                     {'label': 'June', 'value': '06'},
                     {'label': 'July', 'value': '07'},
                     {'label': 'August', 'value': '08'},
                     {'label': 'September', 'value': '09'},
                     {'label': 'October', 'value': '10'},
                     {'label': 'November', 'value': '11'},
                     {'label': 'December', 'value': '12'}
                ],
            placeholder='Select a month...',
            style={'width': '90%', 'margin': '15px'},
            className="px-2 border")
        ]),
    html.Br(),
    html.Br(),
    dcc.Loading(
        id="loading-output",
        type="default",
        children=[html.Div(id='data-table-component')],
    ), 
    html.Br(),
    html.Br(),
    html.Div([
        html.Button("View duplicate records", id='view-duplicate-button'),
        dcc.Loading(
        id="loading-output-1",
        type="default",
        children=[html.Div(id='view-duplicate-records')],
    ),
        ]),
    html.Br(),
    html.Br(),
    html.Div([
        html.Button("Download missing Contact Owner records", id='download-missing-contact-owner-button'),
        dcc.Loading(
        id="loading-output-2",
        type="default",
        children=[html.Div(id='view-missing-contact-owner-records')],
    ),
        dcc.Download(id='download-missing-contact-owner-records'),
        ]),
    html.Br(),
    html.Br(),
    html.Div(id='bar-container'),
    dcc.Graph(id='country-map'),
    html.Div([
        html.Div([
            dcc.Graph(id = 'country-pie-chart'),
            html.Div(id='missing-country-count')]),

        html.Div([
            dcc.Graph(id = 'lead-source-pie-chart'),
            html.Div(id='missing-leadsource-count')]),

        html.Div([
            dcc.Graph(id = 'contact-owner-pie-chart'),
            html.Div(id='missing-contactowner-count')]),

        html.Div([
            dcc.Graph(id = 'lead-status-pie-chart'),
            html.Div(id='missing-leadstatus-count')]),

        dcc.Graph(id = 'month-pie-chart'),

        html.Div([
            dcc.Graph(id = 'age-pie-chart'),
            html.Div(id='inconsistent-values')]),
        ]),
])

# ------------------------------------------------------------------------------------------------------------------------------

# callback to display entire datatable based on year input

@app.callback(
        Output('data-table-component', 'children'),
        Input('upload-data', 'contents'),   
        Input('year-input', 'value'),   
        
)
def make_table(contents, selected_year):
    if contents is None:
        return dash.no_update
    
    raw_df = read_file(contents)
    df = raw_df[raw_df['Year'] == selected_year]
    # print(df.Year)
    table = dash_table.DataTable(
                            id='datatable-interactivity',
                            columns=[{
                                "name": i,
                                "id": i,
                                "deletable": False if i in ["Record ID", "SNo"] else True,  # "Record ID" not deletable
                                "selectable": True,
                                "hideable": True
                            }for i in df.columns],
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
                            style_data={                # overflow cell contents into multiple lines
                                'whiteSpace': 'normal',
                                'height': 'auto'
                            }
                        )
    return table

# ------------------------------------------------------------------------------------------------------------------------------
# callback to display duplicate records

@app.callback(
        Output('view-duplicate-records', 'children'),
        Input('upload-data', 'contents'),
        Input('year-input', 'value'), 
        Input('view-duplicate-button', 'n_clicks'),
        Prevent_initial_call = True
)
def display_duplicate_records(contents, selected_year, n_clicks):
    if contents is None or n_clicks is None:
        return dash.no_update
    
    raw_df = read_file(contents)
    df = raw_df[raw_df['Year'] == selected_year]
    # duplicate_phone = df[df.duplicated('Phone Number', keep = False)]

    phone_without_null = df[df['Phone Number'].notnull()]
    duplicate_phone = phone_without_null[phone_without_null.duplicated('Phone Number', keep = False)]
    
    # print(duplicate_phone['Phone Number'])
    # print("..")
    duplicate_email = df[df.duplicated('Email', keep = False)]
    # print(duplicate_email['Email'])

    duplicates = pd.concat([duplicate_phone, duplicate_email])

    
    return dash_table.DataTable(
        id='duplicate-records-table',
        columns=[{'name': col, 'id': col} for col in duplicates.columns],
        data=duplicates.to_dict('records')
    )

# ------------------------------------------------------------------------------------------------------------------------------

#callback to view and download missing contact owner data

@app.callback(
        Output('view-missing-contact-owner-records', 'children'),
        Output('download-missing-contact-owner-records', 'data'),
        Input('upload-data', 'contents'),
        Input('year-input', 'value'), 
        Input('download-missing-contact-owner-button', 'n_clicks'), 
        Prevent_initial_call = True,     
)
def display_and_download_missing_contact_owner_records(contents, selected_year, n_clicks):
    if n_clicks is None or contents is None:
        return dash.no_update, dash.no_update
    
    raw_df = read_file(contents)
    df = raw_df[raw_df['Year'] == selected_year]

    missing_contact_owner = df[df['Contact owner'].isna()]
    missing_contact_owner_table = dash_table.DataTable(id = 'duplicates-table',
                                            columns = [{
                                                "name": i,
                                                "id": i,
                                                "deletable": False if i in ["Record ID", "SNo"] else True,
                                                "selectable": True,
                                                "hideable": True
                                            }for i in missing_contact_owner.columns],
                                            data = missing_contact_owner.to_dict('records'),
                                            editable=False,
                                            filter_action="native",     
                                            sort_action="native",       
                                            sort_mode="single",           
                                            row_deletable=False,         
                                            page_action="native",
                                            style_cell={'minWidth': 95, 'maxWidth': 95, 'width': 95},
                                            style_data={'whiteSpace': 'normal',}
                                        )
    def to_xlsx(bytes_io):
        xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")  
        missing_contact_owner.to_excel(xslx_writer, index=False, sheet_name="sheet1")
        xslx_writer.close()

    return missing_contact_owner_table, dcc.send_bytes(to_xlsx, "missing_contact_owner_records.xlsx")

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
    country_counts = filtered_df['Country/Region'].value_counts().reset_index()
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
        Input('upload-data', 'contents'),
        Input('year-input', 'value'),
        Prevent_initial_call = True,      
)
def make_pie_chart(contents, selected_year):
    if contents is None:
        return dash.no_update
    
    df = read_file(contents)
    filtered_df = df[df['Year'] == selected_year].copy()
    filtered_df['Age of your Child'] = pd.to_numeric(filtered_df['Age of your Child'], errors='coerce')
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
    return fig
# ------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=True)
