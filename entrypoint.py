#!/usr/bin/env python3
import os
import sys
from functools import cache
from subprocess import call
from pathlib import Path
from threading import Event

DSM_OPT_TEMPLATE_PATH = Path("/__issassist/dsm.opt.template")
DSM_SYS_TEMPLATE_PATH = Path("/__issassist/dsm.sys.template")
TSM_CONFIG_PATH = Path("/__issassist/data")
TSM_SERVER_CA_PATH = TSM_CONFIG_PATH / "ca.crt"
DSM_OPT_PATH = TSM_CONFIG_PATH / "dsm.opt"
DSM_WC_OPT_PATH = TSM_CONFIG_PATH / "dsm_wc.opt"
DSM_NO_WC_OPT_PATH = TSM_CONFIG_PATH / "dsm_no_wc.opt"
DSM_SYS_PATH = TSM_CONFIG_PATH / "dsm.sys"


def fill_template(template_path: Path, **values) -> str:
    """
    Return a string based on a template.

    :param template_path: Path to the template file.
    :param values: Values to replace template placeholders with.
    :return: A string based on the template in `template_path`.
    """
    @cache
    def _load_template(path: Path) -> str:
        return path.read_text()
    return _load_template(template_path).format(**values)


def prepare() -> bool:
    """
    Make sure that dsmc is set up and ready to be invoked without a password
    afterward.

    :return: Success?
    """
    tsm_server_name = os.environ.get("TSM_SERVER_NAME")
    tsm_server_host = os.environ.get("TSM_SERVER_HOST")
    tsm_server_port = os.environ.get("TSM_SERVER_PORT")
    use_ipv6 = os.environ.get("USE_IPV6") == "1"
    tsm_node_name = os.environ.get("TSM_NODE_NAME")
    tsm_proxy_name = os.environ.get("TSM_PROXY_NAME")
    tsm_proxy_password = os.environ.get("TSM_PROXY_PASSWORD")
    tls_enabled = os.environ.get("TLS_ENABLED") == "1"
    disable_tls13 = os.environ.get("TLS_FORCE_V12") == "1"

    assert isinstance(tsm_server_name, str)
    assert isinstance(tsm_proxy_name, str)
    assert isinstance(tsm_proxy_password, str)

    # Ensure that /etc/mtab is available.
    call(["ln", "-sf", "/proc/mounts", "/etc/mtab"])

    # Write the CA certificate if TLS is enabled.
    if tls_enabled:
        if TSM_SERVER_CA_PATH.exists():
            call(["/usr/bin/dsmcert", "-add", "-server",
                  tsm_server_name, "-file", TSM_SERVER_CA_PATH])
            print("Certificate imported.")
        else:
            print(
                f"No CA certificate has been provided at path "
                f"'{TSM_SERVER_CA_PATH}'. "
                f"The client will use pre-defined CA certificates."
            )

    # Write dsmc configuration files
    DSM_OPT_PATH.write_text(
        fill_template(
            DSM_OPT_TEMPLATE_PATH,
            tsm_server_name=tsm_server_name,
            wildcards_are_literal="no"
        )
    )
    DSM_WC_OPT_PATH.write_text(
        fill_template(
            DSM_OPT_TEMPLATE_PATH,
            tsm_server_name=tsm_server_name,
            wildcards_are_literal="no"
        )
    )
    DSM_NO_WC_OPT_PATH.write_text(
        fill_template(
            DSM_OPT_TEMPLATE_PATH,
            tsm_server_name=tsm_server_name,
            wildcards_are_literal="yes"
        )
    )

    DSM_SYS_PATH.write_text(
        fill_template(
            DSM_SYS_TEMPLATE_PATH,
            tsm_server_name=tsm_server_name,
            tsm_server_host=tsm_server_host,
            tsm_server_port=tsm_server_port,
            ip_version="V6TCPIP" if use_ipv6 else "TCPIP",
            tsm_node_name=tsm_node_name,
            tsm_proxy_name=tsm_proxy_name,
            tls_enabled="yes" if tls_enabled else "no",
            disable_tls13="TESTFLAG disable_tls13" if disable_tls13 else ""
        )
    )

    # Set the password.
    call(["/opt/tivoli/tsm/client/ba/bin/dsmc", "set", "password",
          tsm_proxy_password, tsm_proxy_password])

    return True


def main():
    # Prepare the container.
    if not prepare():
        return 1

    # This string lets whatever is listening to the container know that it's
    # ready for use.
    sys.stdout.write("ISSASSIST_TSM_CLIENT_CONTAINER_UP\n")
    sys.stdout.flush()

    # Wait indefinitely.
    Event().wait()


if __name__ == "__main__":
    sys.exit(main())
