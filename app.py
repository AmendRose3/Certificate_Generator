from flask import Flask, request, send_file, render_template, redirect, url_for
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import zipfile

app = Flask(__name__)

# Configure paths
TEMPLATE_PATH = "certificate_template.png"
FONT_PATH = "arial.ttf"  # Path to a .ttf font file
OUTPUT_FOLDER = "certificates"

# Ensure output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def upload_form():
    return render_template("index.html")

@app.route('/generate', methods=['POST'])
def generate_certificates():
    # Check if a file is uploaded
    if 'file' not in request.files:
        return "No file uploaded", 400

    file = request.files['file']

    # Load CSV data
    try:
        data = pd.read_csv(file)
    except Exception as e:
        return f"Error reading CSV file: {str(e)}", 400

    # Check that all necessary columns exist
    required_columns = {'Name', 'College Name', 'Event', 'Rank'}
    if not required_columns.issubset(data.columns):
        return "CSV missing one or more required columns", 400

    # Generate certificates
    for _, row in data.iterrows():
        generate_certificate(row)

    # Create a ZIP file containing all generated certificates
    zip_path = os.path.join(OUTPUT_FOLDER, "certificates.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(OUTPUT_FOLDER):
            for file in files:
                if file.endswith(".pdf"):
                    zipf.write(os.path.join(root, file), file)

    return redirect(url_for('upload_form', download_link=url_for('download_zip')))

def generate_certificate(row):
    # Load the certificate template
    template = Image.open(TEMPLATE_PATH)
    draw = ImageDraw.Draw(template)

    # Load fonts with different sizes
    font_name = ImageFont.truetype(FONT_PATH, 50)    # Font size for name
    font_college = ImageFont.truetype(FONT_PATH, 25) # Font size for college
    font_event = ImageFont.truetype(FONT_PATH, 30)   # Font size for event

    # Get template dimensions
    width, height = template.size

    # Calculate center positions
    text_positions = {
        'Name': (width / 2, height / 2 - 50),        # Centered, slightly above middle
        'College Name': (width / 2, height / 2 + 50), # Centered, above event
        'Event': (width / 2, height / 2 + 80),      # Centered, below college
    }

    # Function to center text with color fill directly in the function
    def draw_centered_text(text, position, font, color="black"):
        text_width = draw.textlength(text, font=font)
        x = position[0] - text_width / 2  # Center text horizontally
        draw.text((x, position[1]), text, font=font, fill=color)

    # Draw text elements
    draw_centered_text(row['Name'], text_positions['Name'], font_name)
    draw_centered_text(f"from the {row['College Name']}", text_positions['College Name'], font_college)

    # Create event text based on rank
    if row['Rank'] != 'Participant':
        event_text = f"has successfully secured {row['Rank']} rank in the {row['Event']}"
    else:
        event_text = f"has successfully participated in the {row['Event']}"
    
    draw_centered_text(event_text, text_positions['Event'], font_event)

    # Save certificate
    output_path = os.path.join(OUTPUT_FOLDER, f"{row['Name']}_certificate.pdf")
    template.save(output_path, "PDF")

@app.route('/download_zip')
def download_zip():
    zip_path = os.path.join(OUTPUT_FOLDER, "certificates.zip")
    return send_file(zip_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
