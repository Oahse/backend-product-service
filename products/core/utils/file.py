from PIL import Image
import mimetypes
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.exceptions import DefaultCredentialsError,GoogleAuthError
import google.auth
from google_auth_oauthlib.flow import InstalledAppFlow
import googleapiclient.errors

class ImageFile:
    @staticmethod
    def reduce_image_quality(input_image_path, output_image_path, quality=30,target_format = 'webp'):
        """
        Reduces the image quality and saves the new image.

        Args:
        - input_image_path (str): The path to the input image.
        - output_image_path (str): The path to save the reduced quality image.
        - quality (int): The quality of the saved image (0 to 100, default is 50).
        - target_format (str): Desired output format ('jpeg', 'png', 'webp').

        # Example usage:
        ImageFile.reduce_image_quality('input_image.jpg', 'output_image.jpg', quality=30)  # Adjust quality from 0 to 100
        """
        # Open the image
        img = Image.open(input_image_path)
        
        # Check if the image format is JPEG or other supported formats for quality reduction
        if target_format == 'jpeg':
            img.convert("RGB").save(output_image_path, format='JPEG', quality=quality)
        elif target_format == 'webp':
            # WebP is the most efficient for web images
            img.convert("RGB").save(output_image_path, format='WebP', quality=quality, method=6)
        elif target_format == 'png':
            # PNG doesn't support quality, but we can still optimize the file
            img.save(output_image_path, format='PNG', optimize=True)
        else:
            raise ValueError("Unsupported format: Please choose 'jpeg', 'webp', or 'png'.")
        
        
        print(f"Image saved with reduced quality at: {output_image_path}")

