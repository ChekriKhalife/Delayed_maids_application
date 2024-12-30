import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import plotly.graph_objects as go
import base64
import io
import dash_bootstrap_components as dbc
from typing import List, Dict, Any
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials
from dataclasses import dataclass
import json
import traceback

# Initialize the Dash app with a modern Bootstrap theme
app = dash.Dash(__name__, 
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
    ]
)
server = app.server  # Expose the Flask server for deployment
# Custom CSS for enhanced visual design
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Modern color palette */
            :root {
                --primary-color: #2C3E50;
                --secondary-color: #34495E;
                --accent-color: #3498DB;
                --success-color: #27AE60;
                --warning-color: #F39C12;
                --danger-color: #E74C3C;
                --light-bg: #F8F9FA;
                --dark-bg: #343A40;
            }
            /* Accordion Enhancements */
                .accordion-button {
                    background-color: var(--light-bg) !important;
                    border-radius: 12px !important;
                    padding: 1rem 1.5rem !important;
                    font-size: 1.1rem !important;
                    font-weight: 500 !important;
                    color: var(--primary-color) !important;
                    box-shadow: none !important;
                }

                .accordion-button:not(.collapsed) {
                    background-color: white !important;
                    color: var(--accent-color) !important;
                }

                .accordion-item {
                    border: 1px solid #dee2e6 !important;
                    border-radius: 12px !important;
                    margin-bottom: 1rem !important;
                    overflow: hidden !important;
                }

                .accordion-body {
                    padding: 1.5rem !important;
                }
            /* Enhanced Typography */
            body {
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                background-color: var(--light-bg);
                color: var(--primary-color);
            }
            
            /* Card Enhancements */
            .dash-card {
                border-radius: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: transform 0.2s, box-shadow 0.2s;
                background: white;
                margin-bottom: 1.5rem;
            }
            
            .dash-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            
            /* Metric Cards */
            .metric-card {
                padding: 1.5rem;
                text-align: center;
                border-radius: 12px;
                background: white;
            }
            
            .metric-card i {
                font-size: 2rem;
                margin-bottom: 1rem;
            }
            
            .metric-value {
                font-size: 2rem;
                font-weight: bold;
                margin-bottom: 0.5rem;
            }
            
            .metric-label {
                color: var(--secondary-color);
                font-size: 0.9rem;
            }
            
            /* Enhanced Tables */
            .dash-table-container {
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .dash-spreadsheet-container .dash-spreadsheet-inner td,
            .dash-spreadsheet-container .dash-spreadsheet-inner th {
                padding: 12px 16px !important;
                border-color: #e9ecef !important;
            }
            
            /* Filter Panels */
            .filter-panel {
                background: white;
                padding: 1.5rem;
                border-radius: 12px;
                margin-bottom: 1.5rem;
            }
            
            /* Upload Zone */
            .upload-zone {
                border: 2px dashed #dee2e6;
                border-radius: 12px;
                padding: 2rem;
                text-align: center;
                background: white;
                transition: border-color 0.2s;
            }
            
            .upload-zone:hover {
                border-color: var(--accent-color);
            }
            
            /* Status Badges */
            .status-badge {
                padding: 0.25rem 0.75rem;
                border-radius: 50px;
                font-size: 0.85rem;
                font-weight: 500;
            }
            
            /* Animations */
            .fade-in {
                animation: fadeIn 0.3s ease-in;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Define User and UserManager classes for Manage Users functionality
@dataclass
class User:
    name: str
    google_sheet_id: str
    active: bool = True
    workload: int = 0

class UserManager:
    def __init__(self):
        self.users: Dict[str, User] = {
            "razan.hassan": User(
                name="Razan Hassan",
                google_sheet_id="14dpPJUFwMXTFemq8b2as3Jpwj_Qs-kplradlM63lS_U"
            ),
            "aya.tahawi": User(
                name="Aya Tahawi",
                google_sheet_id="1hkB77aTFTalcZtUG9xfNKH3b7nIgYAZP1-AF6Ob7szE"
            ),
            "maya.dayoub": User(
                name="Maya Dayoub",
                google_sheet_id="1fDaIXfSGEKlUTlVprS7_SjG1wbhaGk1kVLvZXTia6QU"
            ),
            "laila.alhafi": User(
                name="Laila Alhafi",
                google_sheet_id="1nCzh8FMZOGa2x7v_OLIUtVEtAc4hzUG3f-rIgHJgEF8"
            ),
            "ehab.joud": User(
                name="Ehab Joud",
                google_sheet_id="1WccFTrR-Izh4qpRSnDD9A_nq8MWm0l54fqFJu4eJPYY"
            ),
            "hala.khaddour": User(
                name="Hala Khaddour",
                google_sheet_id="1_zM3sANFMHXvjSFvIHCtG2sKiS7GBWk8haUCoYBm1XU"
            ),
            "marah.ghanem": User(
                name="Marah Ghanem",
                google_sheet_id="1z88anA3_FKx6xo3fc4bci22-J8naoiEYdbcK8eiN8CM"
            )
        }
        self.setup_google_sheets()

    def setup_google_sheets(self):
        """Initialize Google Sheets connection"""
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        # Add your credentials file path
        service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not service_account_json:
            raise ValueError("Environment variable GOOGLE_SERVICE_ACCOUNT_JSON is missing")
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            json.loads(service_account_json), scope
        )
        self.client = gspread.authorize(creds)

    def distribute_data(self, usernames: list, data: pd.DataFrame) -> dict:
        """Distribute data evenly among users."""
        results = {}
        for username in usernames:
            if username in self.users:
                sheet = self.client.open_by_key(self.users[username].google_sheet_id).sheet1
                sheet.clear()
                sheet.update([data.columns.values.tolist()] + data.values.tolist())
                results[username] = {"status": "success", "message": f"Data distributed to {username}"}
            else:
                results[username] = {"status": "error", "message": f"User {username} not found"}
        return results

# Initialize UserManager
user_manager = UserManager()

app.layout = dbc.Container([
    # Header section
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1("Housemaid Monitoring Dashboard", 
                        className="display-4 mb-4 text-primary"),
                html.P("Upload your data file to begin analysis", 
                       className="lead text-muted")
            ], className="text-center my-4")
        ])
    ]),
    
    # File upload section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        html.I(className="fas fa-cloud-upload-alt fa-2x mb-2"),
                        html.Br(),
                        'Drag and Drop or ',
                        html.A('Select a File', className="text-primary")
                    ]),
                    style={
                        'width': '100%',
                        'height': '120px',
                        'lineHeight': '30px',
                        'borderWidth': '2px',
                        'borderStyle': 'dashed',
                        'borderRadius': '10px',
                        'textAlign': 'center',
                        'padding': '20px',
                        'backgroundColor': '#fafafa'
                    },
                    multiple=False
                )
            ], className="mb-4", style=custom_styles['filter-card'])
        ])
    ]),
    
    # Combined Manage Users and Current Users Accordion
    dbc.Accordion([
        dbc.AccordionItem(
            [
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Username", className="font-weight-bold mb-2"),
                            dbc.Input(id='input-username', placeholder="Enter username", type="text", className="mb-3")
                        ], md=4),
                        dbc.Col([
                            html.Label("Full Name", className="font-weight-bold mb-2"),
                            dbc.Input(id='input-fullname', placeholder="Enter full name", type="text", className="mb-3")
                        ], md=4),
                        dbc.Col([
                            html.Label("Google Sheet ID", className="font-weight-bold mb-2"),
                            dbc.Input(id='input-sheet-id', placeholder="Enter Google Sheet ID", type="text", className="mb-3")
                        ], md=4)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                html.Span([
                                    html.I(className="fas fa-plus me-2"),
                                    "Add User"
                                ]),
                                id='add-user',
                                color="success",
                                className="me-2"
                            ),
                            dbc.Button(
                                html.Span([
                                    html.I(className="fas fa-edit me-2"),
                                    "Update User"
                                ]),
                                id='update-user',
                                color="primary",
                                className="me-2"
                            ),
                            dbc.Button(
                                html.Span([
                                    html.I(className="fas fa-trash me-2"),
                                    "Delete User"
                                ]),
                                id='delete-user',
                                color="danger"
                            )
                        ], className="text-end mt-3")
                    ]),
                    html.Div(id='user-management-results', className="mt-3"),
                    dash_table.DataTable(
                        id='user-table',
                        columns=[
                            {'name': 'Username', 'id': 'username', 'type': 'text'},
                            {'name': 'Name', 'id': 'name', 'type': 'text'},
                            {'name': 'Google Sheet ID', 'id': 'google_sheet_id', 'type': 'text'},
                            {'name': 'Status', 'id': 'status', 'type': 'text'},
                            {'name': 'Workload', 'id': 'workload', 'type': 'numeric'}
                        ],
                        data=[
                            {
                                'username': username,
                                'name': user.name,
                                'google_sheet_id': user.google_sheet_id,
                                'status': 'Active' if user.active else 'Inactive',
                                'workload': user.workload
                            }
                            for username, user in user_manager.users.items()
                        ],
                        row_selectable='single',
                        selected_rows=[],
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '12px',
                        },
                        style_header={
                            'backgroundColor': '#f8f9fa',
                            'fontWeight': 'bold'
                        },
                        filter_action='native',
                        sort_action='native',
                        page_action='native',
                        page_size=10
                    )
                ])
            ],
            title="Manage Users ",
            item_id="manage-users"
        )
    ], start_collapsed=True, flush=True, style=custom_styles['filter-card']),
    
    # User Management Modal
    dbc.Modal(
        [
            dbc.ModalHeader("User Management"),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Username", className="font-weight-bold mb-2"),
                        dbc.Input(id='input-username-modal', placeholder="Enter username", type="text", className="mb-3")
                    ], md=4),
                    dbc.Col([
                        html.Label("Full Name", className="font-weight-bold mb-2"),
                        dbc.Input(id='input-fullname-modal', placeholder="Enter full name", type="text", className="mb-3")
                    ], md=4),
                    dbc.Col([
                        html.Label("Google Sheet ID", className="font-weight-bold mb-2"),
                        dbc.Input(id='input-sheet-id-modal', placeholder="Enter Google Sheet ID", type="text", className="mb-3")
                    ], md=4)
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            html.Span([
                                html.I(className="fas fa-plus me-2"),
                                "Add User"
                            ]),
                            id='add-user-modal',
                            color="success",
                            className="me-2"
                        ),
                        dbc.Button(
                            html.Span([
                                html.I(className="fas fa-edit me-2"),
                                "Update User"
                            ]),
                            id='update-user-modal',
                            color="primary",
                            className="me-2"
                        ),
                        dbc.Button(
                            html.Span([
                                html.I(className="fas fa-trash me-2"),
                                "Delete User"
                            ]),
                            id='delete-user-modal',
                            color="danger"
                        )
                    ], className="text-end mt-3")
                ]),
                html.Div(id='user-management-results-modal', className="mt-3")
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-user-modal", className="ms-auto")
            )
        ],
        id="user-management-modal",
        size="lg",
        is_open=False
    ),
    
    # User Management & Task Distribution Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H4("User Management & Task Distribution", className="text-primary mb-0"),
                    html.Small("Manage users and distribute tasks", className="text-muted")
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Select Users", className="font-weight-bold mb-2"),
                            dcc.Dropdown(
                                id='select-users',
                                multi=True,
                                placeholder="Select User(s)",
                                options=[{'label': user.name, 'value': username} for username, user in user_manager.users.items()],
                                className="mb-3"
                            )
                        ], md=6),
                        dbc.Col([
                            html.Label("Distribute Tasks", className="font-weight-bold mb-2"),
                            dbc.Button(
                                html.Span([
                                    html.I(className="fas fa-tasks me-2"),
                                    "Distribute Tasks"
                                ]),
                                id='distribute-tasks',
                                color="primary",
                                className="me-2"
                            )
                        ], md=6)
                    ]),
                    html.Div(id='distribution-results', className="mt-3")
                ])
            ], style=custom_styles['filter-card'])
        ])
    ]),
    
    # Filters Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Filters", className="text-primary mb-0")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Stage", className="font-weight-bold mb-2"),
                            dcc.Dropdown(
                                id='filter-stage',
                                multi=True,
                                placeholder="Select Stage(s)",
                                className="mb-3"
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("Type", className="font-weight-bold mb-2"),
                            dcc.Dropdown(
                                id='filter-type',
                                multi=True,
                                placeholder="Select Type(s)",
                                className="mb-3"
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("Nationality", className="font-weight-bold mb-2"),
                            dcc.Dropdown(
                                id='filter-nationality',
                                multi=True,
                                placeholder="Select Nationality(s)",
                                className="mb-3"
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("Client Priority", className="font-weight-bold mb-2"),
                            dcc.Dropdown(
                                id='filter-client-note',
                                multi=True,
                                placeholder="Select Priority",
                                className="mb-3"
                            )
                        ], md=3)
                    ])
                ])
            ], style=custom_styles['filter-card'])
        ])
    ]),
    
    # Stage Thresholds Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H4("Stage Thresholds (Hours)", className="text-primary mb-0"),
                    html.Small("Set maximum allowed hours for each stage", 
                             className="text-muted")
                ]),
                dbc.CardBody([
                    html.Div(id='threshold-inputs', style={
                        'max-height': '300px',
                        'overflow-y': 'auto',
                        'padding': '10px'
                    }),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                html.Span([
                                    html.I(className="fas fa-filter me-2"),
                                    "Apply Filters & Thresholds"
                                ]),
                                id='apply-filters',
                                color="primary",
                                className="me-2"
                            ),
                            dbc.Button(
                                html.Span([
                                    html.I(className="fas fa-undo me-2"),
                                    "Reset"
                                ]),
                                id='reset-filters',
                                color="secondary"
                            )
                        ], className="text-end mt-3")
                    ])
                ])
            ], style=custom_styles['filter-card'])
        ])
    ]),
    
    # Metrics Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-exclamation-triangle fa-2x mb-2 text-danger"),
                        html.H3(id='metric-super-angry', className="text-danger mb-1"),
                        html.P("Super Angry Clients", className="text-muted mb-0")
                    ], className="text-center")
                ])
            ], style=custom_styles['metric-card'])
        ], md=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-passport fa-2x mb-2 text-warning"),
                        html.H3(id='metric-prioritize-visa', className="text-warning mb-1"),
                        html.P("Priority Visa Cases", className="text-muted mb-0")
                    ], className="text-center")
                ])
            ], style=custom_styles['metric-card'])
        ], md=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-clock fa-2x mb-2 text-info"),
                        html.H3(id='metric-total-late', className="text-info mb-1"),
                        html.P("Total Late Cases", className="text-muted mb-0")
                    ], className="text-center")
                ])
            ], style=custom_styles['metric-card'])
        ], md=4)
    ], className="mb-4"),
    
    # Charts Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H4("Late Cases by Stage (Top 10)", className="text-primary mb-0"),
                    html.Small("Number of cases exceeding threshold per stage", 
                             className="text-muted")
                ]),
                dbc.CardBody([
                    dcc.Graph(id='bar-chart')
                ])
            ], style=custom_styles['chart-card'])
        ], md=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H4("Stage Distribution (Top 10)", className="text-primary mb-0"),
                    html.Small("Current distribution of all cases", 
                             className="text-muted")
                ]),
                dbc.CardBody([
                    dcc.Graph(id='pie-chart')
                ])
            ], style=custom_styles['chart-card'])
        ], md=12)
    ]),
    
    # Data Table Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Detailed Data", className="text-primary mb-0"),
                            html.Small("Full dataset with filtering and sorting", 
                                     className="text-muted")
                        ]),
                        dbc.Col([
                            dbc.Button(
                                html.Span([
                                    html.I(className="fas fa-file-csv me-2"),
                                    "Export CSV"
                                ]),
                                id="export-csv",
                                color="success",
                                size="sm",
                                className="me-2"
                            ),
                            dbc.Button(
                                html.Span([
                                    html.I(className="fas fa-file-excel me-2"),
                                    "Export Excel"
                                ]),
                                id="export-excel",
                                color="success",
                                size="sm"
                            )
                        ], className="text-end d-flex align-items-center")
                    ])
                ]),
                dbc.CardBody([
                    html.Div(id='data-table')
                ])
            ], style=custom_styles['chart-card'])
        ])
    ]),
    
    # Hidden download components
    html.Div([
        html.A(id='download-csv', download="filtered_data.csv", href="", target="_blank", style={'display': 'none'}),
        html.A(id='download-excel', download="filtered_data.xlsx", href="", target="_blank", style={'display': 'none'})
    ])
], fluid=True)
# Helper functions
def get_sorted_unique(series: pd.Series) -> List[str]:
    """Get sorted unique values from a series, handling mixed types and NaN values."""
    unique_values = [str(x) for x in series.unique() if pd.notna(x)]
    return sorted(unique_values)

