# pylint: disable=R1732

from __future__ import annotations

import io  # pylint: disable=unused-import
import logging
import os
import tarfile
import tempfile

from . import extensions, t


def publishEchidna(
    doc: t.SpecT,
    username: str,
    password: str,
    decision: str,
    additionalDirectories: list[str] | None = None,
    cc: str | None = None,
    editorial: bool = False,
) -> None:
    import requests

    logging.captureWarnings(True)  # Silence SNIMissingWarning
    tarBytes = prepareTar(doc, visibleTar=False, additionalDirectories=additionalDirectories)
    # curl 'https://labs.w3.org/echidna/api/request' --user '<username>:<password>' -F "tar=@/some/path/spec.tar" -F "decision=<decisionUrl>"
    data = {
        "decision": decision,
    }
    if cc:
        data["cc"] = cc
    if editorial:
        data["editorial"] = "true"
    r = requests.post(
        "https://labs.w3.org/echidna/api/request",
        auth=(username, password),
        data=data,
        files={"tar": tarBytes},
    )

    if r.status_code == 202:
        print("Successfully pushed to Echidna!")
        print("Check the URL in a few seconds to see if it was published successfully:")
        print("https://labs.w3.org/echidna/api/status?id=" + r.text)
    else:
        print("There was an error publishing your spec. Here's some information that might help?")
        print(r.status_code)
        print(r.text)
        print(r.headers)


def prepareTar(doc: t.SpecT, visibleTar: bool = False, additionalDirectories: list[str] | None = None) -> bytes:
    if additionalDirectories is None:
        additionalDirectories = ["images", "diagrams", "examples"]
    # Finish the spec
    specOutput = tempfile.NamedTemporaryFile(delete=False)
    doc.finish(outputFilename=specOutput.name)
    # Build the TAR file
    if visibleTar:
        tar = tarfile.open(name="test.tar", mode="w")
    else:
        f = tempfile.NamedTemporaryFile(delete=False)
        tar = tarfile.open(fileobj=f, mode="w")
    tar.add(specOutput.name, arcname="Overview.html")
    # Loaded from .include files
    additionalFiles = extensions.BSPublishAdditionalFiles(additionalDirectories)  # type: ignore # pylint: disable=no-member
    for fname in additionalFiles:
        try:
            if isinstance(fname, str):
                tar.add(fname)
            elif isinstance(fname, list):
                tar.add(fname[0], arcname=fname[1])
        except OSError:
            pass
    tar.close()
    specOutput.close()
    os.remove(specOutput.name)
    if visibleTar:
        file = open("test.tar", "rb")
        tarData = file.read()
        file.close()
        os.remove("test.tar")
    else:
        f.seek(0)
        tarData = f.read()
        f.close()
    return tarData