class GoogleDrive:
    def __init__(self, jsonkey='path/to/your/json/key.json'):
        if not jsonkey:
            raise ValueError("The JSON key file path must be provided.")
        self.key = jsonkey
        self.mimetype = 'application/octet-stream'  # Default MIME type for unknown files

    def get_drive_service(self):
        """Return authenticated Google Drive service."""
        try:
            # Try to load the credentials from the provided JSON key file
            creds = service_account.Credentials.from_service_account_file(
                self.key,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            # Build the Drive API service
            drive_service = build('drive', 'v3', credentials=creds)
            return drive_service
        
        except FileNotFoundError:
            raise ValueError(f"The provided JSON key file '{self.key}' was not found.")
        
        except DefaultCredentialsError:
            raise ValueError("The credentials provided are invalid or the key file is missing or incorrect.")
        
        except GoogleAuthError as e:
            raise ValueError(f"Authentication failed with the error: {str(e)}")
        
        except Exception as e:
            raise Exception(f"An error occurred while creating the Google Drive service: {str(e)}")
    

    def get_mimetype(self, filepath):
        """Returns the appropriate MIME type based on the file extension."""
        if not filepath:
            raise ValueError("The file path must be provided.")
        
        # Check if file exists at the provided filepath
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"The file at {filepath} does not exist.")
        
        # Use mimetypes to guess the file's MIME type
        mime_type, encoding = mimetypes.guess_type(filepath)
        
        if mime_type:
            return mime_type
        else:
            # If MIME type can't be guessed, assume a generic binary file
            return 'application/octet-stream'

    def create_folder(self, folder_name, parent_folder_id=None):
        """Creates a folder in Google Drive."""
        if not folder_name:
            raise ValueError("The folder name must be provided.")
        drive_service = self.get_drive_service()

        # Set up folder metadata
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id] if parent_folder_id else []
        }

        try:
            # Create the folder on Google Drive
            folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
            return {'id': folder['id']}
        except Exception as e:
            raise Exception(f"An error occurred while creating the folder: {str(e)}")

    def get_folder_contents(self, folder_id):
        """List all files in a specific folder using its folder ID."""
        if not folder_id:
            raise ValueError("The folder id must be provided.")
        drive_service = self.get_drive_service()

        try:
            # List all files in the folder
            results = drive_service.files().list(
                q=f"'{folder_id}' in parents",
                fields="files(id, name, mimeType)"
            ).execute()
            files = results.get('files', [])

            return files
        except Exception as e:
            raise Exception(f"An error occurred while fetching the folder contents: {str(e)}")

    def delete_folder(self, folder_id):
        """Delete a folder from Google Drive using its folder ID."""
        if not folder_id:
            raise ValueError("The folder id must be provided.")
        drive_service = self.get_drive_service()

        try:
            # First, delete all files in the folder
            files = self.get_folder_contents(folder_id)
            if files:
                for file in files:
                    # Delete each file in the folder
                    drive_service.files().delete(fileId=file['id']).execute()

            # Now, delete the folder itself
            drive_service.files().delete(fileId=folder_id).execute()
            print(f"Folder with ID {folder_id} has been successfully deleted.")
        except Exception as e:
            raise Exception(f"An error occurred while deleting the folder: {str(e)}")
    
    def upload_file(self, filepath='path/to/your/local/file.txt', folder_id=None):
        """Uploads a file to Google Drive with proper MIME type handling."""
        if not filepath:
            raise ValueError("The file path must be provided.")
        self.mimetype = self.get_mimetype(filepath)

        drive_service = self.get_drive_service()

        # Set file metadata
        file_metadata = {
            'name': os.path.basename(filepath),  # Use the filename from the local path
            'parents': [folder_id] if folder_id else []  # Use the provided folder ID (or leave it empty)
        }

        media = MediaFileUpload(filepath, mimetype=self.mimetype)

        try:
            # Create the file on Google Drive
            file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            file_id = file['id']
            file_info = drive_service.files().get(fileId=file_id, fields='webViewLink, webContentLink').execute()

            # Return the file ID and the shareable link or viewable link
            return {'id': file['id'], 'link': file_info.get('webViewLink', 'No link available')}
        except Exception as e:
            raise Exception(f"An error occurred while uploading the file: {str(e)}")

    def download_file(self, file_id, destination_path='path/to/your/destination/file.txt'):
        """Downloads a file from Google Drive using the file ID."""
        if not file_id:
            raise ValueError("The file id must be provided.")
        if not destination_path:
            raise ValueError("The destination path must be provided.")
        drive_service = self.get_drive_service()

        try:
            # Request file metadata
            file = drive_service.files().get(fileId=file_id).execute()
            file_name = file['name']
            file_path = os.path.join(destination_path, file_name)

            # Set up the download process
            request = drive_service.files().get_media(fileId=file_id)
            fh = open(file_path, 'wb')

            # Use MediaIoBaseDownload to download the file
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}%.")
            
            # Close the file after download
            fh.close()
            print(f"File {file_name} downloaded successfully to {file_path}.")
            return file_path
        except Exception as e:
            raise Exception(f"An error occurred while downloading the file: {str(e)}")

    def get_file_link(self, file_id):
        """Fetch the Google Drive link of a file using its file ID."""
        if not file_id:
            raise ValueError("The file id must be provided.")
        drive_service = self.get_drive_service()

        try:
            # Fetch the file metadata using fileId
            file = drive_service.files().get(fileId=file_id).execute()

            # Return the Google Drive URL
            return f"https://drive.google.com/file/d/{file_id}/view"
        except Exception as e:
            raise Exception(f"An error occurred while fetching the file link: {str(e)}")

    def delete_file(self, file_id):
        """Delete a file from Google Drive using its file ID."""
        if not file_id:
            raise ValueError("The file id must be provided.")
        drive_service = self.get_drive_service()

        try:
            # Delete the file using its file ID
            drive_service.files().delete(fileId=file_id).execute()
            print(f"File with ID {file_id} has been successfully deleted.")
        except Exception as e:
            raise Exception(f"An error occurred while deleting the file: {str(e)}")

