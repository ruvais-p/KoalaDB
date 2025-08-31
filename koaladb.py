import os
import uuid
import bson
import shutil
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Union, List
from pathlib import Path

class KoalaDB:
    db_path = "KoalaDB"
    store_path = os.path.join(db_path, "store")
    
    @staticmethod
    def initialize(path="KoalaDB"):
        """Initialize the DB directory and store folder."""
        KoalaDB.db_path = path
        KoalaDB.store_path = os.path.join(path, "store")
        
        if not os.path.exists(path):
            os.makedirs(path)
        
        # Create store directory for media files
        if not os.path.exists(KoalaDB.store_path):
            os.makedirs(KoalaDB.store_path)
            
        print(f"Database initialized at {os.path.abspath(path)}")
        print(f"Media store at {os.path.abspath(KoalaDB.store_path)}")
    
    @staticmethod
    def createCollection(name: str):
        """Create a collection with given name."""
        collection_path = os.path.join(KoalaDB.db_path, name)
        if not os.path.exists(collection_path):
            os.makedirs(collection_path)
            with open(os.path.join(collection_path, "data.bson"), "wb") as f:
                f.write(bson.encode({}))
            print(f"Collection '{name}' created.")
        else:
            print(f"Collection '{name}' already exists.")
    
    @staticmethod
    def collection(name: str):
        """Return collection object."""
        return Collection(name)

