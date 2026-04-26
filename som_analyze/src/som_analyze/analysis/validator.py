from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from ..config import (
    CHAR_LENGTH,
    CHAR_LENGTH_COLUMN_12,
    CHAR_LENGTH_COLUMNS,
    CHAR_PATTERN_REGEX,
    CONTACTED_ALLOWED_VALUES,
    EMAIL_COLUMNS,
    EMAIL_REGEX,
    EXCEL_ERRORS,
    EXCEL_FORMULA_COLUMNS,
    LOCATION_COLUMNS,
    LOCATION_REGEX,
)


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


class ColumnPredicateRule(ValidationRule):
    def __init__(
        self,
        rule_name: str,
        columns: list[str],
        predicate,
        message_template: str,
    ) -> None:
        super().__init__(rule_name)
        self.columns = columns
        self.predicate = predicate
        self.message_template = message_template

    def evaluate(self, dataframe: pd.DataFrame) -> RuleResult:
        fail_matrix = ~dataframe[self.columns].apply(lambda col: col.apply(self.predicate))
        fail_counts = fail_matrix.sum(axis=1).astype(int)

        def _build_message(row: pd.Series) -> str:
            failed_columns = [column for column in self.columns if bool(row[column])]
            if not failed_columns:
                return ""
            return self.message_template.format(columns=", ".join(failed_columns))

        row_messages = fail_matrix.apply(_build_message, axis=1)
        column_fail_counts = {column: int(fail_matrix[column].sum()) for column in self.columns}

        return RuleResult(
            rule_name=self.rule_name,
            fail_counts=fail_counts,
            row_messages=row_messages,
            column_fail_counts=column_fail_counts,
        )


class AllowedValueRule(ValidationRule):
    def __init__(self, rule_name: str, column: str, allowed_values: list[str], message: str) -> None:
        super().__init__(rule_name)
        self.column = column
        self.allowed_values = allowed_values
        self.message = message

    def evaluate(self, dataframe: pd.DataFrame) -> RuleResult:
        fail_series = ~dataframe[self.column].apply(lambda value: is_allowed_value(value, self.allowed_values))
        row_messages = fail_series.apply(lambda failed: self.message if bool(failed) else "")
        return RuleResult(
            rule_name=self.rule_name,
            fail_counts=fail_series.astype(int),
            row_messages=row_messages,
            column_fail_counts={self.column: int(fail_series.sum())},
        )


class StatusInfoConsistencyRule(ValidationRule):
    def __init__(self, rule_name: str) -> None:
        super().__init__(rule_name)

    def evaluate(self, dataframe: pd.DataFrame) -> RuleResult:
        fail_series = (
            dataframe["Status"].astype(str).str.strip().eq("Complete")
            & (
                dataframe["Info completed"].isna()
                | dataframe["Info completed"].astype(str).str.strip().eq("")
                | dataframe["Info completed"].astype(str).str.strip().str.lower().isin(["nan", "none"])
            )
        )
        message = "Consistency check error: Status is Complete but Info completed is missing or empty"
        row_messages = fail_series.apply(lambda failed: message if bool(failed) else "")
        return RuleResult(
            rule_name=self.rule_name,
            fail_counts=fail_series.astype(int),
            row_messages=row_messages,
            column_fail_counts={"Info completed": int(fail_series.sum())},
        )


def is_valid_location(value) -> bool:
    if value is None:
        return False
    if isinstance(value, float):
        return False
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    if len(stripped) < 5:
        return False
    return bool(LOCATION_REGEX.search(stripped))


def is_valid_ref(value) -> bool:
    if not isinstance(value, str):
        return True
    return value.strip().lower() not in EXCEL_ERRORS


def check_column_length(value) -> bool:
    if pd.isna(value) or not isinstance(value, str):
        return False
    return len(value.strip()) == CHAR_LENGTH


def check_column_against_regex(value, regex: str) -> bool:
    if pd.isna(value) or not isinstance(value, str):
        return False
    return re.match(regex, value.strip()) is not None


def is_allowed_value(value, allowed_values: list[str]) -> bool:
    if pd.isna(value) or not isinstance(value, str):
        return False
    return value.strip().lower() in allowed_values


def normalize(dataframe: pd.DataFrame, wanted_columns: list[str]) -> pd.DataFrame:
    normalized = dataframe.copy()
    for column in wanted_columns:
        normalized[column] = normalized[column].astype(str)
        normalized[column] = normalized[column].str.strip()
    return normalized


def build_default_rules() -> list[ValidationRule]:
    return [
        ColumnPredicateRule(
            rule_name="email",
            columns=EMAIL_COLUMNS,
            predicate=lambda value: check_column_against_regex(value, EMAIL_REGEX),
            message_template="Invalid email: {columns}",
        ),
        ColumnPredicateRule(
            rule_name="cofor_pattern",
            columns=CHAR_LENGTH_COLUMNS,
            predicate=lambda value: check_column_against_regex(value, CHAR_PATTERN_REGEX),
            message_template="Invalid COFOR pattern (6 chars + 2 spaces + 2 chars): {columns}",
        ),
        ColumnPredicateRule(
            rule_name="length_12",
            columns=CHAR_LENGTH_COLUMN_12,
            predicate=check_column_length,
            message_template=f"Invalid length (must be {CHAR_LENGTH}): {{columns}}",
        ),
        AllowedValueRule(
            rule_name="contacted",
            column="Contacted",
            allowed_values=CONTACTED_ALLOWED_VALUES,
            message="Invalid Contacted value (allowed: yes, no, out of scope)",
        ),
        ColumnPredicateRule(
            rule_name="location",
            columns=LOCATION_COLUMNS,
            predicate=is_valid_location,
            message_template=(
                "Invalid location (missing postal code, street number, city/country pattern, "
                "or street-type keyword): {columns}"
            ),
        ),
        ColumnPredicateRule(
            rule_name="excel_ref",
            columns=EXCEL_FORMULA_COLUMNS,
            predicate=is_valid_ref,
            message_template="Invalid reference (Excel error token): {columns}",
        ),
        StatusInfoConsistencyRule(rule_name="status_info_missing"),
    ]


