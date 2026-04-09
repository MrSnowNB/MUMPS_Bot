#!/usr/bin/env bash
# Fetch a MUMPS routine from WorldVistA/VistA-M
# Usage: bash scripts/fetch_routine.sh <ROUTINE_NAME>

declare -A PKG_MAP
PKG_MAP[ORQQPL1]="Order Entry Results Reporting"
PKG_MAP[MPIF001]="Master Patient Index VistA"
PKG_MAP[DGPTF]="Registration"
PKG_MAP[XUSRB1]="Kernel"
PKG_MAP[LRBLPH]="Lab Service"

ROUTINE="${1:?Usage: fetch_routine.sh <ROUTINE_NAME>}"
PACKAGE="${PKG_MAP[$ROUTINE]:-}"

if [ -z "$PACKAGE" ]; then
    echo "ERROR: No package mapping for $ROUTINE"
    echo "Add it to PKG_MAP in this script, or download manually from:"
    echo "  https://github.com/WorldVistA/VistA-M — search for $ROUTINE.m"
    exit 1
fi

URL="https://raw.githubusercontent.com/WorldVistA/VistA-M/master/Packages/${PACKAGE// /%20}/Routines/${ROUTINE}.m"
DEST="routines/${ROUTINE}.m"

echo "Fetching $ROUTINE from: $URL"
curl -fSL "$URL" -o "$DEST"

if [ $? -eq 0 ] && [ -s "$DEST" ]; then
    LINES=$(wc -l < "$DEST")
    echo "OK: $DEST ($LINES lines)"
else
    echo "FAIL: could not download $ROUTINE.m"
    rm -f "$DEST"
    exit 1
fi