class Collection:
    def __init__(self, name):
        self.name = name
        self.collection_path = os.path.join(KoalaDB.db_path, name, "data.bson")
        
        if not os.path.exists(self.collection_path):
            raise FileNotFoundError(f"Collection {name} not found. Did you create it?")
        
        # Load existing data
        with open(self.collection_path, "rb") as f:
            raw = f.read()
            self.data = bson.decode(raw) if raw else {}
    
    def create(self, object_id=None, auto_timestamp=True):
        """Create a new document stub with optional automatic timestamps."""
        if object_id is None:
            object_id = str(uuid.uuid4())
        if object_id in self.data:
            raise ValueError("Object ID already exists!")
        
        self.data[object_id] = {}
        
        # Add automatic timestamps if enabled
        if auto_timestamp:
            now = self.get_current_timestamp()
            self.data[object_id]["_created_at"] = now
            self.data[object_id]["_updated_at"] = now
        
        return Document(self, object_id)
    
    def save(self):
        """Save current collection to BSON file."""
        with open(self.collection_path, "wb") as f:
            f.write(bson.encode(self.data))
    
    def find(self, object_id=None, query=None):
        """Find documents by ID or query."""
        if object_id:
            return self.data.get(object_id, None)
        
        if query:
            results = {}
            for doc_id, doc_data in self.data.items():
                if self._matches_query(doc_data, query):
                    results[doc_id] = doc_data
            return results
        
        # Return all documents if no parameters
        return self.data
    
    def find_one(self, query=None):
        """Find first document matching query."""
        if query:
            for doc_id, doc_data in self.data.items():
                if self._matches_query(doc_data, query):
                    return {doc_id: doc_data}
        return None
    
    def find_by_date_range(self, field: str, start_date: datetime, end_date: datetime):
        """Find documents where a date field falls within a specified range."""
        query = {
            field: {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        return self.find(query=query)
    
    def find_created_between(self, start_date: datetime, end_date: datetime):
        """Find documents created between two dates."""
        return self.find_by_date_range("_created_at", start_date, end_date)
    
    def find_updated_between(self, start_date: datetime, end_date: datetime):
        """Find documents updated between two dates."""
        return self.find_by_date_range("_updated_at", start_date, end_date)
    
    def find_recent(self, field: str = "_created_at", hours: int = 24):
        """Find documents created/updated within the last N hours."""
        cutoff_time = self.get_current_timestamp() - (hours * 3600)  # Convert hours to seconds
        query = {field: {"$gte": cutoff_time}}
        return self.find(query=query)
    
    def find_older_than(self, field: str = "_created_at", days: int = 30):
        """Find documents older than N days."""
        cutoff_time = self.get_current_timestamp() - (days * 24 * 3600)  # Convert days to seconds
        query = {field: {"$lt": cutoff_time}}
        return self.find(query=query)
    
    def update(self, object_id, update_data, auto_timestamp=True):
        """Update a document by ID with optional automatic timestamp update."""
        if object_id not in self.data:
            raise ValueError(f"Document with ID '{object_id}' not found")
        
        if not isinstance(update_data, dict):
            raise TypeError("Update data must be a dict")
        
        # Add automatic timestamp update
        if auto_timestamp:
            update_data["_updated_at"] = self.get_current_timestamp()
        
        self.data[object_id].update(update_data)
        self.save()
        return True
    
    def update_many(self, query, update_data, auto_timestamp=True):
        """Update multiple documents matching query with optional automatic timestamps."""
        if not isinstance(update_data, dict):
            raise TypeError("Update data must be a dict")
        
        # Add automatic timestamp update
        if auto_timestamp:
            update_data["_updated_at"] = self.get_current_timestamp()
        
        updated_count = 0
        for doc_id, doc_data in self.data.items():
            if self._matches_query(doc_data, query):
                self.data[doc_id].update(update_data)
                updated_count += 1
        
        if updated_count > 0:
            self.save()
        return updated_count
    
    def delete(self, object_id):
        """Delete a document by ID and its associated media files."""
        if object_id not in self.data:
            raise ValueError(f"Document with ID '{object_id}' not found")
        
        # Delete associated media files
        self._delete_document_media(object_id)
        
        del self.data[object_id]
        self.save()
        return True
    
    def delete_many(self, query):
        """Delete multiple documents matching query and their associated media files."""
        to_delete = []
        for doc_id, doc_data in self.data.items():
            if self._matches_query(doc_data, query):
                to_delete.append(doc_id)
        
        for doc_id in to_delete:
            # Delete associated media files
            self._delete_document_media(doc_id)
            del self.data[doc_id]
        
        if to_delete:
            self.save()
        return len(to_delete)
    
    def _delete_document_media(self, object_id):
        """Delete all media files associated with a document."""
        doc = self.data.get(object_id, {})
        
        # Find all media file paths in the document
        media_paths = []
        for key, value in doc.items():
            if isinstance(value, str) and value.startswith('store/'):
                media_paths.append(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item.startswith('store/'):
                        media_paths.append(item)
        
        # Delete the media files
        for media_path in media_paths:
            full_path = os.path.join(KoalaDB.db_path, media_path)
            try:
                if os.path.exists(full_path):
                    os.remove(full_path)
                    print(f"Deleted media file: {media_path}")
            except Exception as e:
                print(f"Error deleting media file {media_path}: {e}")
    
    def count(self, query=None):
        """Count documents matching query."""
        if query is None:
            return len(self.data)
        
        count = 0
        for doc_data in self.data.values():
            if self._matches_query(doc_data, query):
                count += 1
        return count
    
    def get_oldest_document(self, field: str = "_created_at"):
        """Get the document with the oldest timestamp for a given field."""
        if not self.data:
            return None
        
        oldest_id = None
        oldest_time = float('inf')
        
        for doc_id, doc_data in self.data.items():
            if field in doc_data and doc_data[field] < oldest_time:
                oldest_time = doc_data[field]
                oldest_id = doc_id
        
        return {oldest_id: self.data[oldest_id]} if oldest_id else None
    
    def get_newest_document(self, field: str = "_created_at"):
        """Get the document with the newest timestamp for a given field."""
        if not self.data:
            return None
        
        newest_id = None
        newest_time = 0
        
        for doc_id, doc_data in self.data.items():
            if field in doc_data and doc_data[field] > newest_time:
                newest_time = doc_data[field]
                newest_id = doc_id
        
        return {newest_id: self.data[newest_id]} if newest_id else None
    
    def cleanup_old_documents(self, days: int = 30, field: str = "_created_at"):
        """Delete documents older than specified days."""
        old_docs = self.find_older_than(field, days)
        deleted_count = 0
        
        for doc_id in old_docs:
            # Delete associated media files
            self._delete_document_media(doc_id)
            del self.data[doc_id]
            deleted_count += 1
        
        if deleted_count > 0:
            self.save()
            print(f"Cleaned up {deleted_count} old documents")
        
        return deleted_count
    
    def store_media_file(self, file_path: str, object_id: str = None, field_name: str = None):
        """
        Store a media file in the store directory and return the relative path.
        If object_id and field_name are provided, automatically update the document.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Generate a unique filename
        file_ext = os.path.splitext(file_path)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        store_file_path = os.path.join(KoalaDB.store_path, unique_filename)
        relative_path = f"store/{unique_filename}"
        
        # Copy the file to the store directory
        shutil.copy2(file_path, store_file_path)
        
        # If object_id and field_name are provided, update the document
        if object_id and field_name:
            if object_id not in self.data:
                raise ValueError(f"Document with ID '{object_id}' not found")
            
            update_data = {field_name: relative_path}
            self.update(object_id, update_data)
        
        return relative_path
    
    def store_multiple_media_files(self, file_paths: List[str], object_id: str = None, field_name: str = None):
        """
        Store multiple media files in the store directory and return the relative paths.
        If object_id and field_name are provided, automatically update the document.
        """
        stored_paths = []
        
        for file_path in file_paths:
            stored_path = self.store_media_file(file_path)
            stored_paths.append(stored_path)
        
        # If object_id and field_name are provided, update the document
        if object_id and field_name:
            if object_id not in self.data:
                raise ValueError(f"Document with ID '{object_id}' not found")
            
            update_data = {field_name: stored_paths}
            self.update(object_id, update_data)
        
        return stored_paths
    
    def get_media_file_path(self, relative_path: str):
        """Get the absolute path of a media file from its relative path."""
        return os.path.join(KoalaDB.db_path, relative_path)
    
    def get_media_file_url(self, relative_path: str, base_url: str = "/media"):
        """Get a URL for accessing a media file (for web applications)."""
        return f"{base_url}/{relative_path}"
    
    @staticmethod
    def get_current_timestamp():
        """Get current UTC timestamp as seconds since epoch."""
        return datetime.now(timezone.utc).timestamp()
    
    @staticmethod
    def timestamp_to_datetime(timestamp: Union[int, float]):
        """Convert timestamp to datetime object."""
        return datetime.fromtimestamp(timestamp, timezone.utc)
    
    @staticmethod
    def datetime_to_timestamp(dt: datetime):
        """Convert datetime object to timestamp."""
        return dt.timestamp()
    
    @staticmethod
    def format_timestamp(timestamp: Union[int, float], format_str: str = "%Y-%m-%d %H:%M:%S UTC"):
        """Format timestamp as human-readable string."""
        dt = Collection.timestamp_to_datetime(timestamp)
        return dt.strftime(format_str)
    
    @staticmethod
    def parse_date_string(date_string: str, format_str: str = "%Y-%m-%d"):
        """Parse date string into datetime object."""
        return datetime.strptime(date_string, format_str).replace(tzinfo=timezone.utc)
    
    def get_documents_by_date(self, date: Union[str, datetime], field: str = "_created_at"):
        """Get all documents from a specific date (ignores time)."""
        if isinstance(date, str):
            target_date = self.parse_date_string(date)
        else:
            target_date = date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        
        # Get start and end of the day
        start_of_day = target_date.timestamp()
        end_of_day = target_date.replace(hour=23, minute=59, second=59).timestamp()
        
        return self.find_by_date_range(field, start_of_day, end_of_day)
    
    def group_by_date(self, field: str = "_created_at", date_format: str = "%Y-%m-%d"):
        """Group documents by date."""
        grouped = {}
        
        for doc_id, doc_data in self.data.items():
            if field in doc_data:
                date_str = self.format_timestamp(doc_data[field], date_format)
                if date_str not in grouped:
                    grouped[date_str] = {}
                grouped[date_str][doc_id] = doc_data
        
        return grouped
    
    def _matches_query(self, document, query):
        """Check if document matches query conditions."""
        for key, value in query.items():
            if key not in document:
                return False
            
            # Handle different comparison operators
            if isinstance(value, dict):
                for op, op_value in value.items():
                    if op == "$gt":
                        if not (document[key] > op_value):
                            return False
                    elif op == "$lt":
                        if not (document[key] < op_value):
                            return False
                    elif op == "$gte":
                        if not (document[key] >= op_value):
                            return False
                    elif op == "$lte":
                        if not (document[key] <= op_value):
                            return False
                    elif op == "$ne":
                        if not (document[key] != op_value):
                            return False
                    elif op == "$in":
                        if document[key] not in op_value:
                            return False
                    elif op == "$nin":
                        if document[key] in op_value:
                            return False
            else:
                # Simple equality check
                if document[key] != value:
                    return False
        return True

class Document:
    def __init__(self, collection, object_id):
        self.collection = collection
        self.object_id = object_id
    
    def add(self, data: dict, auto_timestamp=True):
        """Add data to the object and save with optional timestamp update."""
        if not isinstance(data, dict):
            raise TypeError("Data must be a dict")
        
        # Add automatic timestamp update
        if auto_timestamp:
            data["_updated_at"] = Collection.get_current_timestamp()
        
        self.collection.data[self.object_id].update(data)
        self.collection.save()
        return self  # chaining
    
    def add_media_file(self, file_path: str, field_name: str):
        """Add a media file to the document."""
        return self.collection.store_media_file(file_path, self.object_id, field_name)
    
    def add_multiple_media_files(self, file_paths: List[str], field_name: str):
        """Add multiple media files to the document."""
        return self.collection.store_multiple_media_files(file_paths, self.object_id, field_name)
    
    def get_media_file_path(self, field_name: str):
        """Get the absolute path of a media file stored in the document."""
        if field_name not in self.collection.data[self.object_id]:
            raise ValueError(f"Field '{field_name}' not found in document")
        
        relative_path = self.collection.data[self.object_id][field_name]
        return self.collection.get_media_file_path(relative_path)
    
    def get_media_file_url(self, field_name: str, base_url: str = "/media"):
        """Get a URL for accessing a media file stored in the document."""
        if field_name not in self.collection.data[self.object_id]:
            raise ValueError(f"Field '{field_name}' not found in document")
        
        relative_path = self.collection.data[self.object_id][field_name]
        return self.collection.get_media_file_url(relative_path, base_url)
    
    def get_age_in_seconds(self, field: str = "_created_at"):
        """Get the age of the document in seconds."""
        if field not in self.collection.data[self.object_id]:
            raise ValueError(f"Field '{field}' not found in document")
        
        doc_timestamp = self.collection.data[self.object_id][field]
        current_timestamp = Collection.get_current_timestamp()
        return current_timestamp - doc_timestamp
    
    def get_age_in_days(self, field: str = "_created_at"):
        """Get the age of the document in days."""
        return self.get_age_in_seconds(field) / (24 * 3600)
    
    def get_formatted_timestamp(self, field: str = "_created_at", format_str: str = "%Y-%m-%d %H:%M:%S UTC"):
        """Get a formatted timestamp for a specific field."""
        if field not in self.collection.data[self.object_id]:
            raise ValueError(f"Field '{field}' not found in document")
        
        timestamp = self.collection.data[self.object_id][field]
        return Collection.format_timestamp(timestamp, format_str)
    
    def touch(self):
        """Update the _updated_at timestamp to current time."""
        self.collection.data[self.object_id]["_updated_at"] = Collection.get_current_timestamp()
        self.collection.save()
        return self

# Example usage and helper functions
class DateTimeHelpers:
    """Additional helper functions for common date/time operations."""
    
    @staticmethod
    def get_start_of_day(dt: datetime = None):
        """Get start of day (00:00:00) for given datetime or current date."""
        if dt is None:
            dt = datetime.now(timezone.utc)
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    
    @staticmethod
    def get_end_of_day(dt: datetime = None):
        """Get end of day (23:59:59) for given datetime or current date."""
        if dt is None:
            dt = datetime.now(timezone.utc)
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    @staticmethod
    def get_start_of_week(dt: datetime = None):
        """Get start of week (Monday 00:00:00) for given datetime or current date."""
        if dt is None:
            dt = datetime.now(timezone.utc)
        start_of_day = DateTimeHelpers.get_start_of_day(dt)
        days_since_monday = start_of_day.weekday()
        return start_of_day - timedelta(days=days_since_monday)
    
    @staticmethod
    def get_start_of_month(dt: datetime = None):
        """Get start of month for given datetime or current date."""
        if dt is None:
            dt = datetime.now(timezone.utc)
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
