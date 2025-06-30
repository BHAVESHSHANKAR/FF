import os
import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Connection URI from existing .env file
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'fashion_recommendation')

print(f"Connecting to MongoDB database: {DB_NAME}")
print(f"Using connection URI: {MONGO_URI.split('@')[0].split('://')[0]}://*****@{MONGO_URI.split('@')[1] if '@' in MONGO_URI else 'localhost'}")

try:
    # Create MongoDB client with a reasonable timeout
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    
    # Test connection
    client.admin.command('ping')
    print(f"Successfully connected to MongoDB Atlas!")
    
    # Get database
    db = client[DB_NAME]
    
    # Define collections
    users_collection = db['users']
    uploaded_images_collection = db['uploaded_images']
    
    # Create indexes for better query performance
    users_collection.create_index("username", unique=True)
    uploaded_images_collection.create_index("user_id")
    
except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    print(f"Error connecting to MongoDB: {e}")
    print("This could be due to network issues, incorrect URI, or firewall settings.")
    print("Make sure you have installed pymongo[srv] for Atlas connections:")
    print("    python -m pip install \"pymongo[srv]\"")
    
    # Provide fallback for testing
    print("Using memory-based storage instead of MongoDB")
    
    # Define in-memory collections for testing (if MongoDB is not available)
    class MemoryCollection:
        def __init__(self):
            self.data = []
            self.indexes = {}
        
        def create_index(self, field, unique=False):
            self.indexes[field] = unique
            return True
        
        def insert_one(self, doc):
            # Check unique indexes
            for field, unique in self.indexes.items():
                if unique and field in doc:
                    for existing_doc in self.data:
                        if field in existing_doc and existing_doc[field] == doc[field]:
                            class DuplicateKeyError(Exception):
                                pass
                            raise DuplicateKeyError(f"Duplicate key error: {field}")
            
            # Generate simple _id if not present
            if '_id' not in doc:
                import uuid
                doc['_id'] = str(uuid.uuid4())
            
            # Make a deep copy of the document to store
            import copy
            doc_copy = copy.deepcopy(doc)
            
            # Special handling for password field (it could be bytes)
            if 'password' in doc_copy and isinstance(doc_copy['password'], bytes):
                # Store the bytes as a string for easier in-memory handling
                # This is only for the in-memory store, real MongoDB handles bytes correctly
                print("MemoryCollection: Converting password bytes to string for storage")
                doc_copy['password'] = doc_copy['password'].decode('utf-8', errors='replace')
            
            # Add document to collection
            self.data.append(doc_copy)
            
            # Return simple result object
            class InsertOneResult:
                def __init__(self, id):
                    self.inserted_id = id
            
            return InsertOneResult(doc['_id'])
        
        def find_one(self, query):
            for doc in self.data:
                match = True
                for k, v in query.items():
                    if k not in doc:
                        match = False
                        break
                        
                    # Special handling for ObjectId
                    if k == '_id' and isinstance(v, str) and isinstance(doc[k], str):
                        if str(v) != str(doc[k]):
                            match = False
                            break
                    # Special handling for bytes fields (like password)
                    elif isinstance(v, bytes) and isinstance(doc[k], str):
                        # Skip this comparison and leave it to the application code
                        continue
                    elif v != doc[k]:
                        match = False
                        break
                        
                if match:
                    # Return a copy to prevent mutation
                    import copy
                    return copy.deepcopy(doc)
            return None
        
        def find(self, query=None):
            if query is None:
                query = {}
            
            class Cursor:
                def __init__(self, data, query):
                    self.data = data
                    self.query = query
                    self.sort_field = None
                    self.sort_dir = 1
                    self.skip_count = 0
                    self.limit_count = None
                
                def sort(self, field, direction):
                    if isinstance(field, str):
                        self.sort_field = field
                    else:
                        self.sort_field = field[0]
                    self.sort_dir = direction
                    return self
                
                def skip(self, count):
                    self.skip_count = count
                    return self
                
                def limit(self, count):
                    self.limit_count = count
                    return self
                
                def __iter__(self):
                    results = []
                    for doc in self.data:
                        match = True
                        for k, v in self.query.items():
                            if k not in doc or doc[k] != v:
                                match = False
                                break
                        if match:
                            # Add a copy to prevent mutation
                            import copy
                            results.append(copy.deepcopy(doc))
                    
                    if self.sort_field:
                        results.sort(
                            key=lambda x: x.get(self.sort_field, ""),
                            reverse=self.sort_dir == -1
                        )
                    
                    results = results[self.skip_count:]
                    
                    if self.limit_count:
                        results = results[:self.limit_count]
                    
                    return iter(results)
            
            return Cursor(self.data, query)
        
        def update_one(self, query, update):
            doc = self.find_one(query)
            if doc:
                # Find the actual document in the array (not the copy)
                for i, d in enumerate(self.data):
                    match = True
                    for k, v in query.items():
                        if k not in d or d[k] != v:
                            match = False
                            break
                    if match:
                        # Found the document to update
                        if "$set" in update:
                            for k, v in update["$set"].items():
                                # Special handling for password field
                                if k == 'password' and isinstance(v, bytes):
                                    self.data[i][k] = v.decode('utf-8', errors='replace')
                                else:
                                    self.data[i][k] = v
                
                # Return simple result object
                class UpdateResult:
                    def __init__(self, matched, modified):
                        self.matched_count = matched
                        self.modified_count = modified
                
                return UpdateResult(1, 1)
            
            return UpdateResult(0, 0)
        
        def delete_one(self, query):
            for i, doc in enumerate(self.data):
                match = True
                for k, v in query.items():
                    if k not in doc or doc[k] != v:
                        match = False
                        break
                if match:
                    del self.data[i]
                    
                    # Return simple result object
                    class DeleteResult:
                        def __init__(self, deleted):
                            self.deleted_count = deleted
                    
                    return DeleteResult(1)
            
            return DeleteResult(0)
    
    # Create in-memory collections
    users_collection = MemoryCollection()
    uploaded_images_collection = MemoryCollection()
    
    # Create in-memory db wrapper
    class MemoryDB:
        def __init__(self):
            self.users = users_collection
            self.uploaded_images = uploaded_images_collection
        
        def __getitem__(self, name):
            if name == 'users':
                return self.users
            elif name == 'uploaded_images':
                return self.uploaded_images
            return MemoryCollection()
    
    db = MemoryDB()
    
    # Create test user for in-memory database
    try:
        import bcrypt
        test_password = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt())
        test_user = {
            "_id": "test123",
            "username": "test_user",
            "password": test_password,
            "email": "test@example.com",
            "created_at": time.time(),
            "last_login": None
        }
        users_collection.insert_one(test_user)
        print("Created test user in memory database: username=test_user, password=password123")
        
        # Also create guest account
        guest_password = bcrypt.hashpw("style123".encode('utf-8'), bcrypt.gensalt())
        guest_user = {
            "_id": "guest123",
            "username": "guest",
            "password": guest_password,
            "email": "guest@example.com",
            "name": "Guest User",
            "created_at": time.time(),
            "last_login": None
        }
        users_collection.insert_one(guest_user)
        print("Created guest user in memory database: username=guest, password=style123")
    except Exception as e:
        print(f"Could not create test users in memory database: {e}")
        # Create simpler test users with plaintext passwords as fallback
        users_collection.insert_one({
            "_id": "test123",
            "username": "test_user",
            "password": "password123",  # Plaintext as fallback
            "email": "test@example.com",
            "created_at": time.time(),
            "last_login": None
        })
        users_collection.insert_one({
            "_id": "guest123",
            "username": "guest",
            "password": "style123",  # Plaintext as fallback
            "email": "guest@example.com",
            "name": "Guest User",
            "created_at": time.time(),
            "last_login": None
        })
        print("Created test users with plaintext passwords in memory database")
    