def parse_contents(contents: str, filename: str) -> pd.DataFrame:
    """Parse uploaded file contents into a pandas DataFrame."""
    if contents is None:
        return pd.DataFrame()
    
    try:
        # Split the content
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Read the file based on its type
        if 'csv' in filename.lower():
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename.lower():
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            raise ValueError("Unsupported file type")
        
        # Clean up the DataFrame
        df = df.replace({pd.NA: None, pd.NaT: None})
        
        # Sort the DataFrame by 'Note time' and 'RPA try count' to ensure proper filling
        df = df.sort_values(by=['Note time', 'RPA try count'])
        
        # List of columns to forward-fill
        columns_to_fill = [
            'Housemaid Name', 'Housemaid ID', 'HM Status', 
            'Request ID MB', 'Nationality', 'Type'
        ]
        
        # Forward-fill the specified columns
        for column in columns_to_fill:
            if column in df.columns:
                df[column] = df[column].ffill()
        
        # Add Late column if not exists
        if 'Late' not in df.columns:
            df['Late'] = False
            
        return df
    except Exception as e:
        print(f"Error parsing file: {str(e)}")
        return pd.DataFrame()
# Callback to update filters and thresholds
@app.callback(
    [Output('filter-stage', 'options'),
     Output('filter-type', 'options'),
     Output('filter-nationality', 'options'),
     Output('filter-client-note', 'options'),
     Output('threshold-inputs', 'children')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_filters_and_thresholds(contents: str, filename: str):
    """Update filter options and threshold inputs based on uploaded data."""
    if contents is None:
        return [], [], [], [], []
    
    # Parse the uploaded file
    df = parse_contents(contents, filename)
    if df.empty:
        return [], [], [], [], []
    
    # Get unique values for filters
    stages = [{'label': stage, 'value': stage} for stage in get_sorted_unique(df['Current Stage'])]
    types = [{'label': type_, 'value': type_} for type_ in get_sorted_unique(df['Type'])]
    nationalities = [{'label': nat, 'value': nat} for nat in get_sorted_unique(df['Nationality'])]
    client_notes = [{'label': note, 'value': note} for note in get_sorted_unique(df['Client Note'])]
    
    # Create threshold inputs for each stage
    threshold_inputs = []
    for stage in get_sorted_unique(df['Current Stage']):
        threshold_inputs.append(
            dbc.Card([
                dbc.Row([
                    dbc.Col(html.Label(stage, className="font-weight-bold"), width=8),
                    dbc.Col(
                        dbc.Input(
                            id={'type': 'threshold-input', 'stage': stage},
                            type='number',
                            value=24,
                            min=0,
                            className="form-control-sm"
                        ),
                        width=4
                    )
                ], className="align-items-center")
            ], className="mb-2", style=custom_styles['threshold-card'])
        )
    
    return stages, types, nationalities, client_notes, threshold_inputs
# Callback to populate the user table
@app.callback(
    Output('user-table', 'data'),
    Input('user-management-modal', 'is_open')  # Trigger when the modal is opened
)
def populate_user_table(is_open):
    """Populate the user table with data from the UserManager."""
    if not is_open:
        return dash.no_update
    
    # Get user data from the UserManager
    user_data = [
        {
            'username': username,
            'name': user.name,
            'google_sheet_id': user.google_sheet_id,
            'status': 'Active' if user.active else 'Inactive',
            'workload': user.workload
        }
        for username, user in user_manager.users.items()
    ]
    
    return user_data

# Callback to handle user selection
@app.callback(
    [Output('input-username', 'value'),
     Output('input-fullname', 'value'),
     Output('input-sheet-id', 'value')],
    Input('user-table', 'selected_rows'),
    State('user-table', 'data')
)
def populate_form_with_selected_user(selected_rows, user_data):
    """Populate the form with data from the selected user."""
    if not selected_rows:
        return "", "", ""
    
    # Get the selected user's data
    selected_user = user_data[selected_rows[0]]
    return (
        selected_user['username'],
        selected_user['name'],
        selected_user['google_sheet_id']
    )
# Callback to add a new user
@app.callback(
    [Output('user-management-results', 'children', allow_duplicate=True),
     Output('user-table', 'data', allow_duplicate=True)],
    Input('add-user', 'n_clicks'),
    [State('input-username', 'value'),
     State('input-fullname', 'value'),
     State('input-sheet-id', 'value')],
    prevent_initial_call=True
)
def add_user(n_clicks, username, fullname, sheet_id):
    """Add a new user to the UserManager and refresh the table."""
    if not username or not fullname or not sheet_id:
        return dbc.Alert("Please fill in all fields.", color="warning"), dash.no_update
    
    if username in user_manager.users:
        return dbc.Alert(f"User '{username}' already exists.", color="danger"), dash.no_update
    
    try:
        user_manager.users[username] = User(name=fullname, google_sheet_id=sheet_id)
        # Refresh the table
        user_data = [
            {
                'username': username,
                'name': user.name,
                'google_sheet_id': user.google_sheet_id,
                'status': 'Active' if user.active else 'Inactive',
                'workload': user.workload
            }
            for username, user in user_manager.users.items()
        ]
        return dbc.Alert(f"User '{username}' added successfully.", color="success"), user_data
    except Exception as e:
        return dbc.Alert(f"Error adding user: {str(e)}", color="danger"), dash.no_update

# Callback to update an existing user
@app.callback(
    [Output('user-management-results', 'children', allow_duplicate=True),
     Output('user-table', 'data', allow_duplicate=True)],
    Input('update-user', 'n_clicks'),
    [State('input-username', 'value'),
     State('input-fullname', 'value'),
     State('input-sheet-id', 'value')],
    prevent_initial_call=True
)
def update_user(n_clicks, username, fullname, sheet_id):
    """Update an existing user in the UserManager and refresh the table."""
    if not username:
        return dbc.Alert("Please enter a username.", color="warning"), dash.no_update
    
    if username not in user_manager.users:
        return dbc.Alert(f"User '{username}' does not exist.", color="danger"), dash.no_update
    
    try:
        user = user_manager.users[username]
        if fullname:
            user.name = fullname
        if sheet_id:
            user.google_sheet_id = sheet_id
        # Refresh the table
        user_data = [
            {
                'username': username,
                'name': user.name,
                'google_sheet_id': user.google_sheet_id,
                'status': 'Active' if user.active else 'Inactive',
                'workload': user.workload
            }
            for username, user in user_manager.users.items()
        ]
        return dbc.Alert(f"User '{username}' updated successfully.", color="success"), user_data
    except Exception as e:
        return dbc.Alert(f"Error updating user: {str(e)}", color="danger"), dash.no_update

# Callback to delete a user
@app.callback(
    [Output('user-management-results', 'children', allow_duplicate=True),
     Output('user-table', 'data', allow_duplicate=True)],
    Input('delete-user', 'n_clicks'),
    State('input-username', 'value'),
    prevent_initial_call=True
)
def delete_user(n_clicks, username):
    """Delete a user from the UserManager and refresh the table."""
    if not username:
        return dbc.Alert("Please enter a username.", color="warning"), dash.no_update
    
    if username not in user_manager.users:
        return dbc.Alert(f"User '{username}' does not exist.", color="danger"), dash.no_update
    
    try:
        del user_manager.users[username]
        # Refresh the table
        user_data = [
            {
                'username': username,
                'name': user.name,
                'google_sheet_id': user.google_sheet_id,
                'status': 'Active' if user.active else 'Inactive',
                'workload': user.workload
            }
            for username, user in user_manager.users.items()
        ]
        return dbc.Alert(f"User '{username}' deleted successfully.", color="success"), user_data
    except Exception as e:
        return dbc.Alert(f"Error deleting user: {str(e)}", color="danger"), dash.no_update
# Callback for task distribution
@app.callback(
    Output('distribution-results', 'children'),
    Input('distribute-tasks', 'n_clicks'),
    State('select-users', 'value'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('filter-stage', 'value'),
    State('filter-type', 'value'),
    State('filter-nationality', 'value'),
    State('filter-client-note', 'value'),
    State({'type': 'threshold-input', 'stage': dash.ALL}, 'value'),
    State({'type': 'threshold-input', 'stage': dash.ALL}, 'id'),
    prevent_initial_call=True
)
def distribute_tasks(n_clicks, selected_users, contents, filename, stages, types, 
                     nationalities, client_notes, thresholds, threshold_ids):
    """Distribute filtered tasks to selected users' Google Sheets."""
    if not selected_users or not contents:
        return dbc.Alert("No users selected or no data uploaded.", color="warning")
    
    # Parse the uploaded file
    df = parse_contents(contents, filename)
    if df.empty:
        return dbc.Alert("Uploaded file is empty or invalid.", color="danger")
    
    # Apply filters to create the filtered DataFrame
    filtered_df = df.copy()
    
    if stages:
        filtered_df = filtered_df[filtered_df['Current Stage'].isin(stages)]
    if types:
        filtered_df = filtered_df[filtered_df['Type'].isin(types)]
    if nationalities:
        filtered_df = filtered_df[filtered_df['Nationality'].isin(nationalities)]
    if client_notes:
        filtered_df = filtered_df[filtered_df['Client Note'].isin(client_notes)]
    
    # Apply thresholds
    threshold_dict = {
        str(id_dict['stage']): threshold 
        for threshold, id_dict in zip(thresholds, threshold_ids)
    }
    
    # Calculate Late status
    filtered_df['Late'] = filtered_df.apply(
        lambda row: (pd.notna(row['Current Stage']) and 
                    pd.notna(row['Time In Stage']) and 
                    row['Time In Stage'] > threshold_dict.get(str(row['Current Stage']), 24)),
        axis=1
    )
    
    # Filter only late cases
    late_cases_df = filtered_df[filtered_df['Late'] == True]
    
    if late_cases_df.empty:
        return dbc.Alert("No late cases found to distribute.", color="warning")
    
    # Replace NaN values with None (JSON-compatible)
    late_cases_df = late_cases_df.where(pd.notna(late_cases_df), None)
    
    # Distribute the filtered data evenly among selected users
    try:
        num_users = len(selected_users)
        chunk_size = len(late_cases_df) // num_users
        remainder = len(late_cases_df) % num_users
        
        results = {}
        start_idx = 0
        for i, username in enumerate(selected_users):
            if username not in user_manager.users:
                results[username] = {"status": "error", "message": f"User {username} not found"}
                continue
            
            # Calculate end index for this user
            end_idx = start_idx + chunk_size + (1 if i < remainder else 0)
            user_data = late_cases_df.iloc[start_idx:end_idx]
            start_idx = end_idx
            
            # Update the user's Google Sheet
            try:
                sheet = user_manager.client.open_by_key(user_manager.users[username].google_sheet_id).sheet1
                sheet.clear()
                # Replace NaN values with empty strings for Google Sheets compatibility
                user_data = user_data.where(pd.notna(user_data), "")
                sheet.update([user_data.columns.values.tolist()] + user_data.values.tolist())
                results[username] = {"status": "success", "message": f"Assigned {len(user_data)} late cases to {username}"}
            except Exception as e:
                results[username] = {"status": "error", "message": f"Failed to update sheet for {username}: {str(e)}"}
        
        # Display results
        messages = []
        for username, result in results.items():
            if result['status'] == 'success':
                messages.append(dbc.Alert(result['message'], color="success"))
            else:
                messages.append(dbc.Alert(result['message'], color="danger"))
        return html.Div(messages)
    except Exception as e:
        traceback.print_exc()
        return dbc.Alert(f"An error occurred during task distribution: {str(e)}", color="danger")
    
# Callback for metrics and visualizations
@app.callback(
    [Output('metric-super-angry', 'children'),
     Output('metric-prioritize-visa', 'children'),
     Output('metric-total-late', 'children'),
     Output('bar-chart', 'figure'),
     Output('pie-chart', 'figure'),
     Output('data-table', 'children')],
    [Input('apply-filters', 'n_clicks'),
     Input('reset-filters', 'n_clicks')],
    [State('upload-data', 'contents'),
     State('upload-data', 'filename'),
     State('filter-stage', 'value'),
     State('filter-type', 'value'),
     State('filter-nationality', 'value'),
     State('filter-client-note', 'value'),
     State({'type': 'threshold-input', 'stage': dash.ALL}, 'value'),
     State({'type': 'threshold-input', 'stage': dash.ALL}, 'id')]
)
def update_dashboard(apply_clicks, reset_clicks, contents, filename, stages, types, 
                    nationalities, client_notes, thresholds, threshold_ids):
    """Update all dashboard components based on filters and thresholds."""
    if contents is None:
        return "0", "0", "0", {}, {}, []
    
    # Parse the uploaded file
    df = parse_contents(contents, filename)
    if df.empty:
        return "0", "0", "0", {}, {}, []
        
    filtered_df = df.copy()
    
    # Reset filters if reset button is clicked
    if reset_clicks and reset_clicks > (apply_clicks or 0):
        stages, types, nationalities, client_notes = None, None, None, None
    
    # Apply filters
    if stages:
        filtered_df = filtered_df[filtered_df['Current Stage'].isin(stages)]
    if types:
        filtered_df = filtered_df[filtered_df['Type'].isin(types)]
    if nationalities:
        filtered_df = filtered_df[filtered_df['Nationality'].isin(nationalities)]
    if client_notes:
        filtered_df = filtered_df[filtered_df['Client Note'].isin(client_notes)]
    
    # Create threshold dictionary
    threshold_dict = {
        str(id_dict['stage']): threshold 
        for threshold, id_dict in zip(thresholds, threshold_ids)
    }
    
    # Apply thresholds and calculate Late status
    filtered_df['Late'] = filtered_df.apply(
        lambda row: (pd.notna(row['Current Stage']) and 
                    pd.notna(row['Time In Stage']) and 
                    row['Time In Stage'] > threshold_dict.get(str(row['Current Stage']), 24)),
        axis=1
    )
    
    # Calculate metrics
    super_angry = filtered_df[filtered_df['Client Note'] == 'SUPER_ANGRY_CLIENT']['Housemaid Name'].drop_duplicates().shape[0]
    prioritize_visa = filtered_df[filtered_df['Client Note'] == 'PRIORITIZE_VISA']['Housemaid Name'].drop_duplicates().shape[0]
    total_late = filtered_df[filtered_df['Late'] == True]['Housemaid Name'].drop_duplicates().shape[0]
    
    # Create bar chart for late cases (Top 10)
    late_cases = filtered_df[filtered_df['Late'] == True]
    stage_counts = late_cases.groupby('Current Stage')['Housemaid Name'].nunique().reset_index(name='Count')
    stage_counts = stage_counts.sort_values(by='Count', ascending=False).head(10)  # Top 10

    
    bar_fig = go.Figure(data=[
        go.Bar(
            x=stage_counts['Count'],
            y=stage_counts['Current Stage'],
            orientation='h',
            text=stage_counts['Count'],
            textposition='auto',
            marker_color='rgb(55, 83, 109)',
            hovertemplate="Stage: %{y}<br>Late Cases: %{x}<extra></extra>"
        )
    ])
    
    bar_fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
        plot_bgcolor='white',
        height=400,
        xaxis_title="Number of Late Cases",
        yaxis_title="Stage",
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(211, 211, 211, 0.5)'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(211, 211, 211, 0.5)'
        )
    )
    
    # Create pie chart for stage distribution (Top 10)
    stage_dist = filtered_df.groupby('Current Stage')['Housemaid Name'].nunique().reset_index(name='Count')
    stage_dist = stage_dist.sort_values(by='Count', ascending=False).head(10)  # Top 10
    
    pie_fig = go.Figure(data=[
        go.Pie(
            labels=stage_dist['Current Stage'],
            values=stage_dist['Count'],
            textinfo='percent+label',
            hole=0.3,
            hovertemplate="Stage: %{label}<br>Cases: %{value}<br>Percentage: %{percent}<extra></extra>"
        )
    ])
    
    pie_fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
        height=400
    )
    
    # Filter the data to include only delayed cases for the table
    delayed_df = filtered_df[filtered_df['Late'] == True]
    
    # Create data table with enhanced formatting
    table = dash_table.DataTable(
        id='datatable',
        columns=[{"name": i, "id": i} for i in delayed_df.columns],
        data=delayed_df.to_dict('records'),
        page_size=10,
        style_table={
            'overflowX': 'auto'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontSize': '14px',
            'fontFamily': '"Segoe UI", Arial, sans-serif'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'border': '1px solid #dee2e6',
            'textAlign': 'center'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            },
            {
                'if': {'filter_query': '{Late} eq true'},
                'backgroundColor': '#fff3cd',
                'color': '#856404'
            },
            {
                'if': {'filter_query': '{Client Note} eq "SUPER_ANGRY_CLIENT"'},
                'backgroundColor': '#f8d7da',
                'color': '#721c24'
            },
            {
                'if': {'filter_query': '{Client Note} eq "PRIORITIZE_VISA"'},
                'backgroundColor': '#fff3cd',
                'color': '#856404'
            }
        ],
        filter_action='native',
        sort_action='native',
        sort_mode='multi',
        page_current=0,
        filter_options={'case': 'insensitive'},
        tooltip_data=[
            {
                column: {'value': str(value), 'type': 'markdown'}
                for column, value in row.items()
            } for row in delayed_df.to_dict('records')
        ],
        tooltip_header={
            column: {'value': column, 'type': 'markdown'}
            for column in delayed_df.columns
        }
    )
    
    return str(super_angry), str(prioritize_visa), str(total_late), bar_fig, pie_fig, table

