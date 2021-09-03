import os
import json
import argparse
import logging

parser = argparse.ArgumentParser(__name__)
parser.add_argument("--debug", action="store_true")
parser.add_argument(
    "-r",
    "--root",
    default=os.environ.get("GITHUB_WORKSPACE"),
    help="Root GitHub Directory",
)
parser.add_argument("-w", "--working", default=os.getcwd(), help="Working Directory")
parser.add_argument("-s", "--sarif", help="Sarif file or folder")
parser.add_argument("-o", "--output", help="Output SARIF file or folder")


def processSarifFile(root: str, path: str):
    logging.info(f"Processing SARIF File: {path}")
    if not os.path.exists(path):
        raise Exception("Sarif file does not exist")

    with open(path) as handle:
        sarif = json.load(handle)

    #  Check if the file is a SARIF file
    if not sarif.get("$schema", "").startswith(
        "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema"
    ):
        raise Exception(f"Not a SARIF file: {path}")

    for run in sarif.get("runs", []):
        tool = run.get("tool", {}).get("driver", {})
        logging.info("Processing tool: {name} ({semanticVersion})".format(**tool))

        new_results = []

        for result in run.get("results", []):
            logging.debug(f"Rule({result.get('ruleId')})")

            new_locations = []

            for location in result.get("locations", []):
                #  https://github.com/microsoft/sarif-tutorials/blob/main/docs/2-Basics.md#-linking-results-to-artifacts
                uri = (
                    location.get("physicalLocation", {})
                    .get("artifactLocation", {})
                    .get("uri")
                )

                if uri:
                    new_uri = f"{root}/{uri}"

                    logging.debug(f"Update: {uri} => {new_uri}")

                    location["physicalLocation"]["artifactLocation"]["uri"] = new_uri

                    new_locations.append(location)

            if new_locations:
                result["locations"] = new_locations
                new_results.append(result)

        if new_results:
            run["results"] = new_results

    return sarif


def writeSarif(path: str, data: dict):
    logging.info(f"Writing SARIF File: {path}")
    with open(path, "w") as handle:
        json.dump(data, handle, indent=2)


if __name__ == "__main__":
    arguments = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if arguments.debug else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    if arguments.root and not os.path.exists(arguments.root):
        raise Exception(f"Root path provided does not exist: {arguments.root}")

    root = os.path.abspath(arguments.root)
    working = os.path.abspath(arguments.working)

    logging.info(f"Root Path    :: {root}")
    logging.info(f"Working Path :: {working}")
    logging.info(f"Sarif Path   :: {arguments.sarif}")

    if root == working:
        logging.warning(
            "Root and working paths are the same... Not configured correctly?"
        )
        logging.warning("Please check and see if you need the tool.")
        exit(0)

    difference = os.path.relpath(working, root)
    logging.info(f"Difference in paths :: {difference}")

    if os.path.isdir(arguments.sarif):
        for file in os.listdir(arguments.sarif):
            file_path = os.path.abspath(os.path.join(arguments.sarif, file))
            _, extention = os.path.splitext(file)

            if extention in [".json", ".sarif"]:

                sarif = processSarifFile(
                    difference, os.path.join(arguments.sarif, file)
                )

                if arguments.output and arguments.output != "":
                    output = os.path.join(arguments.output, file)
                else:
                    logging.info("Replacing existing SARIF file")
                    output = file_path

                writeSarif(output, sarif)
    else:
        if arguments.output and arguments.output != "":
            output = os.path.abspath(arguments.output)
        else:
            logging.info("Replacing existing SARIF file")
            output = arguments.sarif

        sarif = processSarifFile(difference, arguments.sarif)

        writeSarif(output, sarif)
