from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

import pandas as pd

from ..config import (
    CHAR_LENGTH,
    CHAR_PATTERN_REGEX,
    EMAIL_REGEX,
    DEFAULT_RULE_DEFINITIONS,
    AllowedValueRuleDefinition,
    ConsistencyRuleDefinition,
    EXCEL_ERRORS,
    LOCATION_REGEX,
    PredicateRuleDefinition,
    ScopeFilterDefinition,
)

EMAIL_ITEM_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EMAIL_SPLIT_REGEX = re.compile(r"(?:[;,:/\r\n]+)|(?:\s{2,})")


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
        predicate: Callable[[object], bool],
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
    if is_empty_value(value):
        return True
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    if len(stripped) < 5:
        return False
    return bool(LOCATION_REGEX.search(stripped))


def is_valid_ref(value) -> bool:
    if pd.isna(value):
        return True
    if not isinstance(value, str):
        return True
    return value.strip().lower() not in EXCEL_ERRORS


def check_column_length(value) -> bool:
    if is_empty_value(value):
        return True
    if not isinstance(value, str):
        return False
    return len(value.strip()) == CHAR_LENGTH


def check_column_against_regex(value, regex: str) -> bool:
    if is_empty_value(value):
        return True
    if not isinstance(value, str):
        return False
    if regex == EMAIL_REGEX:
        return is_valid_email_list(value)
    return re.match(regex, value.strip()) is not None


def is_allowed_value(value, allowed_values: list[str]) -> bool:
    if is_empty_value(value):
        return True
    if not isinstance(value, str):
        return False
    return value.strip().lower() in allowed_values


def is_empty_value(value) -> bool:
    if pd.isna(value):
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def is_valid_email_list(value: str) -> bool:
    # Support multiple emails separated by comma, semicolon, slash, or newline.
    parts = [part.strip() for part in EMAIL_SPLIT_REGEX.split(value) if part.strip()]
    if not parts:
        return True
    found_email = False
    for part in parts:
        if "@" not in part:
            # Allow display names / labels mixed with emails in the same cell.
            continue
        found_email = True
        if EMAIL_ITEM_REGEX.match(part) is None:
            return False
    return found_email


def normalize(dataframe: pd.DataFrame, wanted_columns: list[str]) -> pd.DataFrame:
    normalized = dataframe.copy()
    for column in wanted_columns:
        normalized[column] = normalized[column].astype("string").str.strip()
    return normalized


def build_default_rules() -> list[ValidationRule]:
    predicate_registry: dict[str, Callable[[object], bool]] = {
        "email": lambda value: check_column_against_regex(value, EMAIL_REGEX),
        "cofor_pattern": lambda value: check_column_against_regex(value, CHAR_PATTERN_REGEX),
        "length_12": check_column_length,
        "location": is_valid_location,
        "excel_ref": is_valid_ref,
    }

    rules: list[ValidationRule] = []
    for definition in DEFAULT_RULE_DEFINITIONS:
        if isinstance(definition, PredicateRuleDefinition):
            predicate = predicate_registry[definition.predicate_name]
            rules.append(
                ColumnPredicateRule(
                    rule_name=definition.rule_name,
                    columns=list(definition.columns),
                    predicate=predicate,
                    message_template=definition.message_template,
                )
            )
            continue

        if isinstance(definition, AllowedValueRuleDefinition):
            rules.append(
                AllowedValueRule(
                    rule_name=definition.rule_name,
                    column=definition.column,
                    allowed_values=list(definition.allowed_values),
                    message=definition.message,
                )
            )
            continue

        if isinstance(definition, ConsistencyRuleDefinition):
            rules.append(StatusInfoConsistencyRule(rule_name=definition.rule_name))
            continue

        raise TypeError(f"Unsupported rule definition: {definition!r}")

    return rules


def build_scope_mask(dataframe: pd.DataFrame, filters: tuple[ScopeFilterDefinition, ...]) -> pd.Series:
    mask = pd.Series(True, index=dataframe.index)
    for filter_definition in filters:
        series = dataframe[filter_definition.column]
        if filter_definition.normalize_text:
            series = series.astype("string").str.strip()
        if filter_definition.casefold:
            series = series.str.lower()
            allowed_values = {value.strip().lower() for value in filter_definition.allowed_values}
        else:
            allowed_values = set(filter_definition.allowed_values)
        mask &= series.isin(allowed_values)
    return mask