except Exception as e:
    print(f"Unexpected error connecting to MongoDB: {e}")
    print("Falling back to in-memory database")
    
    # Create fallback in-memory database
    class MemoryCollection:
        def __init__(self):
            self.data = []
        
        def create_index(self, *args, **kwargs):
            return True
        
        def insert_one(self, doc):
            import uuid
            doc['_id'] = str(uuid.uuid4())
            
            # Special handling for password field
            if 'password' in doc and isinstance(doc['password'], bytes):
                # Store the bytes as a string for easier in-memory handling
                doc['password'] = doc['password'].decode('utf-8', errors='replace')
            
            self.data.append(doc)
            
            class InsertOneResult:
                def __init__(self, id):
                    self.inserted_id = id
            
            return InsertOneResult(doc['_id'])
        
        def find_one(self, query):
            for doc in self.data:
                match = True
                for k, v in query.items():
                    if k not in doc:
                        match = False
                        break
                    
                    # Special handling for ObjectId
                    if k == '_id' and isinstance(v, str) and isinstance(doc[k], str):
                        if str(v) != str(doc[k]):
                            match = False
                            break
                    elif v != doc[k]:
                        match = False
                        break
                        
                if match:
                    return doc
            return None
    
    users_collection = MemoryCollection()
    uploaded_images_collection = MemoryCollection()
    
    class MemoryDB:
        def __init__(self):
            pass
        
        def __getitem__(self, name):
            if name == 'users':
                return users_collection
            elif name == 'uploaded_images':
                return uploaded_images_collection
            return MemoryCollection()
    
    db = MemoryDB()
    
    # Create test users
    try:
        import bcrypt
        test_password = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt())
        users_collection.insert_one({
            "username": "test_user",
            "password": test_password,
            "email": "test@example.com",
            "created_at": time.time(),
            "last_login": None
        })
        
        guest_password = bcrypt.hashpw("style123".encode('utf-8'), bcrypt.gensalt())
        users_collection.insert_one({
            "username": "guest",
            "password": guest_password,
            "email": "guest@example.com",
            "name": "Guest User",
            "created_at": time.time(),
            "last_login": None
        })
        print("Created test users in fallback memory database")
    except Exception as e:
        print(f"Could not create hashed test users: {e}")
        # Fallback to plaintext
        users_collection.insert_one({
            "username": "test_user",
            "password": "password123",
            "email": "test@example.com",
            "created_at": time.time(),
            "last_login": None
        })
        users_collection.insert_one({
            "username": "guest",
            "password": "style123",
            "email": "guest@example.com", 
            "name": "Guest User",
            "created_at": time.time(),
            "last_login": None
        })
        print("Created plaintext test users in fallback memory database")

def get_db():
    """
    Get the database connection
    
    Returns:
        MongoDB database connection
    """
    return db 