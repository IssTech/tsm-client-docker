import sys
from pathlib import Path
from typing import Tuple
from subprocess import call, check_output
from urllib.request import urlopen


TSM_CLIENT_VERSION = "8.1.25.0"

TSM_CLIENT_VERSION_S = "v" + "".join(TSM_CLIENT_VERSION.split(".")[:-1])

IBM_TSM_ROOT_URL = ("https://public.dhe.ibm.com/storage"
                    "/tivoli-storage-management/maintenance/client/v8r1/Linux"
                    "/LinuxX86_DEB/BA")

FALLBACK_CLIENT_URL = (
    f"{IBM_TSM_ROOT_URL}/{TSM_CLIENT_VERSION_S}"
    f"/{TSM_CLIENT_VERSION}-TIV-TSMBAC-LinuxX86_DEB.tar"
)

FALLBACK_CHECKSUM_URL = (
    f"{IBM_TSM_ROOT_URL}/{TSM_CLIENT_VERSION_S}"
    f"/{TSM_CLIENT_VERSION}-TIV-TSMBAC-LinuxX86_DEB.tar.sha256sum.txt"
)


class DownloadError(RuntimeError):
    pass


class InstallationError(RuntimeError):
    pass


def get_latest_urls() -> Tuple[str, str]:
    """
    Get the URLs for the latest version of the TSM client and its checksum.

    If they are not found, we will fall back to the hardcoded values
    FALLBACK_CLIENT_URL and FALLBACK_CHECKSUM_URL.

    :return: A tuple: (client url, checksum for client url)
    """
    return FALLBACK_CLIENT_URL, FALLBACK_CHECKSUM_URL


def download() -> Path:
    """
    Download the TSM client.
    Results in the TSM client *.deb files being available at ./tsm_client.

    :raises DownloadError: If download or extraction fails.
    :returns: Path('./tsm_client')
    """
    print("Downloading TSM client")
    sys.stdout.flush()

    tsm_client_installer_path = Path("tsm_client")

    if (tsm_client_installer_path / "tivsm-ba.amd64.deb").exists():
        return tsm_client_installer_path

    client_url, checksum_url = get_latest_urls()

    try:
        with urlopen(checksum_url) as response:
            checksum_url_content = response.read().decode().strip()
            expected_checksum, client_tar_filename = \
                checksum_url_content.split()
    except ValueError:
        raise DownloadError("Could not download the client checksum.")

    if not Path(client_tar_filename).exists():
        if call(["wget", client_url]) != 0:
            raise DownloadError("Could not download the client.")

    actual_checksum = (check_output(["openssl", "sha256", client_tar_filename])
                       .strip().split(b"= ")[1].decode())
    if actual_checksum != expected_checksum:
        raise DownloadError("Checksum does not match the downloaded file.")

    tsm_client_installer_path.mkdir(parents=True, exist_ok=True)

    if (call(["tar", "-xf", client_tar_filename, "-C",
              str(tsm_client_installer_path)]) != 0):
        tsm_client_installer_path.rmdir()
        raise DownloadError("Could not extract the client.")

    return tsm_client_installer_path


def install(tsm_client_installer_path: Path):
    """
    Install relevant .deb-files from tsm_client_installer_path.
    """
    deb_paths = []

    for deb_file_path in tsm_client_installer_path.glob("*.deb"):
        filename = deb_file_path.name

        if filename.startswith("gskcrypt"):
            deb_paths.append(deb_file_path)
        elif filename.startswith("gskssl"):
            deb_paths.append(deb_file_path)
        elif filename.startswith("tivsm-api64"):
            deb_paths.append(deb_file_path)
        elif filename.startswith("tivsm-ba."):
            deb_paths.append(deb_file_path)

    if len(deb_paths) < 4:
        raise InstallationError("Could not find all necessary .deb files.")

    return_code = 0
    for deb_path in deb_paths:
        return_code |= call(["dpkg", "-i", deb_path])

    if return_code != 0:
        raise InstallationError("Some .deb-files could not be installed.")


def main() -> int:
    try:
        install(download())
    except (DownloadError, InstallationError) as error:
        print(error, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
