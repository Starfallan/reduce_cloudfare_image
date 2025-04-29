# R2 Image Compression Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[中文文档](README_CN.md)

A tool for downloading, compressing, and re-uploading images in Cloudflare R2 buckets, supporting various image formats and custom paths.

## Features

- Download images from R2 storage
- Support for multiple image formats (PNG, JPEG, WebP, GIF)
- Apply optimal compression strategies based on image format
- Resize large images while maintaining aspect ratio
- Format-specific optimization:
  - PNG: Color optimization and quantization
  - JPEG: Quality adjustment
  - WebP: Compression quality optimization
  - GIF: Convert to more efficient formats when appropriate
- Upload compressed images back to R2, replacing the original
- Process multiple images in parallel
- Custom directory prefix and file matching patterns
- Test mode to preview which files will be processed
- Display file list and request user confirmation before processing
- Generate detailed compression report after processing

## Installation

### Prerequisites

- Python 3.6 or higher
- Cloudflare R2 account with bucket and access credentials

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/r2-image-compression-tool.git
   cd r2-image-compression-tool
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   
   **Option 1: Use environment file**
   
   Copy the example environment file and edit it:
   ```bash
   cp env.example .env
   # Edit .env with your credentials
   ```
   
   **Option 2: Use setup script**
   
   Copy the example setup script and edit it:
   ```bash
   cp set_env.sh.example set_env.sh
   # Edit set_env.sh with your credentials
   chmod +x set_env.sh
   source set_env.sh
   ```

## Usage

```bash
python compress_r2_images.py [options]
```

### Command Line Options

- `--prefix PATH`: Directory prefix in R2 bucket to process (default: "uiprompt/themes/")
- `--pattern REGEX`: Custom regex pattern for matching files (default: matches [prefix]/*/any supported image format)
- `--workers NUMBER`: Number of worker threads for parallel processing (default: 5)
- `--max-width PIXELS`: Maximum width in pixels for resizing (default: 1200)
- `--max-size SIZE_MB`: Target maximum file size in MB (default: 1.0)
- `--compression-level LEVEL`: PNG compression level (0-9, default: 9)
- `--jpeg-quality QUALITY`: JPEG compression quality (0-100, default: 85)
- `--webp-quality QUALITY`: WebP compression quality (0-100, default: 85)
- `--test`: Test mode - only list files that would be processed without actually processing them

### Examples

```bash
# Process all PNG files in the themes directory
python compress_r2_images.py --prefix "themes/" --pattern ".*\.png$"

# Test mode, only show files that would be processed
python compress_r2_images.py --test --prefix "themes/"

# Process all images in a specific theme directory
python compress_r2_images.py --prefix "themes/steampunk-game-community/" --pattern ".*\.png$"
```

### Output Example

```
Files to be processed:
+--------------------------------------------------------------+------+----------+----------+
| File Path                                                     | Format| Size(KB) | Size(MB) |
+==============================================================+======+==========+==========+
| themes/steampunk-game-community/steampunk-game-community.png | PNG  | 664.5 KB | 0.65 MB  |
+--------------------------------------------------------------+------+----------+----------+
| Total                                                        | 1 file| 664.5 KB | 0.65 MB  |
+--------------------------------------------------------------+------+----------+----------+

Processing 1 file, total size 0.65 MB. Continue? (y/n): y

Processing images: 100%|████████████████████████████████████| 1/1 [00:06<00:00,  6.36s/it]

Image Compression Report:
+--------------------------------------------------------------+----------+----------+----------+-------+--------+
| File                                                          | Original | Compressed| Space    | Ratio | Time   |
|                                                              | Size     | Size      | Saved    |       |        |
+==============================================================+==========+==========+==========+=======+========+
| themes/steampunk-game-community/steampunk-game-community.png | 664.5 KB | 529.1 KB | 135.3 KB | 20.4% | 2.7s   |
+--------------------------------------------------------------+----------+----------+----------+-------+--------+
| Total                                                         | 664.5 KB | 529.1 KB | 135.3 KB | 20.4% | -      |
+--------------------------------------------------------------+----------+----------+----------+-------+--------+
| Total(MB)                                                     | 0.65 MB  | 0.52 MB  | 0.13 MB  | 20.4% | -      |
+--------------------------------------------------------------+----------+----------+----------+-------+--------+

Processed 1 file
Total space saved: 0.13 MB
Average compression ratio: 20.4%
```

## Supported Image Formats

The script supports the following image formats:

- **PNG (.png)**: Preserves transparency, uses optimization and color quantization
- **JPEG (.jpg, .jpeg)**: Adjusts quality level
- **WebP (.webp)**: Supports transparency, adjusts quality level
- **GIF (.gif)**: Supports transparency, considers converting non-animated GIFs to more efficient formats

## How It Works

1. List all image files matching the pattern under the specified prefix in the R2 bucket
2. Display file list and request user confirmation
3. Download each image
4. Resize the image if its width exceeds the maximum width
5. Apply the best compression strategy based on image format:
   - PNG: Optimize settings and color quantization
   - JPEG: Adjust quality level
   - WebP: Optimize compression quality
   - GIF: Optimize or convert to more efficient format
6. Upload the compressed image back to R2 using the same key (overwriting the original image)
7. Only upload when at least 5% size reduction is achieved
8. Generate detailed compression report

## Notes

- The script preserves transparency in PNG and WebP formats
- For JPEG, non-transparent layers will be converted to RGB mode
- Execution time depends on the number of images, sizes, and network speed
- Processing progress is displayed via progress bar and log messages
- Test mode helps you preview the files that will be processed before actual processing
- Some already optimized images may not be further compressed

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 