@app.callback(
    Output('select-users', 'options'),
    Input('user-table', 'data')
)
def update_user_dropdown(user_data):
    """Update the dropdown options in the User Management & Task Distribution section."""
    return [{'label': user['name'], 'value': user['username']} for user in user_data]

# Callback for export functionality
@app.callback(
    [Output('download-csv', 'href'),
     Output('download-excel', 'href')],
    [Input('export-csv', 'n_clicks'),
     Input('export-excel', 'n_clicks')],
    [State('upload-data', 'contents'),
     State('upload-data', 'filename'),
     State('filter-stage', 'value'),
     State('filter-type', 'value'),
     State('filter-nationality', 'value'),
     State('filter-client-note', 'value'),
     State({'type': 'threshold-input', 'stage': dash.ALL}, 'value'),
     State({'type': 'threshold-input', 'stage': dash.ALL}, 'id')]
)
def export_data(csv_clicks, excel_clicks, contents, filename, stages, types, 
                nationalities, client_notes, thresholds, threshold_ids):
    """Generate export links for filtered data in CSV and Excel formats."""
    if contents is None:
        return "", ""
        
    # Parse the uploaded file and apply filters
    df = parse_contents(contents, filename)
    if df.empty:
        return "", ""
        
    filtered_df = df.copy()
    
    # Apply filters
    if stages:
        filtered_df = filtered_df[filtered_df['Current Stage'].isin(stages)]
    if types:
        filtered_df = filtered_df[filtered_df['Type'].isin(types)]
    if nationalities:
        filtered_df = filtered_df[filtered_df['Nationality'].isin(nationalities)]
    if client_notes:
        filtered_df = filtered_df[filtered_df['Client Note'].isin(client_notes)]
    
    # Apply thresholds
    threshold_dict = {
        str(id_dict['stage']): threshold 
        for threshold, id_dict in zip(thresholds, threshold_ids)
    }
    
    filtered_df['Late'] = filtered_df.apply(
        lambda row: (pd.notna(row['Current Stage']) and 
                    pd.notna(row['Time In Stage']) and 
                    row['Time In Stage'] > threshold_dict.get(str(row['Current Stage']), 24)),
        axis=1
    )
    
    # Generate filename based on filters
    filter_names = []
    if stages:
        filter_names.append(f"Stage_{'_'.join(stages)}")
    if types:
        filter_names.append(f"Type_{'_'.join(types)}")
    if nationalities:
        filter_names.append(f"Nationality_{'_'.join(nationalities)}")
    if client_notes:
        filter_names.append(f"ClientNote_{'_'.join(client_notes)}")
    
    base_filename = "filtered_data"
    if filter_names:
        base_filename += "_" + "_".join(filter_names)
    
    try:
        # Create CSV download link
        csv_string = filtered_df.to_csv(index=False, encoding='utf-8')
        csv_base64 = base64.b64encode(csv_string.encode()).decode()
        csv_href = f'data:text/csv;base64,{csv_base64}'
        
        # Create Excel download link
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, index=False)
        excel_base64 = base64.b64encode(excel_buffer.getvalue()).decode()
        excel_href = f'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{excel_base64}'
        
        # Update download filenames
        app.clientside_callback(
            """
            function(csv_href, excel_href, base_filename) {
                document.getElementById('download-csv').download = base_filename + '.csv';
                document.getElementById('download-excel').download = base_filename + '.xlsx';
                return [csv_href, excel_href];
            }
            """,
            [Output('download-csv', 'href'),
             Output('download-excel', 'href')],
            [Input('download-csv', 'href'),
             Input('download-excel', 'href')],
            [State('base-filename', 'data')]
        )
        
        return csv_href, excel_href, base_filename
    except Exception as e:
        print(f"Export error: {str(e)}")
        return "", "", ""


def run_server(debug=True, port=8050, host='0.0.0.0'):
    print("""
    ╔════════════════════════════════════════════╗
    ║     Housemaid Monitoring Dashboard         ║
    ╠════════════════════════════════════════════╣
    ║ Starting server at http://localhost:8050   ║
    ║ Press Ctrl+C to quit                       ║
    ╚════════════════════════════════════════════╝
    """)
    app.run_server(debug=debug, port=port, host=host)
# Run the app
if __name__ == '__main__':
    run_server(debug=True, port=8050, host="0.0.0.0")
else:
    server = app.server  # Ensure the server is exposed when deployed
