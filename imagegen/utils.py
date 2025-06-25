import os
import json
from PIL import Image
from PIL.Image import Resampling
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import cv2
import numpy as np
from rembg import remove
from django.urls import path
from typing import Dict
import ezdxf
import uuid
import subprocess
from typing import List, Tuple, Dict






# Define color mappings
WALL_COLOR_MAP = {
    (0, 0, 0): "Outer walls",  # Black
}

AREA_COLOR_MAP = {
    (238, 232, 170): "Living room",    # Light Yellow
    (254, 215, 0): "Common room",      # Yellow
    (240, 128, 127): "Kitchen",        # Light Coral
    (173, 217, 230): "Bathroom",       # Light Blue
    (254, 165, 0): "Master room",      # Orange
    (106, 142, 34): "Balcony",         # Olive Green
    (218, 112, 213): "Storage",        # Orchid
    (254, 254, 255): "Inner walls",    # White-ish
    (253, 1, 0): "Main gate",          # Red
}

class ArchitecturalDimensions:
    def __init__(self, pixels_per_foot: float = 12):
        self.pixels_per_foot = pixels_per_foot
    
    def pixels_to_architectural(self, pixels: float) -> str:
        """Convert pixels to architectural format (feet'-inches")"""
        total_inches = (pixels / self.pixels_per_foot) * 12
        feet = int(total_inches // 12)
        inches = round(total_inches % 12, 1)
        return f"{feet}'-{inches}\""
    
    def calculate_area(self, polygon: List[List[int]]) -> Tuple[float, str]:
        """Calculate area in square feet and return formatted string."""
        poly = np.array(polygon, dtype=np.float32)
        area_pixels = cv2.contourArea(poly)
        area_sqft = area_pixels / (self.pixels_per_foot ** 2)
        return area_sqft, f"{area_sqft:.1f} sq ft"

class ArchitecturalDrawing:
    def __init__(self, width: int, height: int, dims: ArchitecturalDimensions):
        self.width = width
        self.height = height
        self.dims = dims
        self.image = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # def draw_wall(self, start, end, 
    #              thickness: int = 5, color = (0, 0, 0)):
    #     """Draw a wall with proper thickness"""
    #     cv2.line(self.image, start, end, color, thickness)
    def draw_wall(self, start: Tuple[int, int], end: Tuple[int, int], thickness: int = 5):
        """Draw thick walls between start and end points."""
        cv2.line(self.image, start, end, (0, 0, 0), thickness)

    def draw_text_with_outline(self, text: str, position: Tuple[int, int], font_scale: float, color: Tuple[int, int, int]):
        """Draw text with white outline for visibility."""
        cv2.putText(self.image, text, position, cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale, (255, 255, 255), thickness=3, lineType=cv2.LINE_AA)
        cv2.putText(self.image, text, position, cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale, color, thickness=1, lineType=cv2.LINE_AA)
        

    def draw_arrowed_dimension_line(self, start: Tuple[int, int], end: Tuple[int, int], offset: int = 60):
        """Draw dimension line with arrows and measurement."""
        dx, dy = end[0] - start[0], end[1] - start[1]
        angle = np.arctan2(dy, dx)
        length = np.sqrt(dx*dx + dy*dy)

        offset_vec = np.array([-np.sin(angle), np.cos(angle)]) * offset
        start_offset = np.array(start) + offset_vec
        end_offset = np.array(end) + offset_vec

        cv2.arrowedLine(self.image, tuple(start_offset.astype(int)), tuple(end_offset.astype(int)), (0, 0, 0), 1, tipLength=0.02)
        cv2.arrowedLine(self.image, tuple(end_offset.astype(int)), tuple(start_offset.astype(int)), (0, 0, 0), 1, tipLength=0.02)
        
        # Extension lines
        cv2.line(self.image, start, tuple(start_offset.astype(int)), (0, 0, 0), 1)
        cv2.line(self.image, end, tuple(end_offset.astype(int)), (0, 0, 0), 1)

        # Measurement text
        text = self.dims.pixels_to_architectural(length)
        mid_point = ((start_offset + end_offset) / 2).astype(int)
        self.draw_text_with_outline(text, tuple(mid_point), font_scale=0.5, color=(0, 0, 0))
    

    def draw_room_label(self, polygon: List[List[int]], label: str, area: str):
        """Draw room label and area centered inside polygon."""
        poly = np.array(polygon)
        moments = cv2.moments(poly)
        if moments['m00'] != 0:
            cx = int(moments['m10'] / moments['m00'])
            cy = int(moments['m01'] / moments['m00'])
            font_scale = 0.6

            self.draw_text_with_outline(label, (cx - 40, cy - 10), font_scale, (0, 0, 0))
            self.draw_text_with_outline(area, (cx - 35, cy + 15), font_scale * 0.8, (100, 100, 100))
     
    
    

def calculate_edge_lengths(polygon):
    """Calculate edge lengths for a polygon."""
    edges = []
    num_points = len(polygon)
    for i in range(num_points):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % num_points]  # Wrap to the first point
        length = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
        edges.append({"start": (x1, y1), "end": (x2, y2), "length": round(length, 2)})
    return edges

