import os
import json
import psycopg2
from psycopg2.extras import execute_values

class TireDatabase:
    def __init__(self, db_url=None):
        """Initialize database connection using URL from environment or parameter"""
        # Default to the Neon database connection string if none is provided
        self.db_url = db_url or os.environ.get('DATABASE_URL', 
            "postgresql://neondb_owner:npg_lrCXzKNO9A2t@ep-ancient-queen-a2bhzxqa-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require")
        self.conn = None
        
    def connect(self):
        """Establish database connection"""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(self.db_url)
        return self.conn
    
    def create_tables(self):
        """Create tables if they don't exist (not needed since table is already created)"""
        # Table already created in Neon, so we don't need this method
        # but keeping it for completeness
        return True
    
    def import_from_json(self, json_file="combined_tire_data.json"):
        """Import data from JSON file to the Neon database"""
        try:
            # First, load the JSON data
            script_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(script_dir, json_file)
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            with self.connect() as conn:
                with conn.cursor() as cur:
                    # Clear existing tires data
                    cur.execute("DELETE FROM tires")
                    conn.commit()
                    
                    # Prepare data for bulk insert
                    values = []
                    for item in data:
                        # Convert string numeric values to integers where needed
                        try:
                            width = int(item.get('width')) if item.get('width') else None
                            aspect_ratio = int(item.get('aspect_ratio')) if item.get('aspect_ratio') else None
                            rim_size = int(item.get('rim_size')) if item.get('rim_size') else None
                            
                            # Try to parse price to decimal, removing any non-numeric chars
                            price_str = str(item.get('price', '')).replace('.', '').replace(',', '.')
                            import re
                            price_digits = re.sub(r'[^\d.,]', '', price_str)
                            price = float(price_digits) if price_digits else None
                        except (ValueError, TypeError):
                            # If conversion fails, use None
                            width = None
                            aspect_ratio = None
                            rim_size = None
                            price = None
                        
                        values.append((
                            item.get('seller'),
                            item.get('manufacturer'),
                            item.get('product_name', item.get('title')),  # Fallback to title if product_name not found
                            width,
                            aspect_ratio,
                            rim_size,
                            price,
                            item.get('stock'),
                            item.get('inventory_count'),
                            item.get('picture')
                        ))
                    
                    # Bulk insert
                    execute_values(
                        cur,
                        """
                        INSERT INTO tires (
                            seller, manufacturer, product_name,
                            width, aspect_ratio, rim_size,
                            price, stock, inventory_count, picture
                        ) VALUES %s
                        """,
                        values
                    )
                    
                    conn.commit()
                    return True, f"Successfully imported {len(values)} tires into Neon database"
        except Exception as e:
            import traceback
            return False, f"Error importing data: {str(e)}\n{traceback.format_exc()}"
