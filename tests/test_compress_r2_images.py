import unittest
import os
import sys
from io import BytesIO
from unittest.mock import patch, MagicMock
from PIL import Image

# Add the parent directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the functions to test
from compress_r2_images import (
    get_image_format, 
    compress_image,
    process_image
)


class TestImageFormatDetection(unittest.TestCase):
    """Test the image format detection function."""
    
    def test_png_format(self):
        """Test PNG format detection."""
        format_name, content_type = get_image_format("test/image.png")
        self.assertEqual(format_name, "PNG")
        self.assertEqual(content_type, "image/png")
    
    def test_jpeg_format(self):
        """Test JPEG format detection."""
        format_name, content_type = get_image_format("test/image.jpg")
        self.assertEqual(format_name, "JPEG")
        self.assertEqual(content_type, "image/jpeg")
        
        format_name, content_type = get_image_format("test/image.jpeg")
        self.assertEqual(format_name, "JPEG")
        self.assertEqual(content_type, "image/jpeg")
    
    def test_webp_format(self):
        """Test WebP format detection."""
        format_name, content_type = get_image_format("test/image.webp")
        self.assertEqual(format_name, "WEBP")
        self.assertEqual(content_type, "image/webp")
    
    def test_gif_format(self):
        """Test GIF format detection."""
        format_name, content_type = get_image_format("test/image.gif")
        self.assertEqual(format_name, "GIF")
        self.assertEqual(content_type, "image/gif")
    
    def test_unknown_format(self):
        """Test unknown format detection."""
        format_name, content_type = get_image_format("test/image.unknown")
        self.assertEqual(format_name, "PNG")  # Default to PNG
        self.assertEqual(content_type, "image/png")


class TestImageCompression(unittest.TestCase):
    """Test the image compression function."""
    
    def create_test_image(self, format_name, width=200, height=100):
        """Create a test image for testing."""
        img = Image.new('RGB', (width, height), color=(73, 109, 137))
        img_io = BytesIO()
        img.save(img_io, format=format_name)
        img_io.seek(0)
        return img_io
    
    @patch('compress_r2_images.MAX_WIDTH', 100)
    @patch('compress_r2_images.PNG_COMPRESSION_LEVEL', 9)
    def test_png_compression(self):
        """Test PNG image compression."""
        # Create a test PNG image
        test_img = self.create_test_image('PNG', width=200, height=100)
        original_size = test_img.getbuffer().nbytes
        
        # Compress the image
        compressed_data, content_type = compress_image(test_img, "test.png")
        
        # Verify the compressed image
        self.assertIsNotNone(compressed_data)
        self.assertEqual(content_type, "image/png")
        
        # Check if the image was actually compressed
        self.assertLess(compressed_data.getbuffer().nbytes, original_size)
        
        # Verify the image dimensions were changed
        img = Image.open(compressed_data)
        self.assertEqual(img.width, 100)  # Should be resized to MAX_WIDTH


if __name__ == "__main__":
    unittest.main() 