def calculate_polygon_area(polygon, pixels_per_foot=12, label=None):
    """Calculate area of a polygon in square feet. Handle 'Outer walls' differently."""
    if label == "Outer walls":
        # Calculate bounding box area
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        area_pixels = width * height
    else:
        # Normal polygon area (shoelace formula)
        n = len(polygon)
        area_pixels = 0
        for i in range(n):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % n]
            area_pixels += (x1 * y2) - (x2 * y1)
        area_pixels = abs(area_pixels) / 2.0

    # Convert from pixel² to foot²
    area_feet = area_pixels / (pixels_per_foot ** 2)
    return round(area_feet, 2)



def extract_polygons(image, color_map, tolerance=0, epsilon_factor=0.0, filter_image=False):
    """Extract polygons based on color matching."""
    polygons = []  # Store all polygons with their labels
    mask_visual = np.zeros_like(image[:, :, 0])  # Initialize a blank mask for visualization
    
    # Apply bilateral filter if specified
    if filter_image:
        image = cv2.bilateralFilter(image, 9, 4, 3)

    for color, label in color_map.items():
        lower_bound = np.array([max(0, c - tolerance) for c in color], dtype=np.uint8)
        upper_bound = np.array([min(255, c + tolerance) for c in color], dtype=np.uint8)

        # Create a mask for the current color
        mask = cv2.inRange(image, lower_bound, upper_bound)


        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            epsilon = epsilon_factor * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            polygon = [(int(point[0][0]), int(point[0][1])) for point in approx]

            # Calculate edge lengths
            edges = calculate_edge_lengths(polygon)
            
            # Calculate area
            area_sqft = calculate_polygon_area(polygon, pixels_per_foot=12, label=label)
            
            polygons.append({
                "label": label,
                "polygon": polygon,
                "edges": edges,          # Add edge lengths
                "area_sqft": area_sqft    # Add area in square feet
            })


            # Draw the polygon on the visualization mask
            cv2.fillPoly(mask_visual, [np.array(polygon, dtype=np.int32).reshape((-1, 1, 2))], 255)


    return polygons

