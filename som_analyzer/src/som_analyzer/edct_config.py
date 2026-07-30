from __future__ import annotations

EDCT_PROJECT = "eDCT"
EDCT_REQUIRED_SHEETS = ("Supplier Level", "Open Task")
EDCT_HEADER_ROW = 2
EDCT_INDEX_COLUMN = "Index"

EDCT_FORMULA_COLUMNS = (
    "Onboarding Status",
    "Starting date",
    "Triplet COFOR",
    "Seller_Manuf",
    "Seller_Shipper",
    "Kick-off meeting postponed week",
    "Effective kick-off week",
    "Kick-off status",
    "Readiness status",
)

EDCT_EMAIL_COLUMNS = (
    "Sales contact",
    "Logistic contact",
    "Plant Manager",
    "Logistic Manager contact",
    "Key Account Contact",
    "Logistic specialist Contact",
    "Transport manager",
    "Packaging Specialist",
    "EDI Contact",
    "Participants",
)

EDCT_COFOR_COLUMNS = (
    "Seller COFOR",
    "Manufacturer COFOR",
    "Shipper COFOR",
    "Empty Cofor",
)

EDCT_PHONE_COLUMNS = ("Phone", "Phone2", "Phone3", "Phone4", "Phone5", "Phone6", "Phone7")

EDCT_DATE_COLUMNS = (
    "First communication sent",
    "Planned Kick-off meeting",
    "Kick-off Invitation sent",
    "Kick-off meeting postponed date",
    "Effective kick-off date",
    "Cofor created date",
    "DDE Validated date /sent to edi team",
)

EDCT_DATED_COMMENT_COLUMNS = ("Comments", "Kick-off comments", "Readiness Comments", "EDI Comments")

EDCT_PORTAL_COLUMNS = ("eSupplierConnect", "B2B", "New supplier portal", "SPM", "iTMS")

EDCT_REQUIRED_COLUMNS = tuple(
    dict.fromkeys(
        (
            EDCT_INDEX_COLUMN,
            "Triple Status",
            "Supplier Punch code",
            "Supplier name",
            *EDCT_FORMULA_COLUMNS,
            *EDCT_EMAIL_COLUMNS,
            *EDCT_COFOR_COLUMNS,
            *EDCT_PHONE_COLUMNS,
            *EDCT_DATE_COLUMNS,
            *EDCT_DATED_COMMENT_COLUMNS,
            *EDCT_PORTAL_COLUMNS,
            "Shipping location",
            "Overseas",
            "Supplier Confimation",
            "OPEN TASK",
            "EDI Mode",
        )
    )
)
