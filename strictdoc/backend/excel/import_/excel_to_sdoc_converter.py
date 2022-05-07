import os
from typing import Optional, NamedTuple, List, Tuple

import xlrd

from strictdoc.backend.sdoc.models.document import Document
from strictdoc.backend.sdoc.models.document_config import DocumentConfig
from strictdoc.backend.sdoc.models.document_grammar import (
    DocumentGrammar,
    GrammarElement,
)
from strictdoc.backend.sdoc.models.object_factory import SDocObjectFactory
from strictdoc.backend.sdoc.models.reference import Reference
from strictdoc.backend.sdoc.models.requirement import (
    RequirementField,
    Requirement,
)
from strictdoc.backend.sdoc.models.type_system import GrammarElementFieldString


class RequirementColumns(NamedTuple):
    uid_column: Optional[int]
    title_column: Optional[int]
    statement_column: Optional[int]
    comment_column: Optional[int]
    parent_column: Optional[int]
    extra_header_pairs: List[Tuple[int, str]]


def safe_name(dangerous_name):
    dangerous_name = dangerous_name.splitlines()[0]
    dangerous_name = dangerous_name.strip()
    dangerous_name = dangerous_name.upper()
    dangerous_name = dangerous_name.replace(":", "")
    dangerous_name = dangerous_name.replace("+", "")
    dangerous_name = dangerous_name.replace(",", "_")
    dangerous_name = dangerous_name.replace(" ", "_")
    dangerous_name = dangerous_name.replace("-", "_")
    dangerous_name = dangerous_name.replace("/", "_OR_")
    return dangerous_name


# pylint: disable=too-many-instance-attributes
class ExcelToSDocConverter:
    @staticmethod
    # optional argument title is present for external scripts to assign a title
    def convert(excel_file, title=None) -> Document:
        excel_workbook = xlrd.open_workbook(filename=excel_file, on_demand=True)
        xlrd_sheet: xlrd.sheet.Sheet = excel_workbook.sheet_by_index(0)

        excel_file_name = os.path.basename(excel_file)
        if title is None:
            title = excel_file_name + " sheet " + xlrd_sheet.name

        all_header_columns = list(range(xlrd_sheet.ncols))

        for i in range(16):  # the first 16 rows should do ¯\_(ツ)_/¯
            if xlrd_sheet.row_values(0)[0].strip() != "":
                header_row_idx = i
                break
        else:
            raise NotImplementedError

        header_row = xlrd_sheet.row_values(header_row_idx)
        safe_header_row = list(safe_name(x) for x in header_row)

        statement_column = None
        uid_column = None
        comment_column = None
        title_column = None
        parent_column = None
        for header_column_idx, header_column in enumerate(safe_header_row):
            if header_column in ("REQUIREMENT", "STATEMENT"):
                statement_column = header_column_idx
            elif header_column in (
                "REF",
                "REF #",
                "REF_#",
                "REFDES",
                "ID",
                "UID",
            ):
                uid_column = header_column_idx
            elif header_column in ("REMARKS", "COMMENT"):
                comment_column = header_column_idx
            elif header_column in ("TITLE", "NAME"):
                title_column = header_column_idx
            elif header_column in ("PARENT", "PARENT_REF", "PARENT_UID"):
                parent_column = header_column_idx
            else:
                continue
            all_header_columns.remove(header_column_idx)
        assert statement_column is not None

        # array of tuples: (column_idx: int, column_name: str)
        # [
        #  (0, 'APPLICABLE_COMPONENT_CATEGORIES'),
        #  (2, 'CATEGORY'),
        #  ...
        #  (6, 'CRITICALITY')
        # ]
        extra_header_pairs: List[Tuple[int, str]] = list(
            map(lambda x: (x, safe_header_row[x]), all_header_columns)
        )
        columns = RequirementColumns(
            uid_column=uid_column,
            title_column=title_column,
            statement_column=statement_column,
            comment_column=comment_column,
            parent_column=parent_column,
            extra_header_pairs=extra_header_pairs,
        )

        document = ExcelToSDocConverter.create_document(
            title, extra_header_pairs
        )
        for i in range(header_row_idx + 1, xlrd_sheet.nrows):
            row_values = xlrd_sheet.row_values(i)
            requirement = ExcelToSDocConverter.create_requirement(
                row_values, document, columns
            )
            document.section_contents.append(requirement)

        return document

    @staticmethod
    def create_document(title: Optional[str], extra_header_pairs) -> Document:
        document_config = DocumentConfig(
            parent=None,
            version=None,
            number=None,
            markup=None,
            auto_levels=None,
            requirement_style=None,
        )
        document_title = title if title else "<No title>"
        document = Document(None, document_title, document_config, None, [], [])

        fields = DocumentGrammar.create_default(document).elements[0].fields
        for _, name in extra_header_pairs:
            fields.extend(
                [
                    GrammarElementFieldString(
                        parent=None, title=name, required="False"
                    ),
                ]
            )

        requirements_element = GrammarElement(
            parent=None, tag="REQUIREMENT", fields=fields
        )
        elements = [requirements_element]
        grammar = DocumentGrammar(parent=document, elements=elements)
        document.grammar = grammar
        return document

    @staticmethod
    def create_requirement(
        row_values,
        document,
        columns: RequirementColumns,
    ):
        statement = row_values[columns.statement_column]
        uid = None
        if columns.uid_column is not None:
            uid = row_values[columns.uid_column].strip()
        title = None
        if columns.title_column is not None:
            title = row_values[columns.title_column].strip()
        comments = None
        if columns.comment_column is not None:
            comment = row_values[columns.comment_column].strip()
            if comment in ("", "-"):
                comments = None
            else:
                comments = [comment]
        parent_uid = None
        if columns.parent_column is not None:
            parent_uid = row_values[columns.parent_column].strip()
        template_requirement = SDocObjectFactory.create_requirement(
            document,
            requirement_type="REQUIREMENT",
            title=title,
            uid=uid,
            level=None,
            statement=None,
            statement_multiline=statement,
            rationale=None,
            rationale_multiline=None,
            tags=None,
            comments=comments,
        )
        if parent_uid is not None:
            reference = Reference(template_requirement, "Parent", parent_uid)

            requirement_field = RequirementField(
                parent=template_requirement,
                field_name="REFS",
                field_value=None,
                field_value_multiline=None,
                field_value_references=[reference],
            )
            template_requirement.fields.append(requirement_field)
            template_requirement.ordered_fields_lookup["REFS"] = [
                requirement_field
            ]

        for i, name in columns.extra_header_pairs:
            value = row_values[i].strip()
            if value != "":
                template_requirement.fields.append(
                    RequirementField(
                        parent=None,
                        field_name=name,
                        field_value=None,
                        field_value_multiline=value,
                        field_value_references=None,
                    )
                )

        requirement = Requirement(
            parent=template_requirement.parent,
            requirement_type=template_requirement.requirement_type,
            fields=template_requirement.fields,
        )
        requirement.ng_level = 1

        return requirement