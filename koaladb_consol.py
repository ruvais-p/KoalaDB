import argparse
import http.server
import socketserver
import webbrowser
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from koaladb import KoalaDB

def generate_collection_selector():
    """Generate HTML for collection selection"""
    db_path = Path(KoalaDB.db_path)
    collections = []
    
    if db_path.exists():
        for item in db_path.iterdir():
            if item.is_dir() and (item / "data.bson").exists():
                collections.append(item.name)
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KoalaDB Collections</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 40px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                text-align: center;
            }
            h1 {
                color: #333;
                margin-bottom: 30px;
            }
            .collection-list {
                list-style: none;
                padding: 0;
            }
            .collection-item {
                margin: 15px 0;
            }
            .collection-link {
                display: block;
                padding: 15px 20px;
                background-color: #2196F3;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-size: 18px;
                transition: background-color 0.3s;
            }
            .collection-link:hover {
                background-color: #0b7dda;
            }
            .no-collections {
                color: #888;
                font-style: italic;
                margin: 40px 0;
            }
            .stats {
                margin-top: 30px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>KoalaDB Collections</h1>
    """
    
    if collections:
        html_content += """
            <ul class="collection-list">
        """
        for collection in sorted(collections):
            html_content += f"""
                <li class="collection-item">
                    <a href="/collection/{collection}" class="collection-link">{collection}</a>
                </li>
            """
        html_content += """
            </ul>
        """
    else:
        html_content += """
            <div class="no-collections">
                <h3>No collections found</h3>
                <p>Create some collections using the Python API first.</p>
            </div>
        """
    
    html_content += f"""
            <div class="stats">
                <strong>Total Collections:</strong> {len(collections)}<br>
                <strong>Database Path:</strong> {db_path.absolute()}
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def generate_html_view(collection):
    """Generate an HTML view of the collection data"""
    data = collection.data
    
    # Convert timestamps to readable format
    formatted_data = {}
    for doc_id, doc_data in data.items():
        formatted_doc = doc_data.copy()
        
        # Format timestamps if they exist
        if '_created_at' in formatted_doc:
            formatted_doc['_created_at_formatted'] = collection.format_timestamp(formatted_doc['_created_at'])
        if '_updated_at' in formatted_doc:
            formatted_doc['_updated_at_formatted'] = collection.format_timestamp(formatted_doc['_updated_at'])
            
        formatted_data[doc_id] = formatted_doc
    
    # Get all collections for navigation
    db_path = Path(KoalaDB.db_path)
    collections = []
    if db_path.exists():
        for item in db_path.iterdir():
            if item.is_dir() and (item / "data.bson").exists():
                collections.append(item.name)
    
    # Create HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KoalaDB Viewer - {collection.name}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 2px solid #eee;
            }}
            h1 {{
                color: #333;
                margin: 0;
            }}
            .collection-nav {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }}
            .nav-button {{
                padding: 8px 15px;
                background-color: #2196F3;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                border: none;
                cursor: pointer;
            }}
            .nav-button:hover {{
                background-color: #0b7dda;
            }}
            .current-collection {{
                background-color: #4CAF50;
            }}
            .stats {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .document {{
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-bottom: 15px;
                padding: 15px;
                background-color: #fff;
            }}
            .document-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }}
            .document-id {{
                font-weight: bold;
                color: #666;
                font-family: monospace;
                font-size: 0.9em;
            }}
            .document-timestamps {{
                font-size: 0.9em;
                color: #888;
            }}
            .document-content {{
                margin-top: 10px;
            }}
            .field {{
                margin-bottom: 8px;
                padding: 8px;
                background-color: #f9f9f9;
                border-radius: 4px;
                display: flex;
            }}
            .field-name {{
                font-weight: bold;
                color: #555;
                min-width: 150px;
            }}
            .field-value {{
                font-family: monospace;
                flex: 1;
            }}
            .timestamp-field {{
                color: #777;
                font-size: 0.9em;
                background-color: #f0f0f0;
            }}
            .data-field {{
                background-color: #e8f4f8;
            }}
            .controls {{
                margin-bottom: 20px;
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }}
            button {{
                padding: 8px 15px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }}
            button:hover {{
                background-color: #45a049;
            }}
            .search-box {{
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                width: 250px;
            }}
            .no-data {{
                text-align: center;
                padding: 30px;
                color: #888;
                font-style: italic;
            }}
            .section-title {{
                font-weight: bold;
                margin-top: 15px;
                margin-bottom: 10px;
                color: #444;
                border-bottom: 1px solid #eee;
                padding-bottom: 5px;
            }}
            .edit-btn {{
                background-color: #2196F3;
                margin-left: 5px;
            }}
            .edit-btn:hover {{
                background-color: #0b7dda;
            }}
            .save-btn {{
                background-color: #4CAF50;
                margin-left: 5px;
            }}
            .save-btn:hover {{
                background-color: #45a049;
            }}
            .cancel-btn {{
                background-color: #f44336;
                margin-left: 5px;
            }}
            .cancel-btn:hover {{
                background-color: #d32f2f;
            }}
            .edit-field {{
                width: 100%;
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
                font-family: monospace;
            }}
            .add-field {{
                margin-top: 10px;
                padding: 10px;
                background-color: #e7f3fe;
                border-radius: 4px;
            }}
            .add-field input {{
                margin: 0 5px;
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
            }}
            .notification {{
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px;
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                display: none;
                z-index: 1000;
            }}
            .media-file {{
                background-color: #fff3cd;
            }}
            .media-file .field-value {{
                color: #856404;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="notification" id="notification">Document updated successfully!</div>
        <div class="container">
            <div class="header">
                <h1>KoalaDB Viewer - Collection: {collection.name}</h1>
                <div class="collection-nav">
                    <a href="/" class="nav-button">All Collections</a>
                    {"".join([f'<a href="/collection/{col}" class="nav-button{" current-collection" if col == collection.name else ""}">{col}</a>' for col in sorted(collections)])}
                </div>
            </div>
            
            <div class="stats">
                <strong>Total Documents:</strong> {len(data)}<br>
                <strong>Oldest Document:</strong> 
    """
    
    # Add oldest document info
    oldest = collection.get_oldest_document()
    if oldest:
        oldest_id = list(oldest.keys())[0]
        oldest_data = oldest[oldest_id]
        if '_created_at' in oldest_data:
            html_content += f"{collection.format_timestamp(oldest_data['_created_at'])}"
        else:
            html_content += "N/A"
    else:
        html_content += "N/A"
    
    html_content += "<br><strong>Newest Document:</strong> "
    
    # Add newest document info
    newest = collection.get_newest_document()
    if newest:
        newest_id = list(newest.keys())[0]
        newest_data = newest[newest_id]
        if '_created_at' in newest_data:
            html_content += f"{collection.format_timestamp(newest_data['_created_at'])}"
        else:
            html_content += "N/A"
    else:
        html_content += "N/A"
    
    html_content += """
            </div>
    """
    
    if not data:
        html_content += """
            <div class="no-data">
                <h3>No documents found in this collection</h3>
                <p>Create some documents using the Python API first.</p>
            </div>
        """
    else:
        html_content += """
            <div class="controls">
                <input type="text" id="searchInput" class="search-box" placeholder="Search documents..." onkeyup="searchDocuments()">
                <button onclick="sortBy('_created_at')">Sort by Creation Time</button>
                <button onclick="sortBy('_updated_at')">Sort by Update Time</button>
                <button onclick="resetView()">Reset View</button>
            </div>
            
            <div id="documents">
        """
        
        # Add documents
        for doc_id, doc_data in formatted_data.items():
            html_content += f"""
                <div class="document" id="doc-{doc_id}">
                    <div class="document-header">
                        <div class="document-id">ID: {doc_id}</div>
                        <div class="document-timestamps">
            """
            
            if '_created_at_formatted' in doc_data:
                html_content += f"Created: {doc_data['_created_at_formatted']}"
                
            if '_updated_at_formatted' in doc_data and '_created_at_formatted' in doc_data:
                html_content += " | "
                
            if '_updated_at_formatted' in doc_data:
                html_content += f"Updated: {doc_data['_updated_at_formatted']}"
                
            html_content += f"""
                        </div>
                        <div>
                            <button class="edit-btn" onclick="toggleEdit('{doc_id}')">Edit</button>
                        </div>
                    </div>
                    <div class="document-content" id="content-{doc_id}">
            """
            
            # Add metadata section (internal fields)
            metadata_fields = [key for key in doc_data.keys() if key.startswith('_') and not key.endswith('_formatted')]
            if metadata_fields:
                html_content += """
                        <div class="section-title">Metadata:</div>
                """
                for key in metadata_fields:
                    if key in ['_created_at', '_updated_at']:
                        # Use formatted version for timestamps
                        formatted_key = f"{key}_formatted"
                        if formatted_key in doc_data:
                            html_content += f"""
                                <div class="field timestamp-field">
                                    <span class="field-name">{key}:</span> 
                                    <span class="field-value">{doc_data[formatted_key]}</span>
                                </div>
                            """
                    else:
                        html_content += f"""
                            <div class="field timestamp-field">
                                <span class="field-name">{key}:</span> 
                                <span class="field-value">{json.dumps(doc_data[key])}</span>
                            </div>
                        """
            
            # Add data section (custom fields)
            data_fields = [key for key in doc_data.keys() if not key.startswith('_')]
            if data_fields:
                html_content += """
                        <div class="section-title">Data:</div>
                """
                for key in data_fields:
                    field_class = "media-file" if isinstance(doc_data[key], str) and doc_data[key].startswith('store/') else "data-field"
                    html_content += f"""
                        <div class="field {field_class}">
                            <span class="field-name">{key}:</span> 
                            <span class="field-value" id="value-{doc_id}-{key}">{json.dumps(doc_data[key])}</span>
                            <button class="edit-btn" onclick="editField('{doc_id}', '{key}')">Edit</button>
                        </div>
                    """
            
            # Add new field section
            html_content += f"""
                        <div class="add-field">
                            <strong>Add New Field:</strong>
                            <input type="text" id="new-field-name-{doc_id}" placeholder="Field name">
                            <input type="text" id="new-field-value-{doc_id}" placeholder="Field value">
                            <button class="edit-btn" onclick="addField('{doc_id}')">Add Field</button>
                        </div>
            """
            
            html_content += """
                    </div>
                </div>
            """
        
        html_content += """
            </div>
            
            <script>
                let originalOrder = [];
                
                // Store original order on page load
                window.onload = function() {
                    const documents = document.getElementById('documents');
                    originalOrder = Array.from(documents.children);
                };
                
                function searchDocuments() {
                    const input = document.getElementById('searchInput');
                    const filter = input.value.toLowerCase();
                    const documents = document.getElementById('documents');
                    const items = documents.getElementsByClassName('document');
                    
                    for (let i = 0; i < items.length; i++) {
                        const docContent = items[i].textContent || items[i].innerText;
                        if (docContent.toLowerCase().includes(filter)) {
                            items[i].style.display = "";
                        } else {
                            items[i].style.display = "none";
                        }
                    }
                }
                
                function sortBy(field) {
                    const documents = document.getElementById('documents');
                    const items = Array.from(documents.getElementsByClassName('document'));
                    
                    items.sort((a, b) => {
                        const aId = a.id.replace('doc-', '');
                        const bId = b.id.replace('doc-', '');
                        
                        // Get the timestamp values from the data
                        const aData = """ + json.dumps(data) + """[aId] || {};
                        const bData = """ + json.dumps(data) + """[bId] || {};
                        
                        const aValue = aData[field] || 0;
                        const bValue = bData[field] || 0;
                        
                        return bValue - aValue; // Newest first
                    });
                    
                    // Clear and re-add sorted items
                    documents.innerHTML = '';
                    items.forEach(item => documents.appendChild(item));
                }
                
                function resetView() {
                    const documents = document.getElementById('documents');
                    documents.innerHTML = '';
                    originalOrder.forEach(item => documents.appendChild(item));
                    document.getElementById('searchInput').value = '';
                    
                    // Show all documents
                    const items = documents.getElementsByClassName('document');
                    for (let i = 0; i < items.length; i++) {
                        items[i].style.display = "";
                    }
                }
                
                function editField(docId, fieldName) {
                    const valueElement = document.getElementById(`value-${docId}-${fieldName}`);
                    const currentValue = valueElement.textContent;
                    
                    // Create input field
                    const inputField = document.createElement('input');
                    inputField.type = 'text';
                    inputField.value = currentValue;
                    inputField.className = 'edit-field';
                    inputField.id = `edit-${docId}-${fieldName}`;
                    
                    // Replace text with input field
                    valueElement.textContent = '';
                    valueElement.appendChild(inputField);
                    
                    // Add save and cancel buttons
                    const saveBtn = document.createElement('button');
                    saveBtn.textContent = 'Save';
                    saveBtn.className = 'save-btn';
                    saveBtn.onclick = () => saveField(docId, fieldName);
                    
                    const cancelBtn = document.createElement('button');
                    cancelBtn.textContent = 'Cancel';
                    cancelBtn.className = 'cancel-btn';
                    cancelBtn.onclick = () => cancelEdit(docId, fieldName, currentValue);
                    
                    valueElement.appendChild(saveBtn);
                    valueElement.appendChild(cancelBtn);
                }
                
                function saveField(docId, fieldName) {
                    const inputField = document.getElementById(`edit-${docId}-${fieldName}`);
                    const newValue = inputField.value;
                    
                    // Send update to server
                    fetch(window.location.pathname, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: `action=update&docId=${docId}&field=${fieldName}&value=${encodeURIComponent(newValue)}`
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Update the display
                            const valueElement = document.getElementById(`value-${docId}-${fieldName}`);
                            valueElement.textContent = JSON.stringify(newValue);
                            
                            // Show notification
                            showNotification('Field updated successfully!');
                        } else {
                            alert('Error updating field: ' + data.message);
                        }
                    })
                    .catch(error => {
                        alert('Error updating field: : ' + error);
                    });
                }
                
                function addField(docId) {
                    const fieldNameInput = document.getElementById(`new-field-name-${docId}`);
                    const fieldValueInput = document.getElementById(`new-field-value-${docId}`);
                    
                    const fieldName = fieldNameInput.value.trim();
                    const fieldValue = fieldValueInput.value.trim();
                    
                    if (!fieldName) {
                        alert('Please enter a field name');
                        return;
                    }
                    
                    // Send update to server
                    fetch(window.location.pathname, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: `action=add&docId=${docId}&field=${fieldName}&value=${encodeURIComponent(fieldValue)}`
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Add the new field to the display
                            const contentElement = document.getElementById(`content-${docId}`);
                            const dataSection = contentElement.querySelector('.section-title:last-of-type');
                            
                            if (dataSection && dataSection.textContent === 'Data:') {
                                const newField = document.createElement('div');
                                newField.className = 'field data-field';
                                newField.innerHTML = `
                                    <span class="field-name">${fieldName}:</span> 
                                    <span class="field-value" id="value-${docId}-${fieldName}">${JSON.stringify(fieldValue)}</span>
                                    <button class="edit-btn" onclick="editField('${docId}', '${fieldName}')">Edit</button>
                                `;
                                dataSection.parentNode.insertBefore(newField, dataSection.nextSibling);
                            }
                            
                            // Clear input fields
                            fieldNameInput.value = '';
                            fieldValueInput.value = '';
                            
                            // Show notification
                            showNotification('Field added successfully!');
                        } else {
                            alert('Error adding field: ' + data.message);
                        }
                    })
                    .catch(error => {
                        alert('Error adding field: ' + error);
                    });
                }
                
                function cancelEdit(docId, fieldName, originalValue) {
                    const valueElement = document.getElementById(`value-${docId}-${fieldName}`);
                    valueElement.textContent = originalValue;
                }
                
                function toggleEdit(docId) {
                    const contentElement = document.getElementById(`content-${docId}`);
                    const editButtons = contentElement.querySelectorAll('.edit-btn');
                    
                    editButtons.forEach(btn => {
                        if (btn.style.display === 'none') {
                            btn.style.display = 'inline-block';
                        } else {
                            btn.style.display = 'none';
                        }
                    });
                }
                
                function showNotification(message) {
                    const notification = document.getElementById('notification');
                    notification.textContent = message;
                    notification.style.display = 'block';
                    
                    setTimeout(() => {
                        notification.style.display = 'none';
                    }, 3000);
                }
            </script>
        """
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    return html_content

# Add this class to handle HTTP requests
class DBRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')
        
        if parsed_path.path == '/' or parsed_path.path == '':
            # Show collection selector
            html_content = generate_collection_selector()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html_content.encode())
            
        elif len(path_parts) >= 2 and path_parts[0] == 'collection':
            # Show specific collection
            collection_name = path_parts[1]
            try:
                collection = KoalaDB.collection(collection_name)
                html_content = generate_html_view(collection)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html_content.encode())
            except FileNotFoundError:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f"<h1>Collection '{collection_name}' not found</h1>".encode())
        else:
            super().do_GET()
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')
        
        if len(path_parts) >= 2 and path_parts[0] == 'collection':
            collection_name = path_parts[1]
            try:
                collection = KoalaDB.collection(collection_name)
                
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = parse_qs(post_data)
                
                action = data.get('action', [''])[0]
                doc_id = data.get('docId', [''])[0]
                field = data.get('field', [''])[0]
                value = data.get('value', [''])[0]
                
                response = {'success': False}
                
                try:
                    if action == 'update':
                        # Try to parse as JSON first, otherwise use as string
                        try:
                            parsed_value = json.loads(value)
                        except json.JSONDecodeError:
                            parsed_value = value
                        
                        # Update the document
                        collection.update(doc_id, {field: parsed_value})
                        response['success'] = True
                        
                    elif action == 'add':
                        # Try to parse as JSON first, otherwise use as string
                        try:
                            parsed_value = json.loads(value)
                        except json.JSONDecodeError:
                            parsed_value = value
                        
                        # Add field to the document
                        doc = collection.get(doc_id)
                        if doc:
                            doc[field] = parsed_value
                            collection.update(doc_id, doc)
                            response['success'] = True
                        else:
                            response['message'] = 'Document not found'
                    
                except Exception as e:
                    response['message'] = str(e)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except FileNotFoundError:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'message': 'Collection not found'}).encode())
        else:
            self.send_response(404)
            self.end_headers()

# Modify the main section to handle the --view flag
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KoalaDB Management')
    parser.add_argument('--view', action='store_true', help='View database in web browser')
    parser.add_argument('--collection', default=None, help='Specific collection to view (default: show all)')
    args = parser.parse_args()
    
    if args.view:
        # Initialize database
        KoalaDB.initialize()
        
        # Start HTTP server
        port = 8000
        
        with socketserver.TCPServer(("", port), DBRequestHandler) as httpd:
            url = f"http://localhost:{port}"
            if args.collection:
                url += f"/collection/{args.collection}"
            
            print(f"Server started at http://localhost:{port}")
            print(f"Viewing database at: {url}")
            print("Press Ctrl+C to stop the server")
            webbrowser.open(url)
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nShutting down server...")
                httpd.shutdown()
    else:
        # Original example usage code
        print("=== CREATING DOCUMENTS WITH TIMESTAMPS ===")
        # ... rest of the original example code