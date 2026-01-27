# Bookmark Manager

A web-based bookmark management system built with Flask. Organize, search, and manage your bookmarks with support for folders, tags, and powerful search capabilities.

## Features

- **Bookmark Management**: Add, edit, delete, and organize bookmarks
- **Folder Organization**: Create nested folders to organize bookmarks hierarchically
- **Tagging System**: Tag bookmarks for easy categorization and filtering
- **Powerful Search**: Search bookmarks by title, URL, description, or tags
- **Import/Export**:
  - Import bookmarks from browser export files (HTML format)
  - Export bookmarks to JSON or HTML format
- **Automatic Metadata**: Fetch page titles and descriptions automatically
- **Responsive Design**: Works on desktop and mobile devices
- **RESTful API**: Programmatic access to all features

## Requirements

- Python 3.8+
- SQLite 3
- Modern web browser

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd bookmark-manager
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize the database

```bash
python init_db.py
```

### 5. Run the application

**Development mode:**
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### Web Interface

1. **Adding Bookmarks**:
   - Click "Add Bookmark" button
   - Enter URL (title and description will be fetched automatically)
   - Select a folder (optional)
   - Add tags (optional)
   - Click "Save"

2. **Managing Folders**:
   - Click "Manage Folders" to create new folders
   - Create nested folders by selecting a parent folder
   - Drag bookmarks between folders

3. **Searching**:
   - Use the search bar to find bookmarks
   - Search works across titles, URLs, descriptions, and tags
   - Filter by folder or tags

4. **Importing Bookmarks**:
   - Click "Import" and select your browser's exported HTML file
   - Bookmarks will be imported with their folder structure

5. **Exporting Bookmarks**:
   - Click "Export" and choose JSON or HTML format
   - Save the file to your computer

### API Endpoints

All API endpoints are documented and can be tested using tools like curl or Postman.

**Bookmarks:**
- `GET /api/bookmarks` - List all bookmarks
- `POST /api/bookmarks` - Create a bookmark
- `GET /api/bookmarks/<id>` - Get a specific bookmark
- `PUT /api/bookmarks/<id>` - Update a bookmark
- `DELETE /api/bookmarks/<id>` - Delete a bookmark

**Folders:**
- `GET /api/folders` - List all folders
- `POST /api/folders` - Create a folder
- `PUT /api/folders/<id>` - Update a folder
- `DELETE /api/folders/<id>` - Delete a folder

**Tags:**
- `GET /api/tags` - List all tags
- `GET /api/tags/<name>/bookmarks` - Get bookmarks with a specific tag

**Import/Export:**
- `POST /api/import` - Import bookmarks
- `GET /api/export?format=json` - Export bookmarks as JSON
- `GET /api/export?format=html` - Export bookmarks as HTML

## Deployment

### Using Gunicorn and Nginx

1. **Install Gunicorn**:
```bash
pip install gunicorn
```

2. **Configure Gunicorn**:
   - Edit `gunicorn_config.py` as needed
   - The default configuration uses automatic worker calculation

3. **Set up Systemd service**:
```bash
sudo cp systemd.service.example /etc/systemd/system/bookmark-manager.service
sudo nano /etc/systemd/system/bookmark-manager.service
# Edit paths and user as needed
sudo systemctl daemon-reload
sudo systemctl enable bookmark-manager
sudo systemctl start bookmark-manager
```

4. **Configure Nginx**:
```bash
sudo cp nginx.conf.example /etc/nginx/sites-available/bookmark-manager
sudo nano /etc/nginx/sites-available/bookmark-manager
# Edit domain and paths as needed
sudo ln -s /etc/nginx/sites-available/bookmark-manager /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

5. **Set up SSL** (recommended):
```bash
sudo certbot --nginx -d your-domain.com
```

## Development

### Running Tests

```bash
pytest
```

### Code Structure

- `app.py` - Main application file
- `models.py` - Database models
- `utils.py` - Utility functions (URL fetching, import/export)
- `templates/` - HTML templates
- `static/` - CSS, JavaScript, and other static files
- `tests/` - Test files

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
