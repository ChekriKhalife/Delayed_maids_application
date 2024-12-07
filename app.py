import dash
from dash import html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import base64
import io

# Constants
TASK_THRESHOLDS = {
    'Apply for Work Permit - Stage 1': 168,
    'Pay MOHRE Insurance': 24,
    'Pay Work Permit Fees - Stage 2': 24,
    'Check Work Permit Approval - Stage 1': 48,
    'Check Work Permit Approval - Stage 2': 24,
    'Fix Work Permit Issues - Stage -1': 24,
    'Fix work permit issues - stage 2': 24,
    'Apply for entry Visa': 24,
    'Check Entry Visa Immigration Approval': 24,
    'Change of Status': 24,
    'Upload Change of status': 24,
    'Prepare EID application (Receival Automated)': 96,
    'Approve signed Offer Letter': 24,
    'Apply for R-visa': 24,
    'Upload The e-Residency': 24,
    'Check ID application type': 24,
    'Modify eid application': 240,
    'Prepare EID Application for Modification': 48,
    'Prepare medical application': 48,
    'Prepare folder containing E-visa medical application and EID': 72,
    'Receival of EID Card': 168
}

class DelayedMaidsAnalytics:
    def __init__(self):
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[
                dbc.themes.FLATLY,
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
            ],
            title="Delayed Cases Analytics"
        )
        self.df = pd.DataFrame()

    def process_data(self, df):
        """Process the uploaded data with proper handling of all fields."""
        try:
            df = df.copy()
            df.columns = df.columns.str.strip()
            
            required_columns = ['Housemaid ID', 'Current Stage']
            df = df.dropna(subset=required_columns)
            
            # Handle numeric fields
            df['RPA try count'] = pd.to_numeric(df['RPA try count'], errors='coerce').fillna(0).astype(int)
            df['Time in Stage'] = pd.to_numeric(df['Time in Stage'], errors='coerce').fillna(0)
            
            # Handle text fields
            text_fields = {
                'Client Note': 'STANDARD',
                'Error resolver page?': 'No',
                'Latest Note': '',
                'User': '',
                'Note Time': '',
                'Last RPA try time': '',
                'Nationality': 'Unknown',
                'Type': 'Unknown',
                'Portal Passport status': 'Unknown',
                'Photo Status': 'Unknown',
                'Docs status': 'Unknown'
            }
            
            for field, default in text_fields.items():
                if field in df.columns:
                    df[field] = df[field].astype(str).replace('nan', default).fillna(default)
            
            # Calculate delays and severity
            df['Threshold (in hours)'] = df['Current Stage'].map(TASK_THRESHOLDS).fillna(24)
            df['Delay (hours)'] = (df['Time in Stage'] - df['Threshold (in hours)']).fillna(0)
            
            # Calculate severity based on how much they've exceeded their threshold
            df['Threshold Ratio'] = df['Time in Stage'] / df['Threshold (in hours)']
            df['Severity'] = pd.cut(
                df['Threshold Ratio'],
                bins=[0, 1.5, 2, 3, float('inf')],
                labels=['Low', 'Medium', 'High', 'Critical']
            ).fillna('Low')
            
            # Calculate priority score
            df['Priority Score'] = df.apply(self._calculate_priority, axis=1)
            
            # Calculate total delay per housemaid
            df['Total Delay (hours)'] = df.groupby('Housemaid ID')['Delay (hours)'].transform('sum')
            
            return df
            
        except Exception as e:
            print(f"Error in data processing: {str(e)}")
            raise

    def _calculate_priority(self, row):
        """Calculate priority score with enhanced logic."""
        try:
            base_score = row['Threshold Ratio'] * 100
            
            multiplier = 1.0
            if row['Client Note'] == 'SUPER_ANGRY_CLIENT':
                multiplier = 2.5
            elif row['Client Note'] == 'PRIORITIZE_VISA':
                multiplier = 1.8
            elif row['Client Note'] == 'AMNESTY':
                multiplier = 1.5
            
            if str(row['Error resolver page?']).lower() == 'yes':
                multiplier *= 1.3
            
            if row['RPA try count'] > 3:
                multiplier *= 1.2
                
            return round(base_score * multiplier)
            
        except Exception:
            return 0

    def create_layout(self):
        """Create enhanced layout focusing on priority analysis and detailed cases."""
        self.app.layout = html.Div([
            # Header
            dbc.Navbar(
                dbc.Container([
                    html.H2("Delayed Cases Analytics", className="text-white mb-0"),
                    dcc.Upload(
                        id='upload-data',
                        children=dbc.Button(
                            ["Upload Excel ", html.I(className="fas fa-upload")],
                            color="light",
                            className="me-2"
                        ),
                        multiple=False
                    ),
                    html.Span(id='last-update', className="text-white ms-2")
                ]),
                color="primary",
                dark=True,
                className="mb-3"
            ),

            dbc.Container([
                # Alert area
                html.Div(id='alerts-area', className="mb-3"),

                # Enhanced Filters
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Filters", className="card-title mb-3"),
                        dbc.Row([
                            dbc.Col(
                                dcc.Dropdown(
                                    id='stage-filter',
                                    placeholder="Filter by Stage",
                                    multi=True,
                                    className="mb-2"
                                ),
                                md=3
                            ),
                            dbc.Col(
                                dcc.Dropdown(
                                    id='type-filter',
                                    placeholder="Filter by Type",
                                    multi=True,
                                    className="mb-2"
                                ),
                                md=3
                            ),
                            dbc.Col(
                                dcc.Dropdown(
                                    id='nationality-filter',
                                    placeholder="Filter by Nationality",
                                    multi=True,
                                    className="mb-2"
                                ),
                                md=3
                            ),
                            dbc.Col(
                                dcc.Dropdown(
                                    id='client-note-filter',
                                    options=[
                                        {'label': '🔥 Super Angry Clients', 'value': 'SUPER_ANGRY_CLIENT'},
                                        {'label': '⚡ Priority Visa', 'value': 'PRIORITIZE_VISA'},
                                        {'label': '📋 Amnesty', 'value': 'AMNESTY'},
                                        {'label': 'Standard', 'value': 'STANDARD'}
                                    ],
                                    placeholder="Filter by Client Priority",
                                    multi=True,
                                    className="mb-2"
                                ),
                                md=3
                            )
                        ]),
                        
                    ])
                ], className="mb-4 sticky-top bg-white", style={'zIndex': 1000}),

                # Severity Legend
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Understanding Severity Levels:", className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Div(className="d-flex align-items-center mb-2", children=[
                                    html.Div(className="me-2", style={'width': '20px', 'height': '20px', 'backgroundColor': '#2196f3'}),
                                    html.Span("Low: Up to 50% over threshold")
                                ]),
                                html.Div(className="d-flex align-items-center mb-2", children=[
                                    html.Div(className="me-2", style={'width': '20px', 'height': '20px', 'backgroundColor': '#fdd835'}),
                                    html.Span("Medium: 50-100% over threshold")
                                ])
                            ], md=6),
                            dbc.Col([
                                html.Div(className="d-flex align-items-center mb-2", children=[
                                    html.Div(className="me-2", style={'width': '20px', 'height': '20px', 'backgroundColor': '#f57c00'}),
                                    html.Span("High: 100-200% over threshold")
                                ]),
                                html.Div(className="d-flex align-items-center mb-2", children=[
                                    html.Div(className="me-2", style={'width': '20px', 'height': '20px', 'backgroundColor': '#d32f2f'}),
                                    html.Span("Critical: Over 200% threshold")
                                ])
                            ], md=6)
                        ])
                    ])
                ], className="mb-4"),

                # KPI Cards
                dbc.Row(id='kpi-cards', className="mb-4"),

                # Client Priority Analysis
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Client Priority Analysis"),
                            dbc.CardBody([
                                dcc.Graph(id='client-priority-chart'),
                                html.Hr(),
                                dcc.Graph(id='priority-stage-chart')
                            ])
                        ])
                    ], width=12)
                ], className="mb-4"),

                # Enhanced Detailed Cases Table
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col(html.H5("Detailed Cases Overview"), md=3),
                            dbc.Col([
                                dbc.Input(
                                    id='table-search',
                                    type='text',
                                    placeholder='Search cases...',
                                    className="mb-2"
                                )
                            ], md=3),
                            dbc.Col([
                                dcc.Dropdown(
                                    id='table-sort-field',
                                    options=[
                                        {'label': 'Total Delay', 'value': 'Total Delay (hours)'},
                                        {'label': 'Current Delay', 'value': 'Delay (hours)'},
                                        {'label': 'Priority Score', 'value': 'Priority Score'},
                                        {'label': 'Time in Stage', 'value': 'Time in Stage'}
                                    ],
                                    value='Total Delay (hours)',
                                    placeholder="Sort by...",
                                    className="mb-2"
                                )
                            ], md=3),
                            dbc.Col([
                                dbc.Select(
                                    id='records-per-page',
                                    options=[
                                        {'label': '10 records', 'value': 10},
                                        {'label': '25 records', 'value': 25},
                                        {'label': '50 records', 'value': 50},
                                        {'label': '100 records', 'value': 100}
                                    ],
                                    value=25,
                                    className="mb-2"
                                )
                            ], md=3)
                        ])
                    ]),
                    dbc.CardBody([
                        dash_table.DataTable(
                        id='detailed-table',
                        filter_action="native",
                        sort_action="native",
                        sort_mode="multi",
                        sort_by=[{'column_id': 'Time in Stage', 'direction': 'desc'}],  # Set default sorting
                        page_action="native",
                        page_current=0,
                        page_size=25,
                            style_table={'overflowX': 'auto'},
                            style_header={
                                'backgroundColor': '#f8f9fa',
                                'fontWeight': 'bold',
                                'textAlign': 'center'
                            },
                            style_cell={
                                'textAlign': 'left',
                                'padding': '10px',
                                'fontSize': '14px'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'column_id': 'Client Note', 'filter_query': '{Client Note} = "SUPER_ANGRY_CLIENT"'},
                                    'backgroundColor': '#ffebee',
                                    'color': '#c62828',
                                    'fontWeight': 'bold'
                                },
                                {
                                    'if': {'column_id': 'Client Note', 'filter_query': '{Client Note} = "PRIORITIZE_VISA"'},
                                    'backgroundColor': '#fff3e0',
                                    'color': '#ef6c00'
                                },
                                {
                                    'if': {'column_id': 'Client Note', 'filter_query': '{Client Note} = "AMNESTY"'},
                                    'backgroundColor': '#e8f5e9',
                                    'color': '#2e7d32'
                                },
                                {
                                    'if': {'column_id': 'Severity', 'filter_query': '{Severity} = "Critical"'},
                                    'backgroundColor': '#ffebee',
                                    'color': '#c62828'
                                },
                                {
                                    'if': {'column_id': 'Severity', 'filter_query': '{Severity} = "High"'},
                                    'backgroundColor': '#fff3e0',
                                    'color': '#ef6c00'
                                }
                            ],
                            export_format="csv"
                        )
                    ])
                ])
            ])
        ])

    def setup_callbacks(self):
        @self.app.callback(
            [Output('kpi-cards', 'children'),
            Output('client-priority-chart', 'figure'),
            Output('priority-stage-chart', 'figure'),
            Output('detailed-table', 'data'),
            Output('detailed-table', 'columns'),
            Output('stage-filter', 'options'),
            Output('type-filter', 'options'),
            Output('nationality-filter', 'options'),
            Output('last-update', 'children'),
            Output('alerts-area', 'children')],
            [Input('upload-data', 'contents'),
            Input('stage-filter', 'value'),
            Input('type-filter', 'value'),
            Input('nationality-filter', 'value'),
            Input('client-note-filter', 'value'),
            Input('table-search', 'value'),
            Input('table-sort-field', 'value'),
            Input('records-per-page', 'value')],
            [State('upload-data', 'filename')]
        )
        def update_dashboard(contents, stage_filter, type_filter, nationality_filter,
                        client_note_filter, search_value, sort_field,
                        records_per_page, filename):
            # Initialize outputs
            empty_returns = [[], {}, {}, [], [], [], [], [], "", None]
            
            if contents is None:
                return empty_returns

            try:
                # Process uploaded file
                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string)
                
                if filename.endswith('.xlsx'):
                    self.df = pd.read_excel(io.BytesIO(decoded))
                elif filename.endswith('.csv'):
                    self.df = pd.read_csv(io.BytesIO(decoded))
                else:
                    raise ValueError("Unsupported file format")
                
                self.df = self.process_data(self.df)
            except Exception as e:
                return empty_returns[:-1] + [
                    dbc.Alert(f"Error processing file: {str(e)}", color="danger", dismissable=True)
                ]

            # Apply filters
            filtered_df = self.df.copy()
            
            # Basic filters
            if stage_filter:
                filtered_df = filtered_df[filtered_df['Current Stage'].isin(stage_filter)]
            if type_filter:
                filtered_df = filtered_df[filtered_df['Type'].isin(type_filter)]
            if nationality_filter:
                filtered_df = filtered_df[filtered_df['Nationality'].isin(nationality_filter)]
            if client_note_filter:
                filtered_df = filtered_df[filtered_df['Client Note'].isin(client_note_filter)]
                
            # Search filter
            if search_value:
                search = search_value.lower()
                filtered_df = filtered_df[
                    filtered_df.astype(str).apply(lambda x: x.str.lower()).apply(
                        lambda x: x.str.contains(search, na=False)
                    ).any(axis=1)
                ]

            # Create visualizations
            kpi_cards = self.create_kpi_cards(filtered_df)
            client_priority_fig = self.create_client_priority_chart(filtered_df)
            priority_stage_fig = self.create_priority_stage_chart(filtered_df)

            # Sort by Time in Stage by default
            filtered_df = filtered_df.sort_values('Time in Stage', ascending=False)
            
            # Additional sorting if specified
            if sort_field:
                filtered_df = filtered_df.sort_values(sort_field, ascending=False)
            
            table_data = filtered_df.to_dict('records')
            columns = [{'name': i, 'id': i} for i in filtered_df.columns]

            # Create filter options
            stage_options = [{'label': x, 'value': x} for x in sorted(self.df['Current Stage'].unique())]
            type_options = [{'label': x, 'value': x} for x in sorted(self.df['Type'].unique())]
            nationality_options = [{'label': x, 'value': x} for x in sorted(self.df['Nationality'].unique())]

            # Update time
            update_time = f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            return (
                kpi_cards, client_priority_fig, priority_stage_fig,
                table_data, columns, stage_options, type_options, nationality_options,
                update_time, None
            )

    def create_kpi_cards(self, df):
        """Create enhanced KPI cards with key metrics."""
        total_cases = len(df)
        if total_cases == 0:  # Handle empty dataframe case
            return [
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.H3("0", className="text-primary"),
                            html.P("Total Delayed Cases", className="mb-1"),
                            html.Div([
                                html.I(className="fas fa-users me-2"),
                                html.Span("0% Critical")
                            ], className="text-muted small")
                        ])
                    ], className="border-start border-primary border-4 shadow-sm h-100")
                ) for _ in range(4)  # Create 4 empty cards
            ]
        
        avg_delay = df['Delay (hours)'].mean()
        critical_cases = len(df[df['Severity'] == 'Critical'])
        angry_clients = len(df[df['Client Note'] == 'SUPER_ANGRY_CLIENT'])
        
        cards = [
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{total_cases:,}", className="text-primary"),
                        html.P("Total Delayed Cases", className="mb-1"),
                        html.Div([
                            html.I(className="fas fa-users me-2"),
                            html.Span(f"{(critical_cases/total_cases*100):.1f}% Critical")
                        ], className="text-muted small")
                    ])
                ], className="border-start border-primary border-4 shadow-sm h-100")
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{angry_clients:,}", className="text-danger"),
                        html.P("Super Angry Clients", className="mb-1"),
                        html.Div([
                            html.I(className="fas fa-exclamation-circle me-2"),
                            html.Span(f"{(angry_clients/total_cases*100):.1f}% of Total")
                        ], className="text-danger small")
                    ])
                ], className="border-start border-danger border-4 shadow-sm h-100")
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{avg_delay:.1f}", className="text-warning"),
                        html.P("Average Delay (Hours)", className="mb-1"),
                        html.Div([
                            html.I(className="fas fa-clock me-2"),
                            html.Span("Hours per Case")
                        ], className="text-warning small")
                    ])
                ], className="border-start border-warning border-4 shadow-sm h-100")
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{critical_cases:,}", className="text-danger"),
                        html.P("Critical Cases", className="mb-1"),
                        html.Div([
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            html.Span(f"Exceeded threshold by >200%")
                        ], className="text-danger small")
                    ])
                ], className="border-start border-danger border-4 shadow-sm h-100")
            )
        ]
        return cards

    def create_client_priority_chart(self, df):
        """Create enhanced client priority distribution chart."""
        priority_metrics = df.groupby('Client Note').agg({
            'Delay (hours)': ['mean', 'count', 'sum'],
            'Priority Score': 'mean'
        }).reset_index()
        
        priority_metrics.columns = ['Client Note', 'Avg Delay', 'Count', 'Total Delay', 'Avg Priority']
        
        priority_order = ['SUPER_ANGRY_CLIENT', 'PRIORITIZE_VISA', 'AMNESTY', 'STANDARD']
        priority_metrics['Client Note'] = pd.Categorical(
            priority_metrics['Client Note'], 
            categories=priority_order, 
            ordered=True
        )
        priority_metrics = priority_metrics.sort_values('Client Note')
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Average Delay',
            x=priority_metrics['Client Note'],
            y=priority_metrics['Avg Delay'],
            text=priority_metrics['Count'].apply(lambda x: f'Cases: {x}'),
            textposition='auto',
            marker_color=['#d32f2f', '#f57c00', '#388e3c', '#1976d2'],
            hovertemplate=(
                '<b>%{x}</b><br>' +
                'Average Delay: %{y:.1f} hours<br>' +
                '%{text}<br>' +
                'Total Delay: %{customdata[0]:.0f} hours<br>' +
                'Avg Priority Score: %{customdata[1]:.0f}<br>' +
                '<extra></extra>'
            ),
            customdata=np.column_stack((
                priority_metrics['Total Delay'],
                priority_metrics['Avg Priority']
            ))
        ))
        
        fig.update_layout(
            title=None,
            xaxis_title="Client Priority Level",
            yaxis_title="Average Delay (hours)",
            showlegend=False,
            height=300,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        
        return fig

    def create_priority_stage_chart(self, df):
        """Create enhanced priority stage distribution chart showing case counts."""
        if len(df) == 0:  # Handle empty dataframe case
            return go.Figure()
        
        # Create pivot table with counts instead of delays
        pivot_data = pd.crosstab(
            df['Current Stage'],
            df['Client Note']
        ).fillna(0)
        
        # Sort by total cases
        total_cases = pivot_data.sum(axis=1)
        pivot_data = pivot_data.loc[total_cases.sort_values(ascending=True).index]
        pivot_data = pivot_data.tail(10)  # Show top 10 stages by case count
        
        fig = go.Figure()
        
        colors = {
            'SUPER_ANGRY_CLIENT': '#d32f2f',
            'PRIORITIZE_VISA': '#f57c00',
            'AMNESTY': '#388e3c',
            'STANDARD': '#1976d2'
        }
        
        for client_type in pivot_data.columns:
            fig.add_trace(go.Bar(
                name=client_type,
                y=pivot_data.index,
                x=pivot_data[client_type],
                orientation='h',
                marker_color=colors.get(client_type, '#000000'),
                hovertemplate=(
                    '<b>%{y}</b><br>' +
                    f'{client_type}<br>' +
                    'Number of Cases: %{x}<br>' +
                    '<extra></extra>'
                )
            ))
        
        fig.update_layout(
            title=None,
            barmode='stack',
            height=400,
            margin=dict(l=20, r=20, t=20, b=20),
            legend_title="Client Priority",
            xaxis_title="Number of Cases",
            yaxis={'categoryorder': 'total ascending'},
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            showlegend=True
        )
        
        fig.update_yaxes(
            tickfont=dict(size=10),
            tickangle=0
        )
        
        return fig

    def add_custom_css(self):
        """Add enhanced custom CSS styles."""
        custom_css = """
            .sticky-top {
                top: 20px;
                z-index: 1000;
            }
            
            .card {
                border: none;
                border-radius: 10px;
                box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important;
                margin-bottom: 1.5rem !important;
                transition: all 0.3s ease-in-out;
            }
            
            .card:hover {
                transform: translateY(-2px);
            }
            
            .card-header {
                background-color: white;
                border-bottom: 1px solid rgba(0,0,0,.125);
                padding: 1rem;
            }
            
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td {
                font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
                font-size: 14px;
                padding: 8px;
            }
            
            .dropdown-container .Select-control {
                border-radius: 5px;
            }
            
            .dash-table-container {
                overflow-x: auto;
            }
            
            .dash-filter input {
                border-radius: 5px;
            }
        """
        self.app.index_string = self.app.index_string.replace(
            '</head>',
            f'<style>{custom_css}</style></head>'
        )

    def run_server(self, debug=True, port=8050, host='0.0.0.0'):
        """Run the Dash server with startup message."""
        self.create_layout()
        self.setup_callbacks()
        self.add_custom_css()
        print("""
        ╔════════════════════════════════════════════╗
        ║     Delayed Cases Analytics Dashboard      ║
        ╠════════════════════════════════════════════╣
        ║ Starting server at http://localhost:8050   ║
        ║ Press Ctrl+C to quit                       ║
        ╚════════════════════════════════════════════╝
        """)
        self.app.run_server(debug=debug, port=port, host=host)


app = DelayedMaidsAnalytics()
app.create_layout()
app.setup_callbacks()
app.add_custom_css()

if __name__ == '__main__':
    app.run_server()
