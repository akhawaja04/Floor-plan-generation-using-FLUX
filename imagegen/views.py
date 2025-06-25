import os
import json
import shutil
from PIL import Image
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from gradio_client import Client  # Correct
import cv2
import numpy as np
from rembg import remove
from django.urls import path
from PIL import Image
import uuid
from .utils import process_floor_plan, visualize_floor_plan, WALL_COLOR_MAP, AREA_COLOR_MAP, get_area_color, json_to_dxf, generate_and_open_dxf
import platform
import subprocess
from django.conf import settings
from django.contrib.auth.decorators import login_required


def home(request):
    return render(request, "imagegen/test.html")

#@login_required
def about(request):
    return render(request, 'imagegen/about.html')
def gallery(request):
    floorplans = [
    {
        "img": "imagegen/gallery/gallery_img1.png",
        "title": "Modern Minimalist Home",
        "desc": "balcony 24 sqft ratio 14:3 green, 1 common room 150 sqft ratio 7:8 orange, master room 150 sqft ratio 13:15 yellow, bathroom 50 sqft ratio 10:9 blue, 2 common room 50 sqft ratio 5:4 orange, kitchen 50 sqft ratio 9:7 coral red, living room 500 sqft ratio 1:1 light yellow."
    },
    {
        "img": 'imagegen/gallery/gallery_img2.png',
        "title": "Cozy Urban Apartment",
        "desc": "common room 100 sqft ratio 11:9 orange, living room 450 sqft ratio 12:5 light yellow, balcony 50 sqft ratio 3:10 green, master room 250 sqft ratio 7:4 yellow, kitchen 50 sqft ratio 8:11 coral red, bathroom 50 sqft ratio 16:15 blue, dining room 100 sqft ratio 16:11."
    },
    {
        "img": "imagegen/gallery/gallery_img7.png",
        "title": "Eco-Friendly Cabin",
        "desc": "common room 100 sqft ratio 11:9 orange, living room 450 sqft ratio 12:5 light yellow, balcony 50 sqft ratio 3:10 green, master room 250 sqft ratio 7:4 yellow, kitchen 50 sqft ratio 8:11 coral red, bathroom 50 sqft ratio 16:15 blue, dining room 100 sqft ratio 16:11"
    },
    {
        "img": "imagegen/gallery/gallery_img4.png",
        "title": "The Grand Urban Palette",
        "desc": "master room 250 sqft ratio 7:11 yellow, 1 bathroom 50 sqft ratio 7:11 blue, 2 bathroom 50 sqft ratio 3:5 blue, 1 common room 100 sqft ratio 13:11 orange, 2 common room 200 sqft ratio 3:4 orange, living room 800 sqft ratio 13:15 light yellow, kitchen 100 sqft ratio 3:2 coral red."
    },

    {
        "img": "imagegen/gallery/gallery_img3.png",
        "title": "Spacious Family House",
        "desc": "master room 250 sqft ratio 13:7 yellow, living room 850 sqft ratio 5:6 light yellow, bathroom 50 sqft ratio 11:16 blue, 1 common room 150 sqft ratio 16:13 orange, balcony 50 sqft ratio 7:15 green, 2 common room 150 sqft ratio 15:16 orange, 3 common room 100 sqft ratio 11:13 orange, kitchen 100 sqft ratio 10:9 coral red."
    },
    {
        "img": "imagegen/gallery/gallery_img6.png",
        "title": "Seven Spaces",
        "desc": "1 common room 150 sqft ratio 3:4 orange, 2 common room 150 sqft ratio 7:11 orange, 1 bathroom 50 sqft ratio 13:15 blue, 2 bathroom 50 sqft ratio 14:13 blue, master room 150 sqft ratio 7:10 yellow, balcony 50 sqft ratio 8:3 green, kitchen 200 sqft ratio 6:7 coral red, living room 800 sqft ratio 10:13 light yellow."
    },
]
    return render(request, 'imagegen/gallery.html', {"floorplans": floorplans})

            
GRADIO_API_URL = "https://df7b3f0f00a71bb20b.gradio.live"

# Initialize Gradio Client
client = Client(GRADIO_API_URL)

# Folder to store processed images
UPLOAD_FOLDER: str = os.path.join(settings.MEDIA_ROOT, 'images/')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists

