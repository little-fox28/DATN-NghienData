import logging
import zipfile
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from kaggle.api.kaggle_api_extended import KaggleApi
from shared.utils.logger import get_logger

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = get_logger(__name__)


class KaggleDataFetcher:
    """
    Handles data extraction from Kaggle datasets using the Kaggle API.
    """

    def __init__(self, destination_dir: str = "data/raw") -> None:
        """
        Initialize the fetcher with a destination directory.

        Args:
            destination_dir (str): Directory where downloaded files will be stored.
        """
        self.destination_dir = Path(destination_dir)
        self.destination_dir.mkdir(parents=True, exist_ok=True)
        self._api: Optional[KaggleApi] = None

    @property
    def api(self) -> KaggleApi:
        """
        Lazy-loaded and authenticated Kaggle API instance.
        """
        if self._api is None:
            logger.debug("Initializing and authenticating Kaggle API...")
            self._api = KaggleApi()
            self._api.authenticate()
        return self._api

    def fetch(self, dataset_name: str, file_name: Optional[str] = None) -> Optional[Path]:
        """
        Download file(s) from a Kaggle dataset.

        Args:
            dataset_name (str): Kaggle dataset identifier (e.g., 'owner/dataset').
            file_name (Optional[str]): Specific file to download. If None, downloads the entire dataset.

        Returns:
            Optional[Path]: Path to the downloaded file or directory, or None if failed.
        """
        try:
            logger.info(f"Destination directory set to: {self.destination_dir.resolve()}")
            
            if file_name:
                return self._download_single_file(dataset_name, file_name)
            else:
                return self._download_entire_dataset(dataset_name)

        except Exception as e:
            logger.error(f"Error during Kaggle fetch for '{dataset_name}': {e}", exc_info=True)
            return None

    def _download_single_file(self, dataset_name: str, file_name: str) -> Optional[Path]:
        """
        Downloads a specific file from the dataset.
        """
        target_file = self.destination_dir / file_name
        target_zip = self.destination_dir / f"{file_name}.zip"

        if target_file.exists():
            logger.info(f"File already exists, skipping download: {target_file}")
            return target_file

        logger.info(f"Downloading single file '{file_name}' from '{dataset_name}'...")
        self.api.dataset_download_file(dataset_name, file_name, path=str(self.destination_dir))
        
        if target_zip.exists():
            logger.info(f"Extracting {target_zip.name}...")
            self._extract_zip(target_zip)
        
        if target_file.exists():
            logger.info(f"File available at: {target_file}")
            return target_file
        else:
            logger.error(f"Target file {file_name} not found after download attempt.")
            return None

    def _download_entire_dataset(self, dataset_name: str) -> Path:
        """
        Downloads and unzips the entire dataset.
        """
        logger.info(f"Downloading entire dataset '{dataset_name}'...")
        self.api.dataset_download_files(dataset_name, path=str(self.destination_dir), unzip=True)
        logger.info(f"Dataset downloaded and extracted to {self.destination_dir}")
        return self.destination_dir

    def _extract_zip(self, zip_path: Path) -> None:
        """
        Extracts a zip file and removes the archive.
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(path=str(self.destination_dir))
            logger.info(f"Successfully extracted {zip_path.name}")
            zip_path.unlink()
            logger.debug(f"Deleted archive {zip_path.name}")
        except zipfile.BadZipFile as e:
            logger.error(f"Failed to extract zip file {zip_path}: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while extracting {zip_path}: {e}")


def download_kaggle_file(
    dataset_name: str,
    file_name: Optional[str] = None,
    destination_dir: str = "data/raw"
) -> Optional[Path]:
    """
    Backward-compatible wrapper function for the KaggleDataFetcher class.
    """
    fetcher = KaggleDataFetcher(destination_dir=destination_dir)
    return fetcher.fetch(dataset_name=dataset_name, file_name=file_name)
