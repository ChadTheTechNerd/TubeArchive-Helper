# TubeArchivist Metadata Embedder

## Description
The TubeArchivist Metadata Embedder automates the process of copying video files from a specified source directory to a target directory, renaming the file to it's correct title, 
embedding metadata directly into the video files, and downloading associated thumbnails. As well as creating metadata.nfo files for each video. I wrote this script to be the go-between
from TubeArchivist to Jellyfin.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Installation
1. **Clone the repository**:
   ```sh
   git clone https://github.com/your_username/your_repository.git
   cd your_repository
   ```
2. **Create and activate a virtual environment**:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
3. **Install dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

## Usage
1. **Set up the environment variables** by creating a `.env` file in the root directory with the following content:
   ```env
   TA_MEDIA_FOLDER=/path/to/your/media/folder
   TARGET_FOLDER=/path/to/your/target/folder
   TA_API_VIDEO_URL=https://your_tubearchivist_url/api/video
   TA_API_URL=https://your_tubearchivist_url/api
   TA_API_USERNAME=your_username
   TA_API_PASSWORD=your_password
   THUMB_BASE_URL=https://your_tubearchivist_url
   ```
2. **Run the script**:
   ```sh
   python tubearchivist_script.py
   ```

## Configuration
Logs are saved to `tubearchivist_2.log`.

FFmpeg is required for the script as well, and can be installed following these directions for Linux:
   
   Update your package list and install FFmpeg using your package manager:
   
      For Debian-based distributions (e.g., Ubuntu):
         sudo apt update
         sudo apt install ffmpeg
      For Red Hat-based distributions (e.g., Fedora):
         sudo dnf install ffmpeg
      For Arch-based distributions:
         sudo pacman -S ffmpeg
   
   Ensure FFmpeg is installed and accessible from the command line.
   
      ffmpeg -version
      
## Contributing
Contributions are welcome! Please read the [CONTRIBUTING](CONTRIBUTING.md) guidelines before submitting a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For any inquiries or feedback, you can reach out to the project maintainer(s) at chadthetechnerd@gmail.com.