# Define color mapping for different room types
ROOM_COLORS = {
    "kitchen": "coral red",
    "living_room": "light yellow",
    "common_room": "orange",
    "balcony": "green", 
    "master_room": "yellow",
    "bathroom": "blue",
    "storage": "pink",
    
}

def process_image(image_path, prompt, index):
    try:
        if os.path.exists(image_path):
            safe_prompt = "".join(c if c.isalnum() else "_" for c in prompt)[:20]
            webp_filename = f"{safe_prompt}_{index}+{uuid.uuid4().hex}.webp"
            png_filename = f"{safe_prompt}_{index}+{uuid.uuid4().hex}.png"

            target_webp_path = os.path.join(UPLOAD_FOLDER, webp_filename)
            target_png_path = os.path.join(UPLOAD_FOLDER, png_filename)

            shutil.copy(image_path, target_webp_path)

            #Open and resize image before saving
            with Image.open(target_webp_path) as img:
                #img = img.resize((1024, 1024), Image.Resampling.LANCZOS)  # Resize to 1024x1024
                img.save(target_png_path, "PNG")

            print(f"Image successfully saved as PNG (1024x1024): {target_png_path}")

            return f"{settings.MEDIA_URL}images/{png_filename}"
        else:
            print(f"File not found: {image_path}")
            return None
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

        
def get_image_urls(prompt):
    try:
        # Sending request to Gradio API
        result = client.predict(prompt, api_name="/predict")
        print(f"API Response: {result}")
        
        # Process all images
        processed_images = []
        if isinstance(result, list):
            for index, item in enumerate(result):
                if isinstance(item, dict) and 'image' in item:
                    processed_url = process_image(item['image'], prompt, index)
                    if processed_url:
                        processed_images.append(processed_url)
            
            return processed_images  # Return list of image URLs
        else:
            print("Unexpected API response format")
            return []
    except Exception as e:
        print(f"Error getting image from API: {e}")
        return []
@login_required
# Main view for the application
def main(request):
    return render(request, 'imagegen/main.html')

