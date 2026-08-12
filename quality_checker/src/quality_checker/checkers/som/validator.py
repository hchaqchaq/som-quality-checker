from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import pandas as pd

from .config import EMAIL_REGEX, ScopeFilterDefinition

EMAIL_ITEM_REGEX = re.compile(EMAIL_REGEX)
NOTE_DATE_REGEX = re.compile(r"(?<!\d)(\d{2}/\d{2}/\d{4})(?!\d)")
NOTE_DATE_TOKEN_REGEX = re.compile(r"(?<!\d)(\d{1,4}[./-]\d{1,2}[./-]\d{1,4})(?!\d)")
COMPLETED_VALUES = frozenset({"complete", "completed"})


@dataclass(slots=True)
class RuleResult:
    rule_name: str
    fail_counts: pd.Series
    row_messages: pd.Series
    column_fail_counts: dict[str, int]


class ValidationRule(ABC):
    def __init__(self, rule_name: str) -> None:
        self.rule_name = rule_name

    @abstractmethod
    def evaluate(self, dataframe: pd.DataFrame) -> RuleResult:
        raise NotImplementedError


class StatusCompletedRule(ValidationRule):
    def evaluate(self, dataframe: pd.DataFrame) -> RuleResult:
        fail_series = dataframe["Status"].apply(is_completed) & ~dataframe["Info completed"].apply(is_completed)
        message = "INFO COMPLETED MUST BE COMPLETED"
        return _build_result(self.rule_name, fail_series, message, "Info completed")


class CompletionDateRule(ValidationRule):
    def evaluate(self, dataframe: pd.DataFrame) -> RuleResult:
        condition = (
            dataframe["Status"].apply(is_completed)
            & dataframe["Info completed"].apply(is_completed)
            & dataframe["Contacted"].apply(is_yes)
        )
        messages = pd.Series("", index=dataframe.index, dtype="string")
        for index in dataframe.index[condition]:
            value = dataframe.at[index, "Completion date"]
            if is_empty_value(value):
                messages.at[index] = "COMPLETION DATE IS MISSING"
            elif parse_completion_date(value) is None:
                messages.at[index] = "COMPLETION DATE IS INVALID"
        fail_series = messages.ne("")
        return _build_result(self.rule_name, fail_series, messages, "Completion date")


class RelanceRule(ValidationRule):
    def __init__(self, rule_name: str, reference_date: date) -> None:
        super().__init__(rule_name)
        self.reference_date = reference_date

    def evaluate(self, dataframe: pd.DataFrame) -> RuleResult:
        condition = dataframe["Info completed"].apply(is_empty_value) & dataframe["Contacted"].apply(is_yes)
        messages = pd.Series("", index=dataframe.index, dtype="string")
        oldest_allowed = self.reference_date - timedelta(days=3)
        for index in dataframe.index[condition]:
            dates = extract_note_dates(dataframe.at[index, "NOTE"])
            if not dates:
                messages.at[index] = "RELANCE DATE IS MISSING OR INVALID"
                continue
            latest_date = max(dates)
            if latest_date > self.reference_date:
                messages.at[index] = "RELANCE DATE IS IN THE FUTURE"
            elif latest_date < oldest_allowed:
                messages.at[index] = "RELANCE DATE IS OLDER THAN 3 DAYS"
        fail_series = messages.ne("")
        return _build_result(self.rule_name, fail_series, messages, "NOTE")


class CoforAddressRule(ValidationRule):
    def __init__(
        self,
        rule_name: str,
        cofor_column: str,
        address_column: str,
        label: str,
    ) -> None:
        super().__init__(rule_name)
        self.cofor_column = cofor_column
        self.address_column = address_column
        self.label = label

    def evaluate(self, dataframe: pd.DataFrame) -> RuleResult:
        normalized_cofors = dataframe[self.cofor_column].apply(normalize_key)
        normalized_addresses = dataframe[self.address_column].apply(normalize_key)
        participating = normalized_cofors.ne("") & normalized_addresses.ne("")
        grouped = pd.DataFrame(
            {"cofor": normalized_cofors[participating], "address": normalized_addresses[participating]}
        )
        conflicting_cofors = set(
            grouped.groupby("cofor")["address"].nunique().loc[lambda values: values > 1].index
        )
        fail_series = participating & normalized_cofors.isin(conflicting_cofors)
        messages = pd.Series("", index=dataframe.index, dtype="string")
        for index in dataframe.index[fail_series]:
            cofor = normalized_text(dataframe.at[index, self.cofor_column])
            messages.at[index] = f"{self.label} COFOR {cofor} HAS MULTIPLE ADDRESSES"
        return _build_result(self.rule_name, fail_series, messages, self.address_column)


class CoforFormatRule(ValidationRule):
    def evaluate(self, dataframe: pd.DataFrame) -> RuleResult:
        condition = dataframe["Contacted"].apply(is_yes) & dataframe["Info completed"].apply(is_completed)
        fail_series = condition & dataframe["Format check"].apply(normalized_text).str.casefold().eq("nok")
        return _build_result(
            self.rule_name,
            fail_series,
            "COFOR PATTERN (6 CHARS + 2 SPACES + 2 CHARS)",
            "Format check",
        )


