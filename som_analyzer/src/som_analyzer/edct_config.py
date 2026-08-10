from __future__ import annotations

EDCT_PROJECT = "eDCT"
EDCT_REQUIRED_SHEETS = ("Supplier Level", "Open Task", "Template-Cofor-Creation")
EDCT_HEADER_ROW = 2
EDCT_INDEX_COLUMN = "Index"
EDCT_COFOR_TEMPLATE_SHEET = "Template-Cofor-Creation"
EDCT_COFOR_TEMPLATE_PUNCH_COLUMN = 4
EDCT_COFOR_TEMPLATE_PUNCH_HEADER = "Punch Code"
EDCT_COFOR_TEMPLATE_FIRST_DATA_ROW = 3
EDCT_COFOR_REQUEST_DATE_COLUMN = "Creation of Cofors request date"

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
    EDCT_COFOR_REQUEST_DATE_COLUMN,
    "DDE Validated date /sent to edi team",
)

EDCT_DATED_COMMENT_COLUMNS = ("Comments", "Kick-off comments", "Readiness Comments", "EDI Comments")

EDCT_PORTAL_COLUMNS = ("eSupplierConnect", "B2B", "New supplier portal", "SPM", "iTMS")
EDCT_TRIPLE_STATUS_VALUES = ("Valid", "No Valid")
EDCT_YES_NO_VALUES = ("YES", "NO")
EDCT_PORTAL_VALUES = ("YES", "NOT")
EDCT_EDI_MODE_VALUES = ("WEB EDI", "Standard EDI")
EDCT_PHONE_DIGITS = (7, 20)

EDCT_RULE_CATALOGUE_ROWS = (
    "| `Sales contact`, `Logistic contact` | `Effective kick-off date` is populated | Yes | Plain emails separated by `;`; trailing semicolons are ignored |",
    "| `Plant Manager`, `Logistic Manager contact`, `Key Account Contact`, `Logistic specialist Contact`, `Transport manager`, `Packaging Specialist`, `EDI Contact`, `Participants` | When populated | Yes | Plain emails separated by `;`; trailing semicolons are ignored |",
    "| `Seller COFOR`, `Manufacturer COFOR`, `Shipper COFOR`, `Empty Cofor` | `Effective kick-off date` is populated | Yes | Six alphanumeric characters, two spaces, two alphanumeric characters |",
    "| `Phone`, `Phone2`, `Phone3`, `Phone4`, `Phone5`, `Phone6`, `Phone7` | When populated | Yes | 7-20 digits after removing spaces, `+`, parentheses, dots, and hyphens |",
    "| `First communication sent`, `Planned Kick-off meeting`, `Kick-off Invitation sent`, `Kick-off meeting postponed date`, `Cofor created date`, `DDE Validated date /sent to edi team` | When populated | Yes | Native Excel date or `DD.MM.YYYY` |",
    f"| `{EDCT_COFOR_REQUEST_DATE_COLUMN}` | Required when `Supplier Punch code` exists in `Template-Cofor-Creation`; otherwise when populated | Conditional | Native Excel date or `DD.MM.YYYY` |",
    "| `Effective kick-off date` | When populated | Yes | Native Excel date or `DD.MM.YYYY`; today or earlier |",
    "| `Comments`, `Kick-off comments` | When populated | Yes | `DD.MM.YYYY: comment` or `DD/MM/YYYY: comment` |",
    "| `Readiness Comments`, `EDI Comments` | When populated | Yes | `DD.MM.YYYY: comment` |",
    "| `Triple Status` | `Cofor created date` is populated | No | `Valid` or `No Valid` |",
    "| `Overseas` | Always | Yes | `YES` or `NO` |",
    "| `Shipping location` | `Overseas = YES` | No | `YES` or `NO` |",
    "| `Supplier Confimation` | Always | Yes | `YES` |",
    "| `eSupplierConnect`, `B2B`, `New supplier portal`, `SPM`, `iTMS` | Required after `Effective kick-off date`; optional before | Conditional | `YES` or `NOT` |",
    "| `EDI Mode` | Required after `Cofor created date`; optional before | Conditional | `WEB EDI` or `Standard EDI` |",
    "| `OPEN TASK` | Cross-checked for every assessed row | Conditional | `YES` when the punch code exists in `Open Task`; empty otherwise |",
)

EDCT_UNCHECKED_COLUMNS = (
    "Alten owner",
    "Priority",
    "Seller Name",
    "Seller address",
    "Manufacturer Name",
    "Manufacturer company address",
    "Shipper Cofor Name",
    "Shipper address",
    "Seller/Manuf already in EQP",
    "Seller/Shipper already in EQP",
    "EDI already known",
    "Plants",
    "Incoterm",
    "Planned Kick-off week",
    "ABP Training",
    "EDI EQP No",
    "EDI Scenario",
    "Date of Start of EDI validation / migration",
    "UNB DELFOR",
    "Qualifier UNB DELFOR",
    "UNB DELJIT",
    "Qualifier UNB DELJIT",
    "UNB DESADV",
    "Qualifier UNB DESADV",
    "Hybrid Cofor",
    "EQP Status",
    "CZ STATUS DELJIT",
    "CZ progress (Avancement CZ) EQP step",
    "CZ current step (Etape courante CZ)",
    "Status CZ Date of DELJIT/DESADV",
    "MF STATUS DELFOR",
    "MF progress (Avancement MF) EQP step",
    "MF current step (Etape courante MF)",
    "Status MF Date of DELFOR",
    "Status EDI Certified",
    "SET UP IN CORAIL",
)

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
