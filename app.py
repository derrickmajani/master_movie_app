import pyodbc
import pandas as pd
import streamlit as st
from datetime import datetime

# Database secrets
server = st.secrets["database"]["server"]
database = st.secrets["database"]["database"]
username = st.secrets["database"]["username"]
password = st.secrets["database"]["password"]

# Function to get database connection
def get_connection():
    try:
        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};DATABASE={database};'
            f'UID={username};PWD={password};'
            'Encrypt=yes;TrustServerCertificate=yes'
        )
        conn = pyodbc.connect(conn_str, timeout=10)
        return conn
    except pyodbc.Error as e:
        st.error(f"❌ Database connection failed: {e.args[1]}")
        return None

# SQL query to get master movies
sql_query = "SELECT * FROM [DataScienceDataImport].[MasterMovie]"

# Page config
st.set_page_config(
    page_title="Master Movie Database Manager",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS styling
st.markdown("""
    <style>
        /* main styling */
        .main-header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 2rem;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        /* ... rest of your CSS styles ... */
    </style>
""", unsafe_allow_html=True)

# Try to connect to DB
conn = get_connection()
if conn:
    try:
        df = pd.read_sql(sql_query, conn)
        conn.close()
        st.success("✅ Database connection established successfully!")
    except Exception as e:
        st.error(f"❌ Failed to fetch data: {e}")
        df = pd.DataFrame()
else:
    df = pd.DataFrame()

# -----------------------------
# Main Header
# -----------------------------
st.markdown('''
<div class="main-header">
    <h1>🎬 Master Movie Database Manager</h1>
    <p>Professional Movie Records Management System</p>
</div>
''', unsafe_allow_html=True)

# -----------------------------
# Metrics
# -----------------------------
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><h2 style="color:#007bff;">{len(df):,}</h2><p>Total Movies</p></div>', unsafe_allow_html=True)
with col2:
    unique_languages = df['Language'].nunique() if 'Language' in df.columns else 0
    st.markdown(f'<div class="metric-card"><h2 style="color:#28a745;">{unique_languages}</h2><p>Languages</p></div>', unsafe_allow_html=True)
with col3:
    recent_movies = len(df[pd.to_datetime(df['ReleaseDate'], errors="coerce") >= '2020-01-01']) if 'ReleaseDate' in df.columns else 0
    st.markdown(f'<div class="metric-card"><h2 style="color:#ffc107;">{recent_movies:,}</h2><p>Recent Movies (2020+)</p></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><h2 style="color:#17a2b8;">Live</h2><p>Database Status</p></div>', unsafe_allow_html=True)

st.markdown('<hr class="section-separator">', unsafe_allow_html=True)

# -----------------------------
# Search Section
# -----------------------------
st.markdown('<div class="search-container">', unsafe_allow_html=True)
st.markdown("### 🔍 Search Movie Database")
search_query = st.text_input("🎬 Enter movie title:", placeholder="Spider-Man, Batman, Avatar...")
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Search Results
# -----------------------------
if search_query and not df.empty:
    results = df[df["Title"].str.contains(search_query, case=False, na=False)]
    if not results.empty:
        st.markdown('<div class="results-container">', unsafe_allow_html=True)
        st.markdown(f"Found {len(results)} movies matching '{search_query}'")
        
        if 'selected_movie' not in st.session_state:
            st.session_state.selected_movie = None
        
        for idx, (_, row) in enumerate(results.iterrows()):
            if st.button(f"🎬 {row['Title']}", key=f"select_{idx}"):
                st.session_state.selected_movie = row['Title']
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning(f"No movies found matching '{search_query}'")

# -----------------------------
# Edit Section
# -----------------------------
if 'selected_movie' in st.session_state and st.session_state.selected_movie and not df.empty:
    selected_title = st.session_state.selected_movie
    st.markdown('<hr class="section-separator">', unsafe_allow_html=True)
    st.markdown(f'<div class="edit-section"><h3>✏️ Editing Movie Record: {selected_title}</h3></div>', unsafe_allow_html=True)
    
    row_to_edit = df[df["Title"] == selected_title]
    if not row_to_edit.empty:
        current_row = row_to_edit.iloc[0]
        with st.form("edit_movie_form"):
            col1, col2 = st.columns(2)
            with col1:
                movie_key = st.text_input("Movie Key", value=str(current_row.get('MovieKey', '')))
                movie_id = st.text_input("Movie Identifier", value=str(current_row.get('MovieIdentifier', '')))
                master_movie_id = st.text_input("Master Movie ID", value=str(current_row.get('MasterMovieID', '')))
            with col2:
                master_title = st.text_input("Master Title", value=str(current_row.get('MasterTitle', '')))
                language = st.text_input("Language", value=str(current_row.get('Language', '')))
                release_date = st.date_input("Release Date", value=pd.to_datetime(current_row.get('ReleaseDate', datetime.today())).date())
            st.markdown("---")
            submit_button = st.form_submit_button("💾 Save Changes")
            cancel_button = st.form_submit_button("❌ Cancel")
        
        if cancel_button:
            st.session_state.selected_movie = None
            st.success("✅ Edit cancelled")
            st.rerun()
        
        if submit_button:
            try:
                with pymssql.connect(server=server, user=username, password=password, database=database) as conn_update:
                    cursor = conn_update.cursor()
                    update_query = """
                        UPDATE [DataScienceDataImport].[MasterMovie]
                        SET MovieKey=%s, MovieIdentifier=%s, ReleaseDate=%s, MasterMovieID=%s, MasterTitle=%s, Language=%s
                        WHERE Title=%s
                    """
                    cursor.execute(update_query, (
                        movie_key, movie_id, release_date, master_movie_id, master_title, language, selected_title
                    ))
                    conn_update.commit()
                st.success(f"✅ Movie '{selected_title}' updated successfully!")
                st.session_state.selected_movie = None
                st.rerun()
            except Exception as e:
                st.error(f"❌ Database Update Error: {e}")

# -----------------------------
# Demo Mode
# -----------------------------
if df.empty:
    st.warning("🔧 Demo Mode Active - Database not available")
    sample_data = {
        'Title': ['Spider-Man: No Way Home', 'The Batman', 'Top Gun: Maverick'],
        'MasterTitle': ['Spider-Man: No Way Home', 'The Batman', 'Top Gun: Maverick'],
        'Language': ['English', 'English', 'English'],
        'ReleaseDate': ['2021-12-17', '2022-03-04', '2022-05-27'],
        'MovieKey': ['SM001', 'BM001', 'TG001'],
        'MovieIdentifier': ['spiderman-nwh', 'batman-2022', 'topgun-maverick'],
        'MasterMovieID': ['1001', '1002', '1003']
    }
    df = pd.DataFrame(sample_data)
    st.dataframe(df, use_container_width=True)

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("## 🔧 System Information")
    if conn:
        st.success("🟢 Live Database")
    else:
        st.warning("🟡 Demo Mode")
    st.markdown(f"Server: {server}")
    st.markdown(f"Database: {database}")
    st.markdown(f"User: {username}")
    st.markdown(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")