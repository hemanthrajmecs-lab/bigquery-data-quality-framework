# Registry so the runner can look up checks by the name used in rules.yaml.
# Add a new check? Write the module, import it here, add it to the dict. Done.

from checks.null_check import run as null_check
from checks.duplicate_check import run as duplicate_check
from checks.range_check import run as range_check
from checks.schema_check import run as schema_check
from checks.freshness_check import run as freshness_check

REGISTRY = {
    "null_check": null_check,
    "duplicate_check": duplicate_check,
    "range_check": range_check,
    "schema_check": schema_check,
    "freshness_check": freshness_check,
}