# Django view to serve images
def serve_image(request, filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return JsonResponse({"image_url": f"{settings.MEDIA_URL}images/{filename}"})
    return JsonResponse({"error": "File not found"}, status=404)
@csrf_exempt
def generate_prompt(request):
    if request.method == "POST":
        form_data = request.POST
        room_prompt_parts = []
        
        # Organize data by full room keys
        room_data = {}
        
        # First, extract room data from form
        for key, value in form_data.items():
            if key.endswith('_area'):
                room_key = key[:-5]  # Remove '_area' suffix
                room_data.setdefault(room_key, {})['area'] = value
            elif key.endswith('_ratio'):
                room_key = key[:-6]  # Remove '_ratio' suffix
                room_data.setdefault(room_key, {})['ratio'] = value
        
        # Group rooms by base name for counting
        base_rooms = {}
        for room_key in room_data.keys():
            # For keys like "kitchen" or "kitchen_1", get the base name ("kitchen")
            parts = room_key.split('_')
            if len(parts) > 1 and parts[-1].isdigit():
                # This is a numbered room like "kitchen_1"
                base_name = '_'.join(parts[:-1])
            else:
                # This is a base room like "kitchen"
                base_name = room_key
                
            base_rooms.setdefault(base_name, []).append(room_key)
        
        # Process rooms in order, numbering duplicates
        for base_name, room_keys in base_rooms.items():
            # Sort room keys to ensure consistent order (base room first, then numbered)
            room_keys.sort(key=lambda k: 0 if k == base_name else int(k.split('_')[-1]))
            
            for i, room_key in enumerate(room_keys):
                data = room_data[room_key]
                
                # Skip if missing essential data
                if 'area' not in data or 'ratio' not in data or not data['area'] or not data['ratio']:
                    continue
                
                # Get display name (convert underscores to spaces)
                display_name = base_name.replace('_', ' ')
                
                # Add number prefix if it's a duplicate (i > 0)
                if i > 0:
                    display_name = f"{i+1} {display_name}"
                
                # Get color (default to white)
                color = ROOM_COLORS.get(base_name.lower(), "white")
                
                # Add to prompt parts
                room_prompt_parts.append(f"{display_name} {data['area']} sqft ratio {data['ratio']} {color}")
        
        # Join all parts with commas
        prompt = ", ".join(room_prompt_parts)
        
        if not prompt:
            return JsonResponse({
                'success': False,
                'error': 'No valid room data provided'
            })
        
        # Send to Gradio API
        image_urls = get_image_urls(prompt)
        if image_urls:
            return JsonResponse({
                'success': True,
                'prompt': prompt,
                'image_urls': image_urls
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to generate image'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})# @csrf_exempt

@csrf_exempt
def download_image(request, format):
    """Handle the download of processed floor plan in various formats."""
    if request.method == "GET":
        image_url = request.GET.get('image_url')
        if not image_url:
            return JsonResponse({'error': 'No image URL provided'}, status=400)

        # Construct full file path
        file_path = os.path.join(settings.MEDIA_ROOT, 'images', image_url)
        if not os.path.exists(file_path):
            return JsonResponse({'error': 'File not found'}, status=404)

        # Process the floor plan to generate JSON data
        try:
            json_output_path = process_floor_plan(file_path, WALL_COLOR_MAP, AREA_COLOR_MAP, format)
        except Exception as e:
            return JsonResponse({'error': f'Error processing floor plan: {str(e)}'}, status=500)

        filename_base = os.path.splitext(os.path.basename(file_path))[0]
        
        # Create necessary directories
        PROCESSED_PNG_PATH = os.path.join(settings.MEDIA_ROOT, 'processed_png')
        PROCESSED_DXF_PATH = os.path.join(settings.MEDIA_ROOT, 'processed_dxf')
        os.makedirs(PROCESSED_PNG_PATH, exist_ok=True)
        os.makedirs(PROCESSED_DXF_PATH, exist_ok=True)

        if format.lower() == 'png':
            # Generate PNG visualization
            processed_png_filename = f"{filename_base}_processed.png"
            processed_png_path = os.path.join(PROCESSED_PNG_PATH, processed_png_filename)
            
            # Load JSON data
            try:
                with open(json_output_path, 'r') as f:
                    data = json.load(f)
                
                # Visualize floor plan
                visualize_floor_plan(data, processed_png_path)
                
                # Return the processed image
                with open(processed_png_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='image/png')
                    response['Content-Disposition'] = f'attachment; filename="{processed_png_filename}"'
                    return response
            except Exception as e:
                return JsonResponse({'error': f'Error generating PNG: {str(e)}'}, status=500)

        elif format.lower() == 'dxf':
            
            # You would need to import your json_to_dxf function here
            dxf_filename = f"{filename_base}_processed.dxf"
            dxf_path = os.path.join(PROCESSED_DXF_PATH, dxf_filename)
            
            try:
                # Call your json_to_dxf function
                json_to_dxf(json_output_path, dxf_path)
                
                
                with open(dxf_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='application/dxf')
                    response['Content-Disposition'] = f'attachment; filename="{dxf_filename}"'
                    return response
                
            except Exception as e:
                return JsonResponse({'error': f'Error generating DXF: {str(e)}'}, status=500)

        elif format.lower() == 'redirect':
            try:
                filename_base = os.path.splitext(os.path.basename(file_path))[0]
                dxf_filename = f"{filename_base}_processed.dxf"
                dxf_path = os.path.join(settings.MEDIA_ROOT, 'processed_dxf', dxf_filename)
                json_output_path = process_floor_plan(file_path, WALL_COLOR_MAP, AREA_COLOR_MAP, format)
                json_to_dxf(json_output_path, dxf_path)

                if not os.path.exists(dxf_path):
                    return JsonResponse({'error': 'DXF file not created'}, status=500)

                # Automatically open LibreCAD via subprocess
                if platform.system() == "Windows":
                    subprocess.Popen(["C:\Program Files (x86)\LibreCAD\LibreCAD.exe", dxf_path], shell=True)
                else:
                    subprocess.Popen(["librecad", dxf_path])

                return JsonResponse({'message': 'Opening DXF in LibreCAD...', 'dxf_path': dxf_path}, status=200)

            except Exception as e:
                return JsonResponse({'error': f'Error opening DXF: {str(e)}'}, status=500)
            
    return JsonResponse({'error': 'Invalid request method'}, status=400)