class RequiredEmailRule(ValidationRule):
    def __init__(self, rule_name: str, column: str) -> None:
        super().__init__(rule_name)
        self.column = column

    def evaluate(self, dataframe: pd.DataFrame) -> RuleResult:
        fail_series = ~dataframe[self.column].apply(is_valid_single_email)
        message = f"INVALID OR MISSING EMAIL: {self.column}"
        return _build_result(self.rule_name, fail_series, message, self.column)


class ContactedWhenStatusFilledRule(ValidationRule):
    def evaluate(self, dataframe: pd.DataFrame) -> RuleResult:
        status_filled = ~dataframe["Status"].apply(is_empty_value)
        fail_series = status_filled & ~dataframe["Contacted"].apply(is_yes)
        return _build_result(
            self.rule_name,
            fail_series,
            "CONTACTED MUST BE YES WHEN STATUS IS FILLED",
            "Contacted",
        )


class NoteDateFormatRule(ValidationRule):
    def evaluate(self, dataframe: pd.DataFrame) -> RuleResult:
        fail_series = ~dataframe["NOTE"].apply(has_valid_note_dates)
        return _build_result(
            self.rule_name,
            fail_series,
            "NOTE DATE MUST USE DD/MM/YYYY",
            "NOTE",
        )


def _build_result(
    rule_name: str,
    fail_series: pd.Series,
    messages: str | pd.Series,
    column: str,
) -> RuleResult:
    failures = fail_series.astype(int)
    if isinstance(messages, str):
        row_messages = fail_series.apply(lambda failed: messages if bool(failed) else "").astype("string")
    else:
        row_messages = messages.astype("string")
    return RuleResult(
        rule_name=rule_name,
        fail_counts=failures,
        row_messages=row_messages,
        column_fail_counts={column: int(failures.sum())},
    )


def is_empty_value(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    try:
        missing = pd.isna(value)
    except (TypeError, ValueError):
        return False
    return bool(missing) if isinstance(missing, bool) else False


def normalized_text(value: object) -> str:
    return "" if is_empty_value(value) else str(value).strip()


def normalize_key(value: object) -> str:
    return " ".join(normalized_text(value).split()).casefold()


def is_completed(value: object) -> bool:
    return normalized_text(value).casefold() in COMPLETED_VALUES


def is_yes(value: object) -> bool:
    return normalized_text(value).casefold() == "yes"


def parse_completion_date(value: object) -> date | None:
    if isinstance(value, pd.Timestamp):
        return None if pd.isna(value) else value.date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = normalized_text(value)
    if not text:
        return None
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        return None


def extract_note_dates(value: object) -> list[date]:
    text = normalized_text(value)
    parsed_dates: list[date] = []
    for match in NOTE_DATE_REGEX.finditer(text):
        try:
            parsed_dates.append(datetime.strptime(match.group(1), "%d/%m/%Y").date())
        except ValueError:
            continue
    return parsed_dates


def has_valid_note_dates(value: object) -> bool:
    tokens = NOTE_DATE_TOKEN_REGEX.findall(normalized_text(value))
    if not tokens:
        return False

    for token in tokens:
        if NOTE_DATE_REGEX.fullmatch(token) is None:
            return False
        try:
            datetime.strptime(token, "%d/%m/%Y")
        except ValueError:
            return False
    return True


def is_valid_single_email(value: object) -> bool:
    text = normalized_text(value)
    return bool(text) and EMAIL_ITEM_REGEX.fullmatch(text) is not None


def normalize(dataframe: pd.DataFrame, text_columns: list[str]) -> pd.DataFrame:
    normalized = dataframe.copy()
    for column in text_columns:
        normalized[column] = normalized[column].astype("string").str.strip()
    return normalized


def build_default_rules(reference_date: date | None = None) -> list[ValidationRule]:
    as_of = date.today() if reference_date is None else reference_date
    return [
        StatusCompletedRule("status_completed"),
        CompletionDateRule("completion_date"),
        RelanceRule("relance", as_of),
        CoforAddressRule(
            "shipper_cofor_address",
            "Shipper COFOR2",
            "Shipper COFOR Address",
            "SHIPPER",
        ),
        CoforAddressRule(
            "manufacturer_cofor_address",
            "Manufacturer COFOR",
            "Manufacturer address",
            "MANUFACTURER",
        ),
        CoforFormatRule("cofor_format"),
        RequiredEmailRule("quality_contact_email", "Quality contact"),
        RequiredEmailRule("logistic_contact_email", "Logistic contact"),
        ContactedWhenStatusFilledRule("contacted_when_status_filled"),
        NoteDateFormatRule("note_date_format"),
    ]


def build_scope_mask(dataframe: pd.DataFrame, filters: tuple[ScopeFilterDefinition, ...]) -> pd.Series:
    mask = pd.Series(True, index=dataframe.index)
    for filter_definition in filters:
        series = dataframe[filter_definition.column]
        if filter_definition.normalize_text:
            series = series.astype("string").str.strip()
        if filter_definition.casefold:
            series = series.str.casefold()
            allowed_values = {value.strip().casefold() for value in filter_definition.allowed_values}
        else:
            allowed_values = set(filter_definition.allowed_values)
        mask &= series.isin(allowed_values)
    return mask
