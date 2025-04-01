import json
import re
from pathlib import Path
import os

def parse_size(size_str):
    if not size_str:
        return None, None, None
    patterns = [
        r'(\d{3})[/-](\d{2})[/-R]?(\d{2})',   # 185-55-15, 185/55R15
        r'(\d{3})(\d{2})(\d{2})',             # 1855515
    ]
    for pattern in patterns:
        match = re.search(pattern, size_str)
        if match:
            return match.group(1), match.group(2), match.group(3)
    return None, None, None

def normalize_price(price_str):
    if not price_str:
        return None
    price_clean = re.sub(r'[^\d]', '', price_str)
    return float(price_clean) if price_clean else None

def is_valid_tire(width, aspect, rim):
    try:
        width = int(width)
        aspect = int(aspect)
        rim = int(rim)
        return all([
            100 <= width <= 400,
            20 <= aspect <= 95,
            10 <= rim <= 30
        ])
    except (TypeError, ValueError):
        return False

def extract_klettur_details(product_name):
    if not product_name:
        return None, product_name
    parts = product_name.split()
    # Check if first part is size format (e.g., 225/45R17)
    if len(parts) > 1 and re.match(r'\d{3}/\d{2}R\d{2}', parts[0]):
        if len(parts) >= 3:
            manufacturer = parts[2]
            type_name = ' '.join(parts[3:]) if len(parts) > 3 else ""
            return manufacturer, type_name.strip()
        else:
            # Not enough parts, just remove size
            return None, ' '.join(parts[1:]).strip()
    return None, product_name.strip()

def main():
    # Get script directory - should work both on development and production
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    print(f"Script directory: {script_dir}")
    print(f"Project directory: {project_dir}")

    sellers_files = {
        'Klettur': os.path.join(project_dir, 'klettur.json'),
        'Dekkjahollin': os.path.join(project_dir, 'dekkjahollin.json'),
        'Dekkjasalan': os.path.join(project_dir, 'dekkjasalan.json'),
        'Mitra': os.path.join(project_dir, 'mitra.json'),
        'N1': os.path.join(project_dir, 'n1.json'),
        'Nesdekk': os.path.join(project_dir, 'nesdekk.json')
    }

    combined_tires = []

    for seller, filename in sellers_files.items():
        if not os.path.exists(filename):
            print(f"Warning: File not found: {filename}")
            continue
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Loaded {len(data)} items from {seller}")
                
                for item in data:
                    width, aspect, rim = None, None, None

                    if seller == 'Klettur':
                        width, aspect, rim = item.get('Width'), item.get('Height'), item.get('RimSize')
                        if width == 0 or aspect == 0 or rim == 0:
                            continue  # skip non-tire items
                        product_name = item.get('ItemName')
                        price = item.get('Price')
                        stock = 'in stock' if item.get('QTY', 0) > 0 else 'out of stock'
                        inventory = item.get('QTY')
                        picture = item.get('photourl')
                        manufacturer, product_name = extract_klettur_details(product_name)

                    elif seller == 'Dekkjahollin':
                        width, aspect, rim = parse_size(item.get('tire_size'))
                        product_name = item.get('title')
                        price = normalize_price(item.get('price'))
                        stock = 'in stock' if 'til í' in item.get('stock', '').lower() else 'out of stock'
                        inventory = None
                        picture = item.get('picture')
                        manufacturer = item.get('manufacturer')

                    elif seller == 'Dekkjasalan':
                        width, aspect, rim = parse_size(item.get('tire_size'))
                        product_name = item.get('title')
                        price_total = normalize_price(item.get('price'))
                        inventory = item.get('inventory')
                        if inventory and inventory > 1:
                            price = price_total / inventory
                            product_name += f" (sold as set of {inventory})"
                        else:
                            price = price_total
                        stock = item.get('stock')
                        picture = item.get('picture')
                        manufacturer = item.get('manufacturer')

                    elif seller == 'Mitra':
                        width, aspect, rim = item.get('width'), item.get('profile'), item.get('rim')
                        product_name = item.get('title')
                        price = normalize_price(item.get('price'))
                        stock = item.get('stock')
                        inventory = item.get('inventory')
                        picture = item.get('picture')
                        manufacturer = item.get('manufacturer')

                    elif seller == 'N1':
                        width, aspect, rim = parse_size(item.get('size'))
                        product_name = item.get('name')
                        price = normalize_price(item.get('price'))
                        stock = item.get('stock')
                        inventory = None
                        picture = item.get('picture')
                        manufacturer = item.get('manufacturer')

                    elif seller == 'Nesdekk':
                        width, aspect, rim = parse_size(item.get('tyre_size'))
                        product_name = item.get('name')
                        price = normalize_price(item.get('price'))
                        stock_text = item.get('stock', '').lower()
                        stock = 'in stock' if 'á lager' in stock_text else 'out of stock'
                        inventory = None
                        picture = item.get('picture')
                        manufacturer = item.get('manufacturer')

                    combined_tires.append({
                        "seller": seller,
                        "manufacturer": manufacturer,
                        "product_name": product_name,
                        "width": width,
                        "aspect_ratio": aspect,
                        "rim_size": rim,
                        "size": item.get('size') or item.get('tire_size') or item.get('tyre_size'),
                        "price": price,
                        "stock": stock,
                        "inventory_count": inventory,
                        "picture": picture
                    })
                    
        except Exception as e:
            import traceback
            print(f"Error processing {filename}: {str(e)}")
            print(traceback.format_exc())

    # Write out the combined file
    out_file = os.path.join(project_dir, 'combined_tire_data.json')
    with open(out_file, 'w', encoding='utf-8') as out:
        json.dump(combined_tires, out, ensure_ascii=False, indent=2)

    print(f"✅ Successfully combined {len(combined_tires)} tire items into {out_file}")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
