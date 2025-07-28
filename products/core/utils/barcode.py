import barcode
from barcode.writer import ImageWriter
from PIL import Image
import io
import base64
from colorama import Fore, Style, init
from pyzbar.pyzbar import decode

# Initialize colorama
init(autoreset=True)

class Barcode:
    """
    Barcode is a utility class for generating and scanning barcodes with optional embedding of a logo.
    It supports saving the barcode either as an image file or as a base64-encoded string in a text file.

    Usage:
        barcode = Barcode()
        
        # Generate barcode and save as PNG
        barcode.generate_barcode(
            filename="barcode.png", 
            logo_path="logo.png", 
            data="123456789012", 
            save_as_png=True
        )
        
        # Generate barcode and save as base64 string in a text file
        barcode.generate_barcode(
            filename="barcode.png", 
            logo_path="logo.png", 
            data="123456789012", 
            save_as_png=False
        )
        
        # Scan barcode from an image
        result = barcode.scan_barcode("barcode.png")
        print(result)
    """

    def generate_barcode(self, filename=None, logo_path=None, data=None, save_as_png=True):
        if data is None:
            data = ''
        if filename is None:
            filename = "barcode.png"
        
        # Check if logo_path is provided and is a PNG file
        if logo_path and not logo_path.endswith('.png'):
            raise ValueError(Fore.RED + Style.BRIGHT + 'logo_path must end with .png!')

        # Generate the barcode
        code128 = barcode.get_barcode_class('code128')
        barcode_instance = code128(data, writer=ImageWriter())

        # Create an image from the barcode
        buffered = io.BytesIO()
        barcode_instance.write(buffered, options={'module_width': 0.5, 'module_height': 15, 'quiet_zone': 1})  # Adjust for rectangular
        buffered.seek(0)
        img = Image.open(buffered)

        if logo_path:
            # Load the logo image
            logo = Image.open(logo_path)

            # Ensure the logo has a white background (in case of transparency)
            logo = logo.convert("RGBA")
            white_background = Image.new("RGBA", logo.size, "WHITE")
            logo = Image.alpha_composite(white_background, logo).convert("RGBA")

            # Calculate the logo size relative to the barcode
            logo_size = int(img.size[1] / 6)  # Adjust size relative to height

            # Resize the logo
            logo = logo.resize((logo_size, logo_size))

            # Calculate the position to place the logo at the bottom-right corner
            logo_position = (
                img.size[0] - logo_size - 10,  # 10 pixels padding from the right edge
                img.size[1] - logo_size - 10   # 10 pixels padding from the bottom edge
            )

            # Paste the logo image onto the barcode, with a mask to handle transparency
            img.paste(logo, logo_position, mask=logo)

        if save_as_png:
            # Save the final barcode image
            img.save(filename)
            print(f'Barcode has been saved as {filename}')
            return None
        else:
            # Convert the image to a byte stream
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")

            # Encode the byte stream to base64
            image_string = base64.b64encode(buffered.getvalue()).decode("utf-8")

            return image_string

    def scan_barcode(self, filename):
        # Open the image file
        img = Image.open(filename)

        # Decode the barcode from the image
        decoded_objects = decode(img)

        # Check if any barcode was found
        if not decoded_objects:
            raise ValueError(Fore.RED + Style.BRIGHT + "No barcode found in the image.")

        # Return the decoded data from the first barcode found
        return decoded_objects[0].data.decode('utf-8')