def visualize_floor_plan(json_data: Dict, output_path: str):
    dims = ArchitecturalDimensions(pixels_per_foot=12)  
    drawing = ArchitecturalDrawing(1024, 1024, dims)
    
    # Draw walls with dimensions
    for wall in json_data['walls']:
        for edge in wall['edges']:
            start = tuple(map(int, edge['start']))
            end = tuple(map(int, edge['end']))
            drawing.draw_wall(start, end, thickness=6)
            if edge['length'] > 35:  # Only label if big enough
                drawing.draw_arrowed_dimension_line(start, end)
    
    # Draw areas with labels
    for area in json_data['areas']:
        label = area['label']
        polygon = np.array(area['polygon'], dtype=np.int32)

        # Skip drawing if area_sqft < 5.0
        area_sqft = area.get('area_sqft', 0)
        if area_sqft < 3.0:
            continue  # Skip this area

        if label == 'Inner walls':
            fill_color = (220, 220, 200)
            cv2.polylines(drawing.image, [polygon], isClosed=True, color=(0, 0, 0), thickness=2)
        else:
            fill_color = (230, 230, 255)  # Light color for other rooms

        cv2.fillPoly(drawing.image, [polygon], fill_color)

        if label not in ['Inner walls', 'Main gate']:
            area_value, area_text = dims.calculate_area(area['polygon'])
            drawing.draw_room_label(area['polygon'], label, area_text)


    # Compute and display total wall area if available
    total_wall_area = 0.0
    for wall in json_data.get('walls', []):
        if 'area_sqft' in wall:
            total_wall_area += wall['area_sqft']

    # Draw the wall area text on the image
    wall_area_text = f"Total area: {total_wall_area:.1f} sq ft, in Marla: {total_wall_area / 272.25:.2f}"
    drawing.draw_text_with_outline(wall_area_text, position=(500, 100), font_scale=0.7, color=(0, 0, 255))
    # Add scale bar
    scale_length_pixels = int(dims.pixels_per_foot * 12)  
    scale_bar_start = (100, 950)
    scale_bar_end = (100 + scale_length_pixels, 950)
    cv2.line(drawing.image, scale_bar_start, scale_bar_end, (0, 0, 0), 3)
    drawing.draw_text_with_outline("12pix = 1'", (scale_bar_start[0] + scale_length_pixels // 2 - 10, scale_bar_start[1] - 10), 0.7, (0, 0, 0))
    
        
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, drawing.image)
    return output_path

# 'process_floor_plan' takes image and return json file 
def process_floor_plan(image_path, wall_color_map, area_color_map, format, tolerance=23):
    """Process floor plan and extract geometric data."""
    # Load the image
    original_image = cv2.imread(image_path)
    if original_image is None:
        raise FileNotFoundError(f"Image not found at path: {image_path}")
    original_rgb_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
    
    # Decide size based on format
    if format.lower() == 'dxf':
        target_size = (256, 256)
    else:
        target_size = (1024, 1024)
    
    # Resize image
    original_image_rgb = cv2.resize(original_rgb_image, target_size, interpolation=cv2.INTER_LANCZOS4)


    # Wall extraction (outer walls)
    wall_polygons = extract_polygons(original_image_rgb, wall_color_map, 
                                     tolerance=30, epsilon_factor=0.0001)

    # Background removal
    output_dir = os.path.join(settings.MEDIA_ROOT, "no_bg_images")
    os.makedirs(output_dir, exist_ok=True)

    # Open the input image and remove the background
    input_image = Image.open(image_path)

    # Resize input image (for background removal) based on target size
    resized_image = input_image.resize(target_size, resample=Resampling.LANCZOS)
    
    # Remove background from the resized image
    background_removed = remove(resized_image)

    # Generate filename for the no-background image
    filename_base = os.path.splitext(os.path.basename(image_path))[0]
    output_path = os.path.join(output_dir, f"{filename_base}_no_bg.png")
    background_removed.save(output_path)

    # Area extraction
    no_bg_image = cv2.imread(output_path)
    no_bg_image_rgb = cv2.cvtColor(no_bg_image, cv2.COLOR_BGR2RGB)
    area_polygons = extract_polygons(no_bg_image_rgb, area_color_map, 
                                     tolerance=tolerance, epsilon_factor=0.001, 
                                     filter_image=True)

    # Save as JSON
    combined_polygons = {"walls": wall_polygons, "areas": area_polygons}
    unique_filename = f"floor_plan_{uuid.uuid4().hex}.json"
    json_output_path = os.path.join(settings.MEDIA_ROOT, "json_data", unique_filename)
    os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
    
    with open(json_output_path, 'w') as f:
        json.dump(combined_polygons, f, indent=4)

    return json_output_path




def get_area_color(label):
    AREA_COLOR_MAP = {
        "Living room": 10,   # Yellow
        "Common room": 2,    # Green
        "Kitchen": 3,        # Red
        "Bathroom": 5,       # Blue
        "Master room": 6,    # Cyan
        "Balcony": 7,        # Magenta
        "Storage": 8,        # White
        "Inner walls": 9,    # Black
        "Main gate": 1,      # Dark red
    }
    return AREA_COLOR_MAP.get(label, 7)  # Default to white if no color found

def json_to_dxf(json_file, dxf_file):
    """Convert floor plan polygons from JSON to DXF format."""
    with open(json_file, 'r') as f:
        data = json.load(f)

    walls = data['walls']
    areas = data['areas']

    doc = ezdxf.new()
    msp = doc.modelspace()

    for polygon_data in walls:
        polygon = polygon_data['polygon']
        msp.add_lwpolyline(polygon, dxfattribs={'closed': True, 'layer': 'Walls'})

    for polygon_data in areas:
        label = polygon_data['label']
        polygon = polygon_data['polygon']
        layer_color = get_area_color(label)
        layer_name = label.replace(" ", "_")
        
        if layer_name not in doc.layers:
            doc.layers.new(name=layer_name, dxfattribs={'color': layer_color})

        msp.add_lwpolyline(polygon, dxfattribs={'closed': True, 'layer': layer_name})

    # Save the DXF file
    doc.saveas(dxf_file)


DXF_FOLDER = os.path.join(settings.MEDIA_ROOT, "processed_dxf/")

def generate_and_open_dxf(json_file):
    """Generates DXF file from JSON and opens it in LibreCAD."""
    if not json_file or not os.path.exists(json_file):
        return {"error": "JSON file not found"}

    # Define DXF output path
    file_name = os.path.basename(json_file).replace(".json", ".dxf")
    dxf_file = os.path.join(DXF_FOLDER, file_name)

    # Convert JSON to DXF
    json_to_dxf(json_file, dxf_file)

    # Open DXF in LibreCAD
    try:
        subprocess.run(["C:\\Program Files (x86)\\LibreCAD\\LibreCAD.exe", dxf_file], shell=True)
        return {"message": f"Opening {file_name} in LibreCAD..."}
    except Exception as e:
        return {"error": str(e)}