class YouTubeAPI:
    def __init__(self, credentials_json='path/to/your/credentials.json'):
        if not credentials_json:
            raise ValueError("The JSON key credentials.json must be provided.")
        self.credentials_json = credentials_json
        self.youtube_service = self.authenticate()

    def authenticate(self):
        """Authenticate and create the YouTube API service."""
        SCOPES = ['https://www.googleapis.com/auth/youtube.upload',
                  'https://www.googleapis.com/auth/youtube.force-ssl']
        
        try:
            # Check if the credentials JSON file exists
            if not os.path.exists(self.credentials_json):
                raise FileNotFoundError(f"Credentials file '{self.credentials_json}' not found.")

            # Authenticate using OAuth 2.0
            flow = InstalledAppFlow.from_client_secrets_file(self.credentials_json, SCOPES)
            creds = flow.run_local_server(port=0)
            youtube = build('youtube', 'v3', credentials=creds)
            return youtube
        
        except FileNotFoundError as e:
            # Raise an exception if the credentials file is not found
            raise Exception(f"Authentication failed: {str(e)}")
        
        except google.auth.exceptions.DefaultCredentialsError as e:
            # Raise an exception if there are no valid credentials
            raise Exception(f"Authentication failed: Could not find valid credentials. {str(e)}")
        
        except google.auth.exceptions.RefreshError as e:
            # Raise an exception if credentials refresh failed
            raise Exception(f"Authentication failed: Failed to refresh credentials. {str(e)}")
        
        except Exception as e:
            # Raise any other unexpected exception that occurred during authentication
            raise Exception(f"An unexpected error occurred during authentication: {str(e)}")

    def upload_video(self, file_path, title, description, category_id=22, tags=None):
        """Uploads a video to YouTube."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The video file at '{file_path}' does not exist.")
        
        try:
            # Set the video metadata
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags or [],
                    'categoryId': category_id,
                },
                'status': {
                    'privacyStatus': 'private',  # 'private', 'public', 'unlisted'
                }
            }

            # Upload the video
            media = MediaFileUpload(file_path, mimetype='video/*', resumable=True)
            request = self.youtube_service.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )

            # Execute the upload request
            response = request.execute()
            video_id = response['id']
            print(f"Video uploaded successfully. Video ID: {video_id}")
            return video_id

        except googleapiclient.errors.HttpError as e:
            print(f"An error occurred: {e}")
            return None

    def get_video_details(self, video_id):
        """Fetches details of a video by its ID."""
        try:
            request = self.youtube_service.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_id
            )
            response = request.execute()
            if response['items']:
                video = response['items'][0]
                return video
            else:
                print(f"No video found with ID: {video_id}")
                return None
        except googleapiclient.errors.HttpError as e:
            print(f"An error occurred: {e}")
            return None

    def delete_video(self, video_id):
        """Deletes a video from YouTube by its ID."""
        try:
            request = self.youtube_service.videos().delete(id=video_id)
            request.execute()
            print(f"Video with ID {video_id} has been successfully deleted.")
        except googleapiclient.errors.HttpError as e:
            print(f"An error occurred: {e}")

    def get_video_link(self, video_id):
        """Returns the YouTube video link."""
        return f"https://www.youtube.com/watch?v={video_id}"

    def get_playlist_contents(self, playlist_id):
        """Fetches all videos in a specific playlist."""
        try:
            request = self.youtube_service.playlistItems().list(
                part="snippet",
                playlistId=playlist_id
            )
            response = request.execute()
            playlist_items = response.get('items', [])

            if playlist_items:
                for item in playlist_items:
                    print(f"Video Title: {item['snippet']['title']}, Video ID: {item['snippet']['resourceId']['videoId']}")
            else:
                print("No videos found in the playlist.")

            return playlist_items
        except googleapiclient.errors.HttpError as e:
            print(f"An error occurred: {e}")
            return None

# Example usage
# Instantiate the GoogleDrive class and create a folder
# google_drive = GoogleDrive(jsonkey='path/to/your/json/key.json')

# # Create a folder and get its ID
# folder_id = google_drive.create_folder('MyFolder')

# # Upload a file to the newly created folder
# file_link = google_drive.upload_file(filepath='path/to/your/file.txt', folder_id=folder_id)

# print(f"File uploaded successfully! View it here: {file_link}")


# # Example file ID you want to download (replace this with the actual file ID)
# file_id = 'your-file-id-here'

# # Specify the destination folder where the file should be saved
# destination_folder = 'path/to/your/destination/folder'

# # Download the file
# google_drive.download_file(file_id, destination_path=destination_folder)

# youtube----
# # Initialize the YouTubeAPI class
# yt_api = YouTubeAPI(credentials_json='path/to/your/credentials.json')

# # Upload a video to YouTube
# video_id = yt_api.upload_video(
#     file_path='path/to/video.mp4',
#     title='My Video Title',
#     description='A brief description of my video.',
#     tags=['tag1', 'tag2'],
#     category_id=22  # Category ID 22 corresponds to "People & Blogs"
# )

# # Get video details by ID
# if video_id:
#     video_details = yt_api.get_video_details(video_id)
#     if video_details:
#         print(video_details)

# # Delete a video by ID
# yt_api.delete_video(video_id)

# # Get the YouTube link for the video
# video_link = yt_api.get_video_link(video_id)
# print(f"Video Link: {video_link}")

# # Get all videos in a playlist
# playlist_id = 'your_playlist_id_here'
# yt_api.get_playlist_contents(playlist_id)
