"""Google Docs API integration for fetching document content."""

import re
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from rich.console import Console

console = Console()

# Scope for read-only access to Google Drive (needed for export)
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class GoogleDocsClient:
    """Client for fetching Google Docs content."""

    def __init__(
        self,
        credentials_path: Path = None,
        token_path: Path = None,
    ):
        """Initialize Google Docs client.

        Args:
            credentials_path: Path to OAuth client credentials JSON file
            token_path: Path to store/load user token
        """
        self.credentials_path = credentials_path or Path("google_credentials.json")
        self.token_path = token_path or Path("google_token.json")
        self._service = None

    def _get_credentials(self) -> Credentials:
        """Get or refresh OAuth credentials.

        Returns:
            Valid credentials for Google API access
        """
        creds = None

        # Load existing token if available
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                console.print("[dim]Refreshing expired credentials...[/dim]")
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"OAuth credentials file not found: {self.credentials_path}\n"
                        "Download from Google Cloud Console > APIs & Services > Credentials"
                    )

                console.print("[yellow]Opening browser for Google authentication...[/yellow]")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save the credentials for next run
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())
            console.print(f"[green]Credentials saved to {self.token_path}[/green]")

        return creds

    @property
    def service(self):
        """Get or create the Google Drive service."""
        if self._service is None:
            creds = self._get_credentials()
            self._service = build("drive", "v3", credentials=creds)
        return self._service

    @staticmethod
    def extract_document_id(url_or_id: str) -> str:
        """Extract document ID from a Google Docs URL or return the ID directly.

        Args:
            url_or_id: Google Docs URL or document ID

        Returns:
            Document ID

        Examples:
            >>> GoogleDocsClient.extract_document_id("https://docs.google.com/document/d/1abc123/edit")
            '1abc123'
            >>> GoogleDocsClient.extract_document_id("1abc123")
            '1abc123'
        """
        # Pattern for Google Docs URLs
        patterns = [
            r"docs\.google\.com/document/d/([a-zA-Z0-9_-]+)",  # Standard URL
            r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)",  # Drive file URL
            r"^([a-zA-Z0-9_-]{20,})$",  # Direct ID (20+ chars)
        ]

        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)

        raise ValueError(
            f"Could not extract document ID from: {url_or_id}\n"
            "Expected a Google Docs URL or document ID"
        )

    def get_document_text(self, url_or_id: str) -> str:
        """Fetch plain text content from a Google Doc.

        Args:
            url_or_id: Google Docs URL or document ID

        Returns:
            Plain text content of the document
        """
        doc_id = self.extract_document_id(url_or_id)

        console.print(f"[dim]Fetching document: {doc_id}[/dim]")

        # Export the document as plain text
        request = self.service.files().export(fileId=doc_id, mimeType="text/plain")
        content = request.execute()

        # Content is returned as bytes
        if isinstance(content, bytes):
            content = content.decode("utf-8")

        return content

    def get_document_title(self, url_or_id: str) -> str:
        """Get the title of a Google Doc.

        Args:
            url_or_id: Google Docs URL or document ID

        Returns:
            Document title
        """
        doc_id = self.extract_document_id(url_or_id)

        # Get file metadata
        file = self.service.files().get(fileId=doc_id, fields="name").execute()
        return file.get("name", "Untitled")

    def check_credentials(self) -> bool:
        """Check if valid credentials exist.

        Returns:
            True if valid credentials exist, False otherwise
        """
        if not self.token_path.exists():
            return False

        try:
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
            return creds and creds.valid
        except Exception:
